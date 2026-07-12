"""数据追踪器 - SQLite 存储 + 互动率计算 + 表现预测

增强版 DataTracker，替代原有 JSON 文件存储方案。
支持：
- SQLite 持久化（scripts/output/tracker.db）
- 按平台 / 用户查询历史数据
- 互动率计算 engagement_rate = (likes + comments + shares + favorites) / views
- 基于历史数据预测新内容表现
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from analyzers.calibrator import DB_PATH, _ensure_db

ENGAGEMENT_WEIGHTS = {
    "likes": 0.3,
    "comments": 0.4,
    "shares": 0.2,
    "favorites": 0.1,
}


class DataTracker:
    """数据追踪器 - SQLite 存储，支持查询与预测"""

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

    def record_publish(
        self,
        content_id: str,
        user_id: str,
        platform: str,
        title: str,
        fire_score: float | None = None,
        dimension_scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """记录一次发布事件"""
        ds = dimension_scores or {}
        self.conn.execute(
            """INSERT OR IGNORE INTO performance_records
                  (content_id, user_id, platform, fire_score,
                   hook_score, trust_score, retention_score, conversion_score, emotion_score,
                   views, likes, comments, shares, favorites, engagement_rate, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, ?)""",
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
                datetime.now().isoformat(),
            ),
        )
        self.conn.commit()
        return {"content_id": content_id, "recorded": True}

    def update_metrics(self, content_id: str, metrics: dict[str, int]) -> dict[str, Any]:
        """更新内容表现数据并重算互动率"""
        row = self.conn.execute(
            "SELECT id, views, likes, comments, shares, favorites FROM performance_records WHERE content_id = ?",
            (content_id,),
        ).fetchone()

        if row is None:
            return {"error": "记录不存在"}

        views = metrics.get("views", row["views"])
        likes = metrics.get("likes", row["likes"])
        comments = metrics.get("comments", row["comments"])
        shares = metrics.get("shares", row["shares"])
        favorites = metrics.get("favorites", row["favorites"])

        engagement_rate = (
            (likes + comments + shares + favorites) / views if views > 0 else 0.0
        )

        self.conn.execute(
            """UPDATE performance_records
               SET views=?, likes=?, comments=?, shares=?, favorites=?, engagement_rate=?
               WHERE content_id=?""",
            (views, likes, comments, shares, favorites, round(engagement_rate, 6), content_id),
        )
        self.conn.commit()

        return {
            "content_id": content_id,
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "favorites": favorites,
            "engagement_rate": round(engagement_rate, 4),
        }

    def get_platform_history(
        self, user_id: str, platform: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """按平台查询历史数据"""
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

    def get_user_summary(self, user_id: str) -> dict[str, Any]:
        """获取用户全平台汇总"""
        rows = self.conn.execute(
            """SELECT platform,
                      COUNT(*) AS total,
                      SUM(views) AS total_views,
                      SUM(likes) AS total_likes,
                      SUM(comments) AS total_comments,
                      SUM(shares) AS total_shares,
                      SUM(favorites) AS total_favorites,
                      AVG(engagement_rate) AS avg_engagement
               FROM performance_records
               WHERE user_id = ?
               GROUP BY platform""",
            (user_id,),
        ).fetchall()

        platforms = {}
        for r in rows:
            platforms[r["platform"]] = {
                "total_content": r["total"],
                "total_views": r["total_views"],
                "total_likes": r["total_likes"],
                "total_comments": r["total_comments"],
                "total_shares": r["total_shares"],
                "total_favorites": r["total_favorites"],
                "avg_engagement_rate": round(r["avg_engagement"] or 0, 4),
            }
        return {"user_id": user_id, "platforms": platforms}

    def predict_engagement(
        self, user_id: str, platform: str, dimension_scores: dict[str, float]
    ) -> dict[str, Any]:
        """基于历史数据预测新内容的互动率

        算法：
        1. 取该用户该平台最近 N 条数据
        2. 计算加权互动分 = 各维度分 × 平台平均互动率贡献权重
        3. 返回预测互动率和置信度
        """
        history = self.get_platform_history(user_id, platform, limit=30)

        if len(history) < 3:
            return {
                "predicted_engagement": 0.0,
                "confidence": "low",
                "message": "历史数据不足，无法可靠预测",
            }

        avg_engagement = sum(h["engagement_rate"] for h in history) / len(history)
        scores = [h["fire_score"] for h in history if h["fire_score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else 50.0

        current_total = sum(dimension_scores.get(d, 0) for d in ENGAGEMENT_WEIGHTS)
        predicted = avg_engagement * (current_total / max(avg_score, 1))

        variance = sum(
            (h["engagement_rate"] - avg_engagement) ** 2 for h in history
        ) / len(history)
        confidence = "high" if variance < 0.001 else "medium" if variance < 0.01 else "low"

        return {
            "predicted_engagement": round(min(predicted, 1.0), 4),
            "avg_historical_engagement": round(avg_engagement, 4),
            "sample_count": len(history),
            "confidence": confidence,
        }

    def get_fire_score_accuracy(self, user_id: str, platform: str) -> dict[str, Any]:
        """评估 Fire Score 预测准确度"""
        rows = self.conn.execute(
            """SELECT fire_score, engagement_rate
               FROM performance_records
               WHERE user_id = ? AND platform = ?
                 AND fire_score IS NOT NULL
                 AND engagement_rate > 0
               ORDER BY created_at DESC
               LIMIT 50""",
            (user_id, platform),
        ).fetchall()

        if len(rows) < 3:
            return {"accuracy": None, "message": "数据不足"}

        scores = [r["fire_score"] for r in rows]
        engagements = [r["engagement_rate"] for r in rows]

        mean_s = sum(scores) / len(scores)
        mean_e = sum(engagements) / len(engagements)

        num = sum((s - mean_s) * (e - mean_e) for s, e in zip(scores, engagements))
        den_s = sum((s - mean_s) ** 2 for s in scores) ** 0.5
        den_e = sum((e - mean_e) ** 2 for e in engagements) ** 0.5

        correlation = num / (den_s * den_e) if den_s > 0 and den_e > 0 else 0.0

        return {
            "correlation": round(correlation, 4),
            "sample_count": len(rows),
            "avg_fire_score": round(mean_s, 2),
            "avg_engagement": round(mean_e, 4),
        }
