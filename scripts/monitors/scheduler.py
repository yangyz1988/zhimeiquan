"""定时任务调度器 - 定期更新爆款规则"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from services.logging import logger
from .scraper import PlatformScraper
from .analyzer import RuleAnalyzer


class RuleScheduler:
    """规则更新调度器"""

    # 首次运行时的种子规则 - 各平台默认爆款特征
    SEED_RULES: dict[str, list[dict]] = {
        "抖音": [
            {"rule": "标题控制在20字以内，前5字制造悬念", "importance": "高", "category": "标题"},
            {"rule": "前3秒必须出现钩子，用反问或数字开场", "importance": "高", "category": "结构"},
            {"rule": "使用热门BGM和特效提升完播率", "importance": "中", "category": "制作"},
            {"rule": "评论区置顶引导话术，提升互动率", "importance": "中", "category": "运营"},
            {"rule": "视频时长控制在15-60秒", "importance": "高", "category": "结构"},
            {"rule": "封面图用大字报+表情包风格", "importance": "中", "category": "封面"},
        ],
        "小红书": [
            {"rule": "标题20字以内，用emoji和数字吸引点击", "importance": "高", "category": "标题"},
            {"rule": "首图必须精美，采用3:4竖版比例", "importance": "高", "category": "封面"},
            {"rule": "正文分段清晰，每段2-3行，多用换行", "importance": "中", "category": "结构"},
            {"rule": "文末加话题标签，不超过5个", "importance": "中", "category": "运营"},
            {"rule": "攻略/测评类内容收藏率高", "importance": "高", "category": "内容"},
            {"rule": "图片数量控制在6-9张", "importance": "中", "category": "封面"},
        ],
        "B站": [
            {"rule": "标题40字以内，突出核心看点", "importance": "高", "category": "标题"},
            {"rule": "前5秒用高能片段或问题引入", "importance": "高", "category": "结构"},
            {"rule": "视频时长5-15分钟完播率最佳", "importance": "中", "category": "结构"},
            {"rule": "弹幕互动设计：提问、投票、填空", "importance": "中", "category": "运营"},
            {"rule": "每周固定时间更新培养用户习惯", "importance": "中", "category": "运营"},
        ],
        "微博": [
            {"rule": "标题包含热点关键词，蹭热搜话题", "importance": "高", "category": "标题"},
            {"rule": "文字控制在140字以内，配多图", "importance": "中", "category": "结构"},
            {"rule": "@相关大V或官号增加曝光", "importance": "高", "category": "运营"},
            {"rule": "发起投票或抽奖提升互动", "importance": "高", "category": "运营"},
        ],
        "知乎": [
            {"rule": "标题用提问形式，包含核心关键词", "importance": "高", "category": "标题"},
            {"rule": "回答结构：结论先行+分点论述+总结", "importance": "高", "category": "结构"},
            {"rule": "引用数据和案例增强说服力", "importance": "中", "category": "内容"},
            {"rule": "关注热点话题，第一时间回答", "importance": "高", "category": "运营"},
            {"rule": "回答长度建议1000-3000字", "importance": "中", "category": "结构"},
        ],
        "公众号": [
            {"rule": "标题64字以内，包含数字和利益点", "importance": "高", "category": "标题"},
            {"rule": "开头300字决定打开率，用故事或痛点开场", "importance": "高", "category": "结构"},
            {"rule": "排版美观，段落间距适中，配图均衡", "importance": "中", "category": "制作"},
            {"rule": "文末引导在看和转发", "importance": "中", "category": "运营"},
            {"rule": "固定推送时间培养用户习惯", "importance": "中", "category": "运营"},
        ],
        "YouTube": [
            {"rule": "标题包含核心关键词，控制在60字符内", "importance": "高", "category": "标题"},
            {"rule": "缩略图用高对比度+人脸特写", "importance": "高", "category": "封面"},
            {"rule": "前30秒介绍视频内容框架", "importance": "高", "category": "结构"},
            {"rule": "视频时长8-15分钟广告收益最佳", "importance": "中", "category": "结构"},
            {"rule": "描述区放关键词和时间戳", "importance": "中", "category": "运营"},
        ],
        "TikTok": [
            {"rule": "标题简短有冲击力，前2秒定成败", "importance": "高", "category": "标题"},
            {"rule": "使用热门话题标签和挑战赛", "importance": "高", "category": "运营"},
            {"rule": "视频时长15-30秒完播率最高", "importance": "高", "category": "结构"},
            {"rule": "利用平台特效和滤镜提高推荐权重", "importance": "中", "category": "制作"},
        ],
        "快手": [
            {"rule": "标题接地气，使用方言或地域特色", "importance": "高", "category": "标题"},
            {"rule": "前3秒有爆点或反转", "importance": "高", "category": "结构"},
            {"rule": "直播预告类内容引流效果好", "importance": "中", "category": "运营"},
            {"rule": "与老铁互动频繁提升账号权重", "importance": "中", "category": "运营"},
        ],
        "视频号": [
            {"rule": "标题30字以内，突出社交传播属性", "importance": "高", "category": "标题"},
            {"rule": "利用朋友圈和社群进行冷启动", "importance": "高", "category": "运营"},
            {"rule": "内容正能量或实用性强分享率高", "importance": "中", "category": "内容"},
            {"rule": "时长1分钟以内完播率最佳", "importance": "中", "category": "结构"},
        ],
        "头条": [
            {"rule": "标题用数字+悬念+利益点组合", "importance": "高", "category": "标题"},
            {"rule": "内容400-800字读完率最高", "importance": "中", "category": "结构"},
            {"rule": "追踪实时热点，快速出稿", "importance": "高", "category": "运营"},
            {"rule": "图文结合，每200字配一张图", "importance": "中", "category": "制作"},
        ],
        "百度热搜": [
            {"rule": "标题包含热搜关键词", "importance": "高", "category": "标题"},
            {"rule": "内容200-500字快速阅读", "importance": "中", "category": "结构"},
            {"rule": "信息准确有来源，增强可信度", "importance": "高", "category": "内容"},
        ],
    }

    # All 13 supported platforms with categories
    ALL_PLATFORMS: dict[str, str] = {
        "抖音": "短视频",
        "小红书": "种草",
        "B站": "中长视频",
        "微博": "社交",
        "知乎": "问答",
        "头条": "资讯",
        "快手": "短视频",
        "YouTube": "中长视频",
        "TikTok": "短视频",
        "公众号": "图文",
        "视频号": "短视频",
        "百度热搜": "资讯",
        "Instagram": "社交",
    }

    def __init__(self, data_dir: str = "../data/rules"):
        self.scraper = PlatformScraper()
        self.analyzer = RuleAnalyzer()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        # 首次运行时自动生成种子规则
        self._ensure_seed_rules()

    def _ensure_seed_rules(self):
        """如果数据目录为空，生成种子规则文件"""
        existing = list(self.data_dir.glob("*.json"))
        if existing:
            return

        logger.info("首次运行，生成种子规则...")
        for platform, rules in self.SEED_RULES.items():
            seed_data = {
                "platform": platform,
                "category": self.ALL_PLATFORMS.get(platform, ""),
                "title_rules": [
                    {
                        "rule": r["rule"],
                        "importance": r["importance"],
                        "category": r["category"],
                    }
                    for r in rules
                ],
                "content_rules": [],
                "hook_patterns": [
                    {"pattern": "数字型", "description": "用具体数字吸引眼球", "examples": ["3个技巧让你...", "99%的人都错了"]},
                    {"pattern": "悬念型", "description": "制造好奇心缺口", "examples": ["没想到...", "原来是这样..."]},
                    {"pattern": "痛点型", "description": "直击用户痛点", "examples": ["怎么办？", "如何解决..."]},
                ],
                "trending_topics": [],
                "best_practices": [],
                "avoid_list": [],
                "score": {"hook": 75, "trend": 70, "engagement": 70, "monetization": 65},
                "is_seed": True,
                "updated_at": datetime.now().isoformat(),
            }
            filepath = self.data_dir / f"{platform}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(seed_data, f, ensure_ascii=False, indent=2)

        # 生成汇总文件
        summary = {
            "updated_at": datetime.now().isoformat(),
            "platforms": list(self.SEED_RULES.keys()),
            "is_seed": True,
            "rules": {p: {"title_rules_count": len(r)} for p, r in self.SEED_RULES.items()},
        }
        filepath = self.data_dir / "_summary.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info("种子规则已生成", platforms=len(self.SEED_RULES))

    def seed_rules(self, force: bool = False) -> int:
        """显式创建/覆盖种子规则文件。

        Args:
            force: 如果为 True，即使文件已存在也重新写入。

        Returns:
            创建的规则文件数量。
        """
        existing = list(self.data_dir.glob("*.json"))
        existing = [f for f in existing if f.name != "_summary.json"]
        if existing and not force:
            logger.info("规则文件已存在，跳过 seed_rules()", existing=len(existing))
            return 0

        created = 0
        for platform, category in self.ALL_PLATFORMS.items():
            filepath = self.data_dir / f"{platform}.json"
            if filepath.exists() and not force:
                continue
            seed = self._build_seed_rule(platform, category)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(seed, f, ensure_ascii=False, indent=2)
            created += 1

        logger.info("seed_rules() 完成", created=created)
        return created

    def _build_seed_rule(self, platform: str, category: str) -> dict:
        """构建单平台的完整种子规则。"""
        return {
            "platform": platform,
            "category": category,
            "last_updated": datetime.now().isoformat(),
            "title_rules": self._default_title_rules(platform),
            "hook_patterns": self._default_hook_patterns(platform),
            "best_practices": self._default_best_practices(platform),
            "algorithm": self._default_algorithm(platform),
            "trending_topics": [],
        }

    async def refresh_rules(self, platform: str) -> dict | None:
        """调用 PlatformScraper 刷新单个平台的规则。

        从平台采集热门数据 -> AI 分析 -> 合并已有规则 -> 保存。

        Args:
            platform: 平台名称。

        Returns:
            更新后的规则 dict，失败返回 None。
        """
        hot_list = await self.scraper.fetch_hot_list(platform)
        if not hot_list:
            logger.info(f"{platform} 无热门数据，跳过刷新")
            return None

        # AI 生成规则
        ai_rules = await self.analyzer.generate_platform_rules(platform, hot_list)

        # 统计标题模式
        title_analysis = self.analyzer.analyze_title_patterns(hot_list)

        # 合并已有规则
        existing = self.load_rules(platform)
        merged = self.analyzer.merge_rules(
            ai_rules, title_analysis, existing_rules=existing
        )
        merged["platform"] = platform
        merged["last_updated"] = datetime.now().isoformat()

        self._save_rules(platform, merged)
        logger.info(f"{platform} 规则已刷新", platform=platform)

        # 用采集到的标题填充 trending_topics
        titles = [h.get("title", "") for h in hot_list if h.get("title")]
        if titles:
            try:
                from monitors.parser import HotContentParser
                topics = HotContentParser.extract_topics(titles)
                if topics:
                    merged["trending_topics"] = topics
                    self._save_rules(platform, merged)
                    logger.info(f"{platform} trending_topics 已填充", topics_count=len(topics))
            except Exception as e:
                logger.warning(f"{platform} trending_topics 填充失败", error=str(e))

        return merged

    async def update_all_rules(self) -> dict:
        """更新所有平台的爆款规则"""
        logger.info("开始更新规则")
        all_rules = {}
        hot_data = await self.scraper.fetch_all_platforms()

        for platform, hot_list in hot_data.items():
            if not hot_list:
                logger.info(f"{platform} 无数据，跳过")
                continue

            # 分析标题模式
            title_analysis = self.analyzer.analyze_title_patterns(hot_list)

            # AI 生成规则
            ai_rules = await self.analyzer.generate_platform_rules(platform, hot_list)

            # 合并规则（保留已有）
            existing = self.load_rules(platform)
            merged = self.analyzer.merge_rules(
                ai_rules, title_analysis, existing_rules=existing
            )
            merged["platform"] = platform
            merged["last_updated"] = datetime.now().isoformat()
            all_rules[platform] = merged

            # 保存到文件
            self._save_rules(platform, merged)
            logger.info(f"{platform} 规则已更新")

        # 保存汇总
        self._save_summary(all_rules)
        logger.info("规则更新完成")
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
        """加载规则。

        首次运行时如果 data/rules/ 为空，自动执行 _ensure_seed_rules() 初始化。

        Args:
            platform: 如果提供，只加载该平台的规则；否则加载完整汇总。

        Returns:
            规则字典。找不到时返回空 dict。
        """
        if platform:
            filepath = self.data_dir / f"{platform}.json"
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            # 尝试种子规则
            if platform in self.SEED_RULES:
                self._ensure_seed_rules()
                if filepath.exists():
                    with open(filepath, "r", encoding="utf-8") as f:
                        return json.load(f)
            return {}

        filepath = self.data_dir / "_summary.json"
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)

        # 没有汇总文件时，从各个平台文件构建
        all_rules = self._load_all_platform_rules()
        if all_rules:
            self._save_summary(all_rules)
        return all_rules

    def _load_all_platform_rules(self) -> dict:
        """从各平台 JSON 文件加载所有规则。"""
        platforms = []
        rules = {}
        for filepath in sorted(self.data_dir.glob("*.json")):
            if filepath.name == "_summary.json":
                continue
            platform_name = filepath.stem
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                platforms.append(platform_name)
                rules[platform_name] = data
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("加载规则文件失败", filename=filepath.name, error=str(e))
                continue

        return {
            "updated_at": datetime.now().isoformat(),
            "platforms": platforms,
            "rules": rules,
        }

    # ------------------------------------------------------------------
    # Rule summary & stats
    # ------------------------------------------------------------------

    def get_rule_summary(self, platform: str | None = None) -> str:
        """返回人类可读的平台规则摘要文本。

        Args:
            platform: 如果提供，返回该平台的摘要；否则返回所有平台摘要。

        Returns:
            格式化的摘要文本。
        """
        if platform:
            rules = self.load_rules(platform)
            if not rules:
                return f"【{platform}】暂无规则数据"

            lines = [
                f"【{platform}】爆款规则摘要",
                f"分类：{rules.get('category', '未知')}",
                f"更新：{rules.get('last_updated', rules.get('updated_at', '未知'))}",
                "",
                "标题规则：",
            ]
            for tr in rules.get("title_rules", []):
                ctr = tr.get("ctr_rating", "")
                lines.append(
                    f"  - {tr.get('type', tr.get('rule', ''))} "
                    f"{ctr} | {tr.get('formula', tr.get('category', ''))}"
                )
            lines.append("")
            lines.append("钩子分布：")
            for hp in rules.get("hook_patterns", []):
                lines.append(
                    f"  - {hp.get('type', hp.get('pattern', ''))}: "
                    f"{hp.get('count', 0)}次 | {hp.get('description', '')}"
                )
            lines.append("")
            lines.append("最佳实践：")
            for bp in rules.get("best_practices", []):
                lines.append(f"  * {bp}")

            algo = rules.get("algorithm", {})
            if algo:
                lines.append("")
                lines.append(f"算法核心指标：{algo.get('core_metric', '')}")
                lines.append(f"冷启动窗口：{algo.get('cold_start_window_hours', '')}")

            return "\n".join(lines)

        # 所有平台
        all_data = self.load_rules()
        rules_dict = all_data.get("rules", {})
        if not rules_dict:
            return "暂无任何平台规则数据"

        lines = [
            "===== 全平台爆款规则摘要 =====",
            f"更新时间：{all_data.get('updated_at', '未知')}",
            f"平台数量：{len(rules_dict)}",
            "",
        ]
        for pname, prules in sorted(rules_dict.items()):
            cat = prules.get("category", "")
            title_count = len(prules.get("title_rules", []))
            hook_count = len(prules.get("hook_patterns", []))
            topic_count = len(prules.get("trending_topics", []))
            lines.append(
                f"  {pname} ({cat}): {title_count}条标题规则, "
                f"{hook_count}种钩子, {topic_count}个热门话题"
            )
        return "\n".join(lines)

    def get_platform_stats(self) -> dict:
        """获取各平台规则统计信息。

        Returns:
            dict: {
                "total_platforms": int,
                "total_titles": int,
                "total_hooks": int,
                "total_topics": int,
                "platforms": [ { name, category, last_updated, ... } ],
                "freshness": { "fresh": int, "stale": int, "unknown": int },
            }
        """
        stats = {
            "total_platforms": 0,
            "total_titles": 0,
            "total_hooks": 0,
            "total_topics": 0,
            "platforms": [],
            "freshness": {"fresh": 0, "stale": 0, "unknown": 0},
        }

        twelve_hours = timedelta(hours=12)
        now = datetime.now()
        all_platform_names = set(self.ALL_PLATFORMS.keys()) | set(self.SEED_RULES.keys())

        for pname in sorted(all_platform_names):
            filepath = self.data_dir / f"{pname}.json"
            file_exists = filepath.exists()
            rules = self.load_rules(pname) if file_exists else {}

            last_updated = rules.get(
                "last_updated", rules.get("updated_at", "")
            )
            stale = True
            if last_updated:
                try:
                    updated = datetime.fromisoformat(last_updated)
                    stale = (now - updated) > twelve_hours
                except (ValueError, TypeError):
                    pass

            title_count = len(rules.get("title_rules", []))
            hook_count = len(rules.get("hook_patterns", []))
            topic_count = len(rules.get("trending_topics", []))

            stats["total_platforms"] += 1
            stats["total_titles"] += title_count
            stats["total_hooks"] += hook_count
            stats["total_topics"] += topic_count

            stats["platforms"].append(
                {
                    "name": pname,
                    "category": rules.get(
                        "category",
                        self.ALL_PLATFORMS.get(pname, ""),
                    ),
                    "last_updated": last_updated,
                    "title_rule_count": title_count,
                    "hook_pattern_count": hook_count,
                    "trending_topic_count": topic_count,
                    "file_exists": file_exists,
                }
            )

            if not last_updated:
                stats["freshness"]["unknown"] += 1
            elif stale:
                stats["freshness"]["stale"] += 1
            else:
                stats["freshness"]["fresh"] += 1

        return stats

    # ------------------------------------------------------------------
    # Rule age / auto-update
    # ------------------------------------------------------------------

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
            "age_hours": round(age.total_seconds() / 3600, 1),
            "updated_at": data["updated_at"],
        }

    async def start_auto_update(self, interval_hours: int = 12):
        """启动自动更新循环"""
        self.running = True
        logger.info("自动更新已启动", interval_hours=interval_hours)

        while self.running:
            try:
                await self.update_all_rules()
            except Exception as e:
                logger.warning("自动更新失败", error=str(e))

            await asyncio.sleep(interval_hours * 3600)

    def stop(self):
        """停止自动更新"""
        self.running = False
        logger.info("自动更新已停止")

    # ------------------------------------------------------------------
    # Default rule builders
    # ------------------------------------------------------------------

    @staticmethod
    def _default_title_rules(platform: str) -> list[dict]:
        """返回默认的标题规则模板。"""
        return [
            {
                "type": "数字承诺型",
                "formula": "数字+承诺+话题",
                "ctr_rating": "★★★★☆",
                "max_chars": 20,
            },
            {
                "type": "好奇心缺口型",
                "formula": "悬念钩子+只说半句",
                "ctr_rating": "★★★★☆",
                "max_chars": 20,
            },
            {
                "type": "痛点共鸣型",
                "formula": "场景+痛点+共鸣",
                "ctr_rating": "★★★★☆",
                "max_chars": 20,
            },
        ]

    @staticmethod
    def _default_hook_patterns(platform: str) -> list[dict]:
        """返回默认的钩子模式模板。"""
        return [
            {"type": "数字型", "count": 10, "description": "用数字吸引眼球"},
            {"type": "悬念型", "count": 8, "description": "制造好奇心缺口"},
            {"type": "情绪型", "count": 6, "description": "触发情绪共鸣"},
        ]

    @staticmethod
    def _default_best_practices(platform: str) -> list[str]:
        """返回默认的最佳实践。"""
        return [
            "保持更新频率",
            "关注用户反馈",
            "与粉丝互动建立社群",
            "分析数据持续优化",
        ]

    @staticmethod
    def _default_algorithm(platform: str) -> dict:
        """返回默认的算法元数据。"""
        return {
            "core_metric": "互动率",
            "cold_start_window_hours": "1-6",
            "qualification_rates": {
                "engagement_rate": ">2%",
            },
        }
