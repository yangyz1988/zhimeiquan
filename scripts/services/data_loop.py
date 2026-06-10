"""数据闭环服务 - 发布→数据→校准"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class DataTracker:
    """数据追踪器 - 记录发布内容的表现数据"""

    def __init__(self, data_dir: str = "../data/analytics"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def record_publish(
        self,
        project_id: str,
        platform: str,
        title: str,
        content_id: str,
        fire_score: float | None = None,
    ) -> dict:
        """记录发布事件"""
        record = {
            "project_id": project_id,
            "platform": platform,
            "title": title,
            "content_id": content_id,
            "published_at": datetime.now().isoformat(),
            "metrics": {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "saves": 0,
                "follows": 0,
                "watch_time": 0,
            },
            "fire_score": fire_score,
            "updated_at": datetime.now().isoformat(),
        }

        filepath = self.data_dir / f"{project_id}_{content_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return record

    def update_metrics(self, project_id: str, content_id: str, metrics: dict) -> dict:
        """更新内容表现数据"""
        filepath = self.data_dir / f"{project_id}_{content_id}.json"
        if not filepath.exists():
            return {"error": "记录不存在"}

        with open(filepath, "r", encoding="utf-8") as f:
            record = json.load(f)

        record["metrics"].update(metrics)
        record["updated_at"] = datetime.now().isoformat()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return record

    def get_project_analytics(self, project_id: str) -> dict:
        """获取项目数据分析"""
        records = []
        for f in self.data_dir.glob(f"{project_id}_*.json"):
            with open(f, "r", encoding="utf-8") as file:
                records.append(json.load(file))

        if not records:
            return {"total_content": 0, "total_views": 0}

        total_views = sum(r["metrics"]["views"] for r in records)
        total_likes = sum(r["metrics"]["likes"] for r in records)
        total_comments = sum(r["metrics"]["comments"] for r in records)
        total_shares = sum(r["metrics"]["shares"] for r in records)

        return {
            "total_content": len(records),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "avg_engagement": (total_likes + total_comments + total_shares)
            / max(total_views, 1)
            * 100,
            "content_list": records,
        }

    def get_platform_summary(self) -> dict:
        """获取平台汇总数据"""
        platform_data = {}
        for f in self.data_dir.glob("*.json"):
            with open(f, "r", encoding="utf-8") as file:
                record = json.load(file)
            platform = record["platform"]
            if platform not in platform_data:
                platform_data[platform] = {"count": 0, "views": 0, "likes": 0}
            platform_data[platform]["count"] += 1
            platform_data[platform]["views"] += record["metrics"]["views"]
            platform_data[platform]["likes"] += record["metrics"]["likes"]

        return platform_data

    def get_avg_fire_score(self, project_id: str | None = None) -> float | None:
        """获取平均 Fire Score"""
        scores = []
        pattern = f"{project_id}_*.json" if project_id else "*.json"
        for f in self.data_dir.glob(pattern):
            with open(f, "r", encoding="utf-8") as file:
                record = json.load(file)
            score = record.get("fire_score")
            if score is not None:
                scores.append(score)
        return round(sum(scores) / len(scores), 1) if scores else None


class ABTester:
    """A/B 测试管理器"""

    def __init__(self, data_dir: str = "../data/ab_tests"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create_test(self, test_id: str, project_id: str, variants: list[dict]) -> dict:
        """创建 A/B 测试"""
        test = {
            "test_id": test_id,
            "project_id": project_id,
            "variants": [
                {
                    "id": f"variant_{i}",
                    "title": v.get("title", ""),
                    "content": v.get("content", ""),
                    "metrics": {"views": 0, "likes": 0, "comments": 0, "shares": 0},
                }
                for i, v in enumerate(variants)
            ],
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "winner": None,
        }

        filepath = self.data_dir / f"{test_id}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(test, f, ensure_ascii=False, indent=2)

        return test

    def update_variant_metrics(
        self, test_id: str, variant_id: str, metrics: dict
    ) -> dict:
        """更新变体数据"""
        filepath = self.data_dir / f"{test_id}.json"
        if not filepath.exists():
            return {"error": "测试不存在"}

        with open(filepath, "r", encoding="utf-8") as f:
            test = json.load(f)

        for variant in test["variants"]:
            if variant["id"] == variant_id:
                variant["metrics"].update(metrics)
                break

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(test, f, ensure_ascii=False, indent=2)

        return test

    def get_winner(self, test_id: str) -> dict:
        """获取测试结果"""
        filepath = self.data_dir / f"{test_id}.json"
        if not filepath.exists():
            return {"error": "测试不存在"}

        with open(filepath, "r", encoding="utf-8") as f:
            test = json.load(f)

        # 计算综合得分
        best_score = 0
        winner = None
        for variant in test["variants"]:
            m = variant["metrics"]
            score = (
                m["views"] * 0.1
                + m["likes"] * 0.3
                + m["comments"] * 0.4
                + m["shares"] * 0.2
            )
            if score > best_score:
                best_score = score
                winner = variant

        return {
            "test_id": test_id,
            "winner": winner,
            "all_variants": test["variants"],
        }
