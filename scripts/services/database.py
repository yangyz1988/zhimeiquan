"""统一数据库服务 — SQLite 后端数据层

提供与前端 Prisma schema 一致的 Python 数据访问层。
数据库文件: scripts/output/zhimeiquan.db
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent / "output" / "zhimeiquan.db"


def _json_serialize(obj: Any) -> str:
    """JSON 序列化，处理 datetime"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class Database:
    """SQLite 数据库连接池"""

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._create_tables()
        return self._conn

    def _create_tables(self):
        """创建所有表（与 Prisma schema 一致）"""
        self._conn.executescript("""
            -- 22. MediaAsset
            CREATE TABLE IF NOT EXISTS media_assets (
                id           TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                file_name    TEXT NOT NULL,
                original_name TEXT,
                mime_type    TEXT NOT NULL,
                size         INTEGER DEFAULT 0,
                url          TEXT NOT NULL,
                thumbnail_url TEXT,
                width        INTEGER,
                height       INTEGER,
                duration     REAL,
                alt_text     TEXT,
                tags         TEXT,  -- JSON array
                folder       TEXT,
                usage_count  INTEGER DEFAULT 0,
                is_public    INTEGER DEFAULT 0,
                metadata     TEXT,  -- JSON
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_media_user ON media_assets(user_id);
            CREATE INDEX IF NOT EXISTS idx_media_folder ON media_assets(user_id, folder);

            -- 23. Comment
            CREATE TABLE IF NOT EXISTS comments (
                id           TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                body         TEXT NOT NULL,
                is_resolved  INTEGER DEFAULT 0,
                parent_id    TEXT,
                entity_type  TEXT NOT NULL,
                entity_id    TEXT NOT NULL,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_comments_entity ON comments(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id);

            -- 24. Tags
            CREATE TABLE IF NOT EXISTS tags (
                id          TEXT PRIMARY KEY,
                name        TEXT UNIQUE NOT NULL,
                slug        TEXT UNIQUE NOT NULL,
                color       TEXT,
                description TEXT,
                usage_count INTEGER DEFAULT 0,
                is_system   INTEGER DEFAULT 0,
                group_id    TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_tags_group ON tags(group_id);

            CREATE TABLE IF NOT EXISTS tag_groups (
                id          TEXT PRIMARY KEY,
                name        TEXT UNIQUE NOT NULL,
                slug        TEXT UNIQUE NOT NULL,
                color       TEXT,
                description TEXT,
                sort_order  INTEGER DEFAULT 0,
                is_collapsed INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS content_tags (
                tag_id      TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id   TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (tag_id, entity_type, entity_id),
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_content_tags_entity ON content_tags(entity_type, entity_id);

            -- 25. Subscription
            CREATE TABLE IF NOT EXISTS subscriptions (
                id                   TEXT PRIMARY KEY,
                user_id              TEXT UNIQUE NOT NULL,
                status               TEXT DEFAULT 'ACTIVE',
                current_period_start TEXT,
                current_period_end   TEXT,
                cancel_at_period_end INTEGER DEFAULT 0,
                canceled_at          TEXT,
                trial_end            TEXT,
                stripe_subscription_id TEXT UNIQUE,
                stripe_customer_id   TEXT,
                stripe_price_id      TEXT,
                payment_method       TEXT,
                plan_tier            TEXT DEFAULT 'FREE',
                auto_renew           INTEGER DEFAULT 1,
                metadata             TEXT,
                created_at           TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

            CREATE TABLE IF NOT EXISTS invoices (
                id              TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL,
                stripe_invoice_id TEXT UNIQUE,
                amount          REAL NOT NULL,
                currency        TEXT DEFAULT 'CNY',
                status          TEXT NOT NULL,
                invoice_url     TEXT,
                invoice_pdf     TEXT,
                period_start    TEXT,
                period_end      TEXT,
                paid_at         TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_invoices_subscription ON invoices(subscription_id);

            CREATE TABLE IF NOT EXISTS billing_cycles (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                cycle_start     TEXT NOT NULL,
                cycle_end       TEXT NOT NULL,
                credits_used    INTEGER DEFAULT 0,
                credits_limit   INTEGER DEFAULT 1000,
                api_calls       INTEGER DEFAULT 0,
                api_calls_limit INTEGER DEFAULT 10000,
                storage_bytes   REAL DEFAULT 0,
                storage_limit   REAL DEFAULT 1073741824,
                is_overage      INTEGER DEFAULT 0,
                overage_charges REAL DEFAULT 0,
                metadata        TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, cycle_start)
            );
            CREATE INDEX IF NOT EXISTS idx_billing_cycles_user ON billing_cycles(user_id, cycle_end);

            -- 26. DistributionChannel
            CREATE TABLE IF NOT EXISTS distribution_channels (
                id              TEXT PRIMARY KEY,
                user_id         TEXT NOT NULL,
                name            TEXT NOT NULL,
                platform        TEXT NOT NULL,
                channel_type    TEXT DEFAULT 'SOCIAL',
                account_name    TEXT,
                account_id      TEXT,
                config          TEXT,
                daily_limit     INTEGER,
                scheduled_count INTEGER DEFAULT 0,
                is_active       INTEGER DEFAULT 1,
                last_sync_at    TEXT,
                health_status   TEXT DEFAULT 'UNKNOWN',
                metrics         TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, platform, account_id)
            );
            CREATE INDEX IF NOT EXISTS idx_channels_user ON distribution_channels(user_id, platform);

            CREATE TABLE IF NOT EXISTS publish_logs (
                id           TEXT PRIMARY KEY,
                channel_id   TEXT NOT NULL,
                entity_id    TEXT NOT NULL,
                entity_type  TEXT NOT NULL,
                platform     TEXT NOT NULL,
                external_url TEXT,
                status       TEXT DEFAULT 'PENDING',
                error_message TEXT,
                retry_count  INTEGER DEFAULT 0,
                published_at TEXT,
                scheduled_at TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (channel_id) REFERENCES distribution_channels(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_publish_logs_channel ON publish_logs(channel_id, status);

            CREATE TABLE IF NOT EXISTS channel_metrics (
                id            TEXT PRIMARY KEY,
                channel_id    TEXT NOT NULL,
                followers     INTEGER DEFAULT 0,
                engagement    REAL DEFAULT 0,
                posts         INTEGER DEFAULT 0,
                avg_views     REAL DEFAULT 0,
                avg_likes     REAL DEFAULT 0,
                avg_comments  REAL DEFAULT 0,
                avg_shares    REAL DEFAULT 0,
                top_performing TEXT,
                collected_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (channel_id) REFERENCES distribution_channels(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_channel_metrics ON channel_metrics(channel_id, collected_at);

            -- 27. TrendEvent
            CREATE TABLE IF NOT EXISTS trend_events (
                id                 TEXT PRIMARY KEY,
                title              TEXT NOT NULL,
                summary            TEXT,
                source_platform    TEXT NOT NULL,
                source_url         TEXT,
                category           TEXT,
                keywords           TEXT,
                heat_score         REAL DEFAULT 0,
                heat_trend         TEXT DEFAULT 'STABLE',
                mention_count      INTEGER DEFAULT 0,
                first_seen_at      TEXT NOT NULL,
                last_seen_at       TEXT NOT NULL DEFAULT (datetime('now')),
                peak_at            TEXT,
                is_active          INTEGER DEFAULT 1,
                lifespan           INTEGER,
                related_events     TEXT,
                content_suggestions TEXT,
                created_at         TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at         TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_trends_platform ON trend_events(source_platform, is_active);
            CREATE INDEX IF NOT EXISTS idx_trends_score ON trend_events(heat_score);

            CREATE TABLE IF NOT EXISTS trend_snapshots (
                id              TEXT PRIMARY KEY,
                event_id        TEXT NOT NULL,
                heat_score      REAL NOT NULL,
                mention_count   INTEGER NOT NULL,
                related_count   INTEGER DEFAULT 0,
                sentiment_ratio TEXT,
                top_keywords    TEXT,
                source_breakdown TEXT,
                recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (event_id) REFERENCES trend_events(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_trend_snapshots ON trend_snapshots(event_id, recorded_at);
        """)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.conn
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# 全局单例
_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def generate_id() -> str:
    """生成 cuid 风格 ID"""
    import random
    import time
    timestamp = hex(int(time.time() * 1000))[2:]
    random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=25))
    return f"{timestamp}{random_part}"[:25]