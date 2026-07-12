"""Fire Score 数据回流校准系统

根据用户实际发布数据自动校准 Fire Score 五维权重：
hook（钩子）、trust（信任）、retention（留存）、conversion（转化）、emotion（情绪）

核心算法：
1. 收集用户在某平台的历史数据：每次的 Fire Score 各维度分 + 实际互动率
2. 计算每个维度的「预测贡献度」：该维度分数与实际互动率的皮尔逊相关系数
3. 按贡献度重新分配权重（总和保持 100%）
4. 用滑动窗口（最近 50 条）避免早期数据过度影响
"""

import math
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_WEIGHTS: dict[str, float] = {
    "hook": 25.0,
    "trust": 20.0,
    "retention": 25.0,
    "conversion": 15.0,
    "emotion": 15.0,
}

DIMENSIONS = list(DEFAULT_WEIGHTS.keys())
WINDOW_SIZE = 50
MIN_SAMPLES = 5
DB_PATH = Path(__file__).resolve().parent.parent / "output" / "tracker.db"


def _ensure_db(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS performance_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id      TEXT    NOT NULL,
            user_id         TEXT    NOT NULL,
            platform        TEXT    NOT NULL,
            fire_score      REAL,
            hook_score      REAL,
            trust_score     REAL,
            retention_score REAL,
            conversion_score REAL,
            emotion_score   REAL,
            views           INTEGER DEFAULT 0,
            likes           INTEGER DEFAULT 0,
            comments        INTEGER DEFAULT 0,
            shares          INTEGER DEFAULT 0,
            favorites       INTEGER DEFAULT 0,
            engagement_rate REAL,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS weight_configs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         TEXT    NOT NULL,
            platform        TEXT    NOT NULL,
            hook_weight     REAL    DEFAULT 25,
            trust_weight    REAL    DEFAULT 20,
            retention_weight REAL   DEFAULT 25,
            conversion_weight REAL  DEFAULT 15,
            emotion_weight  REAL    DEFAULT 15,
            sample_count    INTEGER DEFAULT 0,
            calibrated_at   TEXT,
            created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(user_id, platform)
        );

        CREATE INDEX IF NOT EXISTS idx_perf_user_platform
            ON performance_records(user_id, platform);
        CREATE INDEX IF NOT EXISTS idx_perf_content
            ON performance_records(content_id);
        """
    )
    conn.commit()
    return conn


class FireScoreCalibrator:
    """根据用户实际发布数据自动校准 Fire Score 权重"""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = _ensure_db(self.db_path)
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def record_performance(
        self,
        content_id: str,
        user_id: str,
        platform: str,
        fire_score: float | None,
        dimension_scores: dict[str, float] | None,
        actual_metrics: dict[str, int],
    ) -> dict[str, Any]:
        """记录一次实际表现，用于后续校准

        Args:
            content_id: 内容 ID
            user_id: 用户 ID
            platform: 平台名称
            fire_score: Fire Score 总分
            dimension_scores: 各维度分 {"hook": 80, "trust": 70, ...}
            actual_metrics: 实际数据 {"views": 1000, "likes": 50, ...}
        """
        views = actual_metrics.get("views", 0)
        likes = actual_metrics.get("likes", 0)
        comments = actual_metrics.get("comments", 0)
        shares = actual_metrics.get("shares", 0)
        favorites = actual_metrics.get("favorites", 0)

        engagement_rate = (
            (likes + comments + shares + favorites) / views if views > 0 else 0.0
        )

        ds = dimension_scores or {}
        self.conn.execute(
            """INSERT OR REPLACE INTO performance_records
               (content_id, user_id, platform, fire_score,
                hook_score, trust_score, retention_score, conversion_score, emotion_score,
                views, likes, comments, shares, favorites, engagement_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                content_id,
                user_id,
                platform,
                fire_score,
                ds.get("hook"),
                ds.get("trust"),
                ds.get("retention"),
                ds.get("conversion"),
                ds.get("emotion"),
                views,
                likes,
                comments,
                shares,
                favorites,
                round(engagement_rate, 6),
            ),
        )
        self.conn.commit()

        return {
            "content_id": content_id,
            "engagement_rate": round(engagement_rate, 4),
            "recorded": True,
        }

    def calibrate(self, user_id: str, platform: str) -> dict[str, Any]:
        """基于历史数据重新校准权重

        Returns:
            校准结果，包含新权重和校准统计
        """
        rows = self.conn.execute(
            """SELECT hook_score, trust_score, retention_score,
                      conversion_score, emotion_score, engagement_rate
               FROM performance_records
               WHERE user_id = ? AND platform = ?
                 AND hook_score IS NOT NULL
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, platform, WINDOW_SIZE),
        ).fetchall()

        if len(rows) < MIN_SAMPLES:
            default = self._upsert_weights(user_id, platform, DEFAULT_WEIGHTS, len(rows))
            return {
                "status": "insufficient_data",
                "message": f"至少需要 {MIN_SAMPLES} 条数据才能校准，当前 {len(rows)} 条",
                "weights": default,
                "sample_count": len(rows),
            }

        dim_values: dict[str, list[float]] = {d: [] for d in DIMENSIONS}
        engagement_values: list[float] = []

        for row in rows:
            dim_values["hook"].append(row["hook_score"])
            dim_values["trust"].append(row["trust_score"])
            dim_values["retention"].append(row["retention_score"])
            dim_values["conversion"].append(row["conversion_score"])
            dim_values["emotion"].append(row["emotion_score"])
            engagement_values.append(row["engagement_rate"])

        correlations: dict[str, float] = {}
        for dim in DIMENSIONS:
            correlations[dim] = abs(_pearson(dim_values[dim], engagement_values))

        total_corr = sum(correlations.values())
        if total_corr < 1e-9:
            new_weights = DEFAULT_WEIGHTS.copy()
        else:
            new_weights = {
                dim: round((correlations[dim] / total_corr) * 100, 1)
                for dim in DIMENSIONS
            }

        saved = self._upsert_weights(user_id, platform, new_weights, len(rows))

        return {
            "status": "calibrated",
            "weights": saved,
            "correlations": {d: round(v, 4) for d, v in correlations.items()},
            "sample_count": len(rows),
            "calibrated_at": datetime.now().isoformat(),
        }

    def get_calibrated_weights(self, user_id: str, platform: str) -> dict[str, float]:
        """获取校准后的权重"""
        row = self.conn.execute(
            """SELECT hook_weight, trust_weight, retention_weight,
                      conversion_weight, emotion_weight
               FROM weight_configs
               WHERE user_id = ? AND platform = ?""",
            (user_id, platform),
        ).fetchone()

        if row is None:
            return DEFAULT_WEIGHTS.copy()

        return {
            "hook": row["hook_weight"],
            "trust": row["trust_weight"],
            "retention": row["retention_weight"],
            "conversion": row["conversion_weight"],
            "emotion": row["emotion_weight"],
        }

    def predict_engagement(
        self, user_id: str, platform: str, dimension_scores: dict[str, float]
    ) -> float:
        """基于校准权重预测互动率"""
        weights = self.get_calibrated_weights(user_id, platform)
        weighted_sum = sum(
            dimension_scores.get(d, 0) * weights.get(d, 0) for d in DIMENSIONS
        )
        return round(weighted_sum / 100, 4)

    def get_history(
        self, user_id: str, platform: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """获取历史校准数据"""
        rows = self.conn.execute(
            """SELECT content_id, fire_score,
                      hook_score, trust_score, retention_score, conversion_score, emotion_score,
                      views, likes, comments, shares, favorites,
                      engagement_rate, created_at
               FROM performance_records
               WHERE user_id = ? AND platform = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, platform, limit),
        ).fetchall()

        return [dict(r) for r in rows]

    def _upsert_weights(
        self,
        user_id: str,
        platform: str,
        weights: dict[str, float],
        sample_count: int,
    ) -> dict[str, float]:
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO weight_configs
                  (user_id, platform, hook_weight, trust_weight, retention_weight,
                   conversion_weight, emotion_weight, sample_count, calibrated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, platform) DO UPDATE SET
                  hook_weight     = excluded.hook_weight,
                  trust_weight    = excluded.trust_weight,
                  retention_weight = excluded.retention_weight,
                  conversion_weight = excluded.conversion_weight,
                  emotion_weight  = excluded.emotion_weight,
                  sample_count    = excluded.sample_count,
                  calibrated_at   = excluded.calibrated_at""",
            (
                user_id,
                platform,
                weights["hook"],
                weights["trust"],
                weights["retention"],
                weights["conversion"],
                weights["emotion"],
                sample_count,
                now,
            ),
        )
        self.conn.commit()
        return {
            "hook": weights["hook"],
            "trust": weights["trust"],
            "retention": weights["retention"],
            "conversion": weights["conversion"],
            "emotion": weights["emotion"],
        }


def _pearson(x: list[float], y: list[float]) -> float:
    """计算皮尔逊相关系数"""
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if den_x < 1e-12 or den_y < 1e-12:
        return 0.0

    return num / (den_x * den_y)
