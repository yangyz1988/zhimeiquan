"""规则变化检测与通知

检测规则 JSON 文件的差异，生成人类可读的变化摘要。
通知方式：控制台日志 + 可选的 Webhook 回调（Slack/钉钉/飞书等）。

典型用法:
    notifier = RuleChangeNotifier(rules_dir="../data/rules")
    changes = notifier.detect_changes()
    if changes:
        notifier.notify(changes)
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from services.logging import logger


class RuleChangeNotifier:
    """检测规则变化并通知。

    通过比较新旧规则 JSON 的 hash 来检测变化，
    生成结构化变更摘要，支持多种通知渠道。
    """

    def __init__(self, rules_dir: str = "../data/rules"):
        self._rules_dir = Path(rules_dir)
        self._snapshots: dict[str, str] = {}  # platform → md5 hash
        self._webhook_url = os.getenv("RULE_CHANGE_WEBHOOK_URL", "")
        self._load_snapshots()

    def _load_snapshots(self):
        """从快照文件加载上次规则 hash。"""
        snapshot_file = self._rules_dir / "_snapshots.json"
        if snapshot_file.exists():
            try:
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    self._snapshots = json.load(f)
            except Exception:
                self._snapshots = {}

    def _save_snapshots(self):
        """保存当前规则 hash 为快照。"""
        snapshot_file = self._rules_dir / "_snapshots.json"
        try:
            with open(snapshot_file, "w", encoding="utf-8") as f:
                json.dump(self._snapshots, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存规则快照失败: {e}")

    def _hash_file(self, filepath: Path) -> str:
        """计算规则文件的 MD5 hash。"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""

    def detect_changes(self) -> list[dict]:
        """比较当前规则与上次快照，返回变更列表。

        Returns:
            [
                {
                    "platform": "抖音",
                    "change_type": "updated" | "new" | "removed",
                    "summary": "标题规则从 5 条变为 6 条",
                    "diff": {...},
                },
                ...
            ]
        """
        changes = []

        # 扫描当前规则文件
        current_files = {}
        for filepath in sorted(self._rules_dir.glob("*.json")):
            if filepath.name in ("_summary.json", "_snapshots.json"):
                continue
            current_files[filepath.stem] = self._hash_file(filepath)

        # 检查变化
        for platform, current_hash in current_files.items():
            previous_hash = self._snapshots.get(platform)

            if previous_hash is None:
                changes.append({
                    "platform": platform,
                    "change_type": "new",
                    "summary": f"{platform} 规则首次生成",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                })
            elif current_hash != previous_hash:
                changes.append({
                    "platform": platform,
                    "change_type": "updated",
                    "summary": f"{platform} 规则已更新",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                })

        # 检查被移除的
        for platform in self._snapshots:
            if platform not in current_files:
                changes.append({
                    "platform": platform,
                    "change_type": "removed",
                    "summary": f"{platform} 规则已被移除",
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                })

        # 更新快照
        self._snapshots = current_files
        if changes:
            self._save_snapshots()

        return changes

    def notify(self, changes: list[dict]):
        """发送变更通知。

        当前支持：
        - 控制台日志（始终启用）
        - Webhook POST（需配置 RULE_CHANGE_WEBHOOK_URL）
        """
        if not changes:
            return

        # 控制台日志
        for change in changes:
            logger.info(
                f"规则变化: [{change['change_type']}] {change['summary']}",
                platform=change["platform"],
                change_type=change["change_type"],
            )

        # Webhook 通知
        if self._webhook_url:
            self._send_webhook(changes)

    async def notify_async(self, changes: list[dict]):
        """异步通知（Webhook 使用 httpx 异步客户端）。"""
        if not changes:
            return

        for change in changes:
            logger.info(
                f"规则变化: [{change['change_type']}] {change['summary']}",
                platform=change["platform"],
                change_type=change["change_type"],
            )

        if self._webhook_url:
            await self._send_webhook_async(changes)

    def _send_webhook(self, changes: list[dict]):
        """同步发送 Webhook。"""
        try:
            payload = {
                "text": "智媒圈 规则变化通知",
                "changes": changes,
                "total": len(changes),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            resp = httpx.post(
                self._webhook_url,
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            logger.info(f"Webhook 通知已发送", changes=len(changes))
        except Exception as e:
            logger.warning(f"Webhook 通知发送失败: {e}")

    async def _send_webhook_async(self, changes: list[dict]):
        """异步发送 Webhook。"""
        try:
            payload = {
                "text": "智媒圈 规则变化通知",
                "changes": changes,
                "total": len(changes),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self._webhook_url, json=payload)
                resp.raise_for_status()
            logger.info(f"Webhook 通知已发送", changes=len(changes))
        except Exception as e:
            logger.warning(f"Webhook 通知发送失败: {e}")

    def get_change_history(self) -> list[dict]:
        """获取当前与快照的差异概览。"""
        history = []
        current_files = {}

        for filepath in sorted(self._rules_dir.glob("*.json")):
            if filepath.name in ("_summary.json", "_snapshots.json"):
                continue
            current_files[filepath.stem] = {
                "hash": self._hash_file(filepath),
                "has_snapshot": filepath.stem in self._snapshots,
                "changed": (
                    self._hash_file(filepath) != self._snapshots.get(filepath.stem, "")
                ),
            }

        for platform, info in current_files.items():
            status = "unchanged"
            if not info["has_snapshot"]:
                status = "new"
            elif info["changed"]:
                status = "changed"

            history.append({
                "platform": platform,
                "status": status,
            })

        return history
