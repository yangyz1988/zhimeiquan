"""竞品内容监控 - 追踪对标账号的内容策略和表现"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from services.logging import logger


class CompetitorMonitor:
    """竞品监控器"""

    def __init__(self, data_dir: str = "../data/competitors"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._competitors_file = self.data_dir / "_competitors.json"
        self._ensure_index()

    def _ensure_index(self):
        """确保竞品索引文件存在"""
        if not self._competitors_file.exists():
            with open(self._competitors_file, "w", encoding="utf-8") as f:
                json.dump({"competitors": []}, f, ensure_ascii=False, indent=2)

    def _load_index(self) -> list[dict]:
        """加载竞品索引"""
        with open(self._competitors_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["competitors"]

    def _save_index(self, competitors: list[dict]):
        """保存竞品索引"""
        with open(self._competitors_file, "w", encoding="utf-8") as f:
            json.dump({"competitors": competitors}, f, ensure_ascii=False, indent=2)

    def _competitor_path(self, competitor_id: str) -> Path:
        """获取竞品数据目录"""
        comp_dir = self.data_dir / competitor_id
        comp_dir.mkdir(parents=True, exist_ok=True)
        return comp_dir

    def _generate_id(self) -> str:
        """生成唯一竞品 ID"""
        from uuid import uuid4
        return uuid4().hex[:12]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_competitor(self, user_id: str, platform: str, account_id: str, account_name: str) -> dict:
        """添加竞品账号"""
        competitors = self._load_index()

        # 查重
        for c in competitors:
            if c["account_id"] == account_id and c["platform"] == platform and c["user_id"] == user_id:
                return {"error": "该竞品账号已存在", "competitor": c}

        competitor = {
            "id": self._generate_id(),
            "user_id": user_id,
            "platform": platform,
            "account_id": account_id,
            "account_name": account_name,
            "added_at": datetime.now().isoformat(),
            "total_content": 0,
            "last_activity": None,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
        }

        competitors.append(competitor)
        self._save_index(competitors)
        logger.info("竞品账号添加成功", competitor_id=competitor["id"], platform=platform, account_name=account_name)

        # 创建竞品数据目录
        self._competitor_path(competitor["id"])

        return {"competitor": competitor}

    def remove_competitor(self, competitor_id: str) -> bool:
        """移除竞品账号"""
        competitors = self._load_index()
        before = len(competitors)
        competitors = [c for c in competitors if c["id"] != competitor_id]

        if len(competitors) == before:
            return False

        self._save_index(competitors)

        # 保留数据文件，仅从索引移除
        logger.info("竞品账号已移除", competitor_id=competitor_id)
        return True

    def list_competitors(self, user_id: str) -> list[dict]:
        """列出用户监控的所有竞品"""
        competitors = self._load_index()
        return [c for c in competitors if c["user_id"] == user_id]

    # ------------------------------------------------------------------
    # 内容记录
    # ------------------------------------------------------------------

    def record_content(self, competitor_id: str, content_data: dict) -> dict:
        """记录竞品发布的内容

        content_data 字段:
            - content_id (str): 平台内容 ID
            - title (str): 标题
            - content_type (str): 图文/视频/短剧等
            - published_at (str): ISO 发布时间
            - metrics (dict): views, likes, comments, shares, saves
            - topics (list[str]): 内容主题标签
            - style_tags (list[str]): 风格标签 (如 "教程", "测评", "Vlog")
            - summary (str): 内容摘要
        """
        comp_dir = self._competitor_path(competitor_id)

        platform_id = content_data.get("content_id", f"local_{datetime.now().timestamp()}")
        filepath = comp_dir / f"{platform_id}.json"

        if filepath.exists():
            return {"error": "该内容已记录"}

        record = {
            "competitor_id": competitor_id,
            "content_id": platform_id,
            "title": content_data.get("title", ""),
            "content_type": content_data.get("content_type", "图文"),
            "published_at": content_data.get("published_at", datetime.now().isoformat()),
            "recorded_at": datetime.now().isoformat(),
            "metrics": {
                "views": content_data.get("metrics", {}).get("views", 0),
                "likes": content_data.get("metrics", {}).get("likes", 0),
                "comments": content_data.get("metrics", {}).get("comments", 0),
                "shares": content_data.get("metrics", {}).get("shares", 0),
                "saves": content_data.get("metrics", {}).get("saves", 0),
            },
            "topics": content_data.get("topics", []),
            "style_tags": content_data.get("style_tags", []),
            "summary": content_data.get("summary", ""),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 更新索引汇总
        self._update_competitor_summary(competitor_id)

        return {"record": record}

    def _update_competitor_summary(self, competitor_id: str):
        """更新竞品汇总数据"""
        comp_dir = self._competitor_path(competitor_id)
        competitors = self._load_index()

        total_content = 0
        total_views = 0
        total_likes = 0
        total_comments = 0
        total_shares = 0
        last_activity = None

        for f in comp_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as file:
                record = json.load(file)
            total_content += 1
            m = record["metrics"]
            total_views += m.get("views", 0)
            total_likes += m.get("likes", 0)
            total_comments += m.get("comments", 0)
            total_shares += m.get("shares", 0)

            pub = record.get("published_at")
            if pub and (last_activity is None or pub > last_activity):
                last_activity = pub

        for c in competitors:
            if c["id"] == competitor_id:
                c["total_content"] = total_content
                c["total_views"] = total_views
                c["total_likes"] = total_likes
                c["total_comments"] = total_comments
                c["total_shares"] = total_shares
                c["last_activity"] = last_activity
                break

        self._save_index(competitors)

    # ------------------------------------------------------------------
    # 分析
    # ------------------------------------------------------------------

    def analyze_competitor(self, competitor_id: str) -> dict:
        """分析竞品的内容策略"""
        comp_dir = self._competitor_path(competitor_id)
        records = []

        for f in sorted(comp_dir.glob("*.json")):
            with open(f, "r", encoding="utf-8") as file:
                records.append(json.load(file))

        if not records:
            return {
                "topic_focus": [],
                "posting_frequency": "暂无数据",
                "avg_engagement": 0,
                "top_performing": [],
                "style_analysis": [],
                "total_analyzed": 0,
            }

        # 主题分布
        topic_count: dict[str, int] = {}
        for r in records:
            for t in r.get("topics", []):
                topic_count[t] = topic_count.get(t, 0) + 1

        sorted_topics = sorted(topic_count.items(), key=lambda x: -x[1])
        topic_focus = [{"topic": t, "count": c, "ratio": round(c / len(records) * 100, 1)} for t, c in sorted_topics[:10]]

        # 风格分析
        style_count: dict[str, int] = {}
        for r in records:
            for s in r.get("style_tags", []):
                style_count[s] = style_count.get(s, 0) + 1

        sorted_styles = sorted(style_count.items(), key=lambda x: -x[1])
        style_analysis = [{"style": s, "count": c, "ratio": round(c / len(records) * 100, 1)} for s, c in sorted_styles[:10]]

        # 发布频率
        if len(records) >= 2:
            dates = []
            for r in records:
                try:
                    dates.append(datetime.fromisoformat(r["published_at"]))
                except (ValueError, TypeError):
                    continue
            if len(dates) >= 2:
                dates.sort()
                span_days = (dates[-1] - dates[0]).days + 1
                freq = round(len(dates) / max(span_days, 1), 1)
                posting_frequency = f"平均每天 {freq} 条内容"
            else:
                posting_frequency = "数据不足"
        else:
            posting_frequency = "数据不足（< 2 条）"

        # 平均互动率
        total_engagement = 0
        for r in records:
            m = r["metrics"]
            views = m.get("views", 0)
            if views > 0:
                rate = (m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0)) / views * 100
                total_engagement += rate

        avg_engagement = round(total_engagement / max(len(records), 1), 2)

        # 最佳表现内容 (按互动量排序)
        scored = []
        for r in records:
            m = r["metrics"]
            total = m.get("likes", 0) + m.get("comments", 0) * 2 + m.get("shares", 0) * 3
            scored.append((total, r))

        scored.sort(key=lambda x: -x[0])
        top_performing = [
            {
                "title": r["title"],
                "content_type": r.get("content_type", ""),
                "total_interaction": score,
                "metrics": r["metrics"],
                "published_at": r.get("published_at", ""),
                "summary": r.get("summary", ""),
            }
            for score, r in scored[:5]
        ]

        return {
            "topic_focus": topic_focus,
            "posting_frequency": posting_frequency,
            "avg_engagement": avg_engagement,
            "top_performing": top_performing,
            "style_analysis": style_analysis,
            "total_analyzed": len(records),
        }

    def get_comparison(self, user_id: str, competitor_id: str) -> dict:
        """对比用户与竞品的表现差异"""
        # 竞品数据
        comp_analysis = self.analyze_competitor(competitor_id)

        # 用户自己的内容数据 - 复用分析逻辑
        user_competitors = self.list_competitors(user_id)
        comp_info = None
        for c in user_competitors:
            if c["id"] == competitor_id:
                comp_info = c
                break

        # 加载用户本地数据 (假设存在)
        user_dir = Path(self.data_dir).parent / "analytics"
        user_records = []
        if user_dir.exists():
            for f in user_dir.glob("*.json"):
                with open(f, "r", encoding="utf-8") as file:
                    user_records.append(json.load(file))

        # 计算用户互动率
        user_total_engagement = 0
        for r in user_records:
            m = r.get("metrics", {})
            views = m.get("views", 0)
            if views > 0:
                rate = (m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0)) / views * 100
                user_total_engagement += rate

        user_avg_engagement = round(user_total_engagement / max(len(user_records), 1), 2) if user_records else 0

        return {
            "competitor": {
                "name": comp_info["account_name"] if comp_info else "未知",
                "platform": comp_info["platform"] if comp_info else "",
                "total_content": comp_info.get("total_content", 0) if comp_info else 0,
                "avg_engagement": comp_analysis["avg_engagement"],
                "top_topics": [t["topic"] for t in comp_analysis["topic_focus"][:5]],
            },
            "user": {
                "total_content": len(user_records),
                "avg_engagement": user_avg_engagement,
            },
            "comparison": {
                "engagement_gap": round(comp_analysis["avg_engagement"] - user_avg_engagement, 2),
                "content_gap": (comp_info.get("total_content", 0) if comp_info else 0) - len(user_records),
            },
        }
