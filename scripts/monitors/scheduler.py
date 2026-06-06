"""定时任务调度器 - 定期更新爆款规则"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from .scraper import PlatformScraper
from .analyzer import RuleAnalyzer


class RuleScheduler:
    """规则更新调度器"""

    def __init__(self, data_dir: str = "../data/rules"):
        self.scraper = PlatformScraper()
        self.analyzer = RuleAnalyzer()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.running = False

    async def update_all_rules(self) -> dict:
        """更新所有平台的爆款规则"""
        print(f"[Scheduler] 开始更新规则 - {datetime.now()}")

        all_rules = {}
        hot_data = await self.scraper.fetch_all_platforms()

        for platform, hot_list in hot_data.items():
            if not hot_list:
                print(f"[Scheduler] {platform} 无数据，跳过")
                continue

            # 分析标题模式
            title_analysis = self.analyzer.analyze_title_patterns(hot_list)

            # AI 生成规则
            ai_rules = await self.analyzer.generate_platform_rules(platform, hot_list)

            # 合并规则
            merged = self.analyzer.merge_rules(ai_rules, title_analysis)
            all_rules[platform] = merged

            # 保存到文件
            self._save_rules(platform, merged)
            print(f"[Scheduler] {platform} 规则已更新")

        # 保存汇总
        self._save_summary(all_rules)
        print(f"[Scheduler] 规则更新完成 - {datetime.now()}")
        return all_rules

    def _save_rules(self, platform: str, rules: dict):
        """保存单平台规则"""
        filepath = self.data_dir / f"{platform}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

    def _save_summary(self, all_rules: dict):
        """保存规则汇总"""
        summary = {
            "updated_at": datetime.now().isoformat(),
            "platforms": list(all_rules.keys()),
            "rules": all_rules,
        }
        filepath = self.data_dir / "_summary.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def load_rules(self, platform: str | None = None) -> dict:
        """加载规则"""
        if platform:
            filepath = self.data_dir / f"{platform}.json"
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}

        filepath = self.data_dir / "_summary.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_rules_age(self) -> dict | None:
        """检查规则是否过期"""
        filepath = self.data_dir / "_summary.json"
        if not filepath.exists():
            return {"expired": True, "age_hours": None}

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated_at = datetime.fromisoformat(data["updated_at"])
        age = datetime.now() - updated_at
        return {
            "expired": age > timedelta(hours=12),
            "age_hours": age.total_seconds() / 3600,
            "updated_at": data["updated_at"],
        }

    async def start_auto_update(self, interval_hours: int = 12):
        """启动自动更新循环"""
        self.running = True
        print(f"[Scheduler] 自动更新已启动，间隔 {interval_hours} 小时")

        while self.running:
            try:
                await self.update_all_rules()
            except Exception as e:
                print(f"[Scheduler] 更新失败: {e}")

            await asyncio.sleep(interval_hours * 3600)

    def stop(self):
        """停止自动更新"""
        self.running = False
        print("[Scheduler] 自动更新已停止")
