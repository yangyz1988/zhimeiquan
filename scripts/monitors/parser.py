"""热门内容解析器 — 将原始 DOM/JSON 数据清洗为结构化字段

核心职责：
1. 平台解析器注册表 → 按平台名分发到正确的解析器
2. 通用数据清洗管道 → 去重、去噪、标准化
3. 话题提取 → jieba 分词 + TF 统计（无 jieba 时回退到 2-gram）
4. 钩子类型识别 → 复用 RuleAnalyzer.HOOK_PATTERNS 正则分类
"""

import re
from collections import Counter
from typing import Any

from services.logging import logger

# 尝试导入 jieba（可选依赖）
try:
    import jieba
    _has_jieba = True
except ImportError:
    jieba = None  # type: ignore
    _has_jieba = False

# 中文停用词（高频但无意义的词）
_STOP_WORDS = frozenset({
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
    "们", "那", "这个", "那个", "什么", "怎么", "如何", "为什么",
    "可以", "还是", "但是", "如果", "因为", "所以", "而且", "虽然",
    "应该", "可能", "已经", "一直", "一些", "这些", "那些", "一些",
    "就是", "的话", "不会", "不能", "不是", "出来", "起来", "过来",
    "做", "让", "把", "被", "从", "对", "与", "以", "及", "等",
    "年", "月", "日", "时", "分", "秒", "个", "位", "次", "种",
})


# -------------------------------------------------------
# 钩子类型正则 (复用 RuleAnalyzer.HOOK_PATTERNS)
# -------------------------------------------------------

HOOK_PATTERNS: dict[str, str] = {
    "数字型": r"\d+",
    "反常识型": r"(竟然|没想到|原来|居然|真的|不为人知|揭秘|真相)",
    "痛点型": r"(怎么办|如何|怎么|为什么|解决|摆脱|不再|告别)",
    "利益型": r"(赚钱|省钱|涨粉|爆款|流量|变现|月入|年入|副业)",
    "悬念型": r"(真相|秘密|内幕|曝光|揭露|不说的|没人告诉)",
    "对比型": r"(vs|对比|区别|不同|差距|PK|测评)",
    "情绪型": r"(气死|震惊|无语|绝了|离谱|炸裂|泪目|笑死|哭死)",
    "权威型": r"(专家|大V|官方|认证|专业|资深|医生|律师)",
    "清单型": r"(合集|清单|攻略|指南|教程|推荐|汇总|盘点)",
}


# -------------------------------------------------------
# 通用解析器注册表
# -------------------------------------------------------

class HotContentParser:
    """热门内容解析器注册表 + 统一入口。

    每个平台解析器的 parse() 返回统一结构:
    {
        "titles": [str],           # 清洗后的标题列表
        "topics": [str],           # 高频话题词
        "stats": {                 # 统计摘要
            "total_items": int,
            "avg_title_length": float,
            "top_words": [(str, int)],
        }
    }
    """

    PARSERS: dict[str, Any] = {}  # 在模块底部延迟注册

    # ------------------------------------------------------------------
    # 公共 API
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, platform: str, raw_data: Any) -> dict:
        """根据平台类型分发到对应解析器。

        Args:
            platform: 平台名称 (如 "B站", "知乎")
            raw_data: 浏览器采集到的原始数据 (list[dict] 或 dict)

        Returns:
            统一的解析结果 dict
        """
        # 提取纯标题列表
        titles = cls._extract_titles(raw_data)
        if not titles:
            return cls._build_result([])

        # 平台特定解析器（可选的额外处理）
        parser = cls.PARSERS.get(platform)
        if parser:
            try:
                extra = parser.parse(raw_data)
                # 合并额外提取的标题
                for t in extra.get("titles", []):
                    if t and t not in titles:
                        titles.append(t)
            except Exception as e:
                logger.warning(f"平台解析器 {platform} 异常: {e}")

        # 清洗管道
        titles = cls._clean(titles)

        # 提取话题和钩子
        topics = cls.extract_topics(titles)
        hooks = cls.extract_hook_patterns(titles)
        stats = cls._compute_stats(titles, hooks)

        return {
            "titles": titles[:100],
            "topics": topics[:30],
            "hook_patterns": hooks,
            "stats": stats,
        }

    @classmethod
    def extract_topics(cls, titles: list[str], top_n: int = 20) -> list[str]:
        """从标题列表中提取高频话题词。

        策略：jieba 分词 → 过滤停用词/单字 → TF 排序 → 取 top_n。
        无 jieba 时回退到 2-gram 子串匹配。
        """
        if not titles:
            return []

        word_freq: Counter[str] = Counter()

        if _has_jieba and jieba is not None:
            for title in titles:
                words = jieba.lcut(title)
                for w in words:
                    w = w.strip()
                    if len(w) >= 2 and w not in _STOP_WORDS and not w.isascii():
                        word_freq[w] += 1
        else:
            # 回退：基于 2-3 gram 的简单频率统计
            for title in titles:
                # 提取中文子串作为话题候选
                for gram_len in (3, 4, 2):
                    for i in range(len(title) - gram_len + 1):
                        gram = title[i:i + gram_len]
                        # 只保留纯中文词组
                        if re.match(r'^[一-鿿]+$', gram):
                            word_freq[gram] += 1

        # 取频率最高的词
        return [w for w, _ in word_freq.most_common(top_n)]

    @classmethod
    def extract_hook_patterns(cls, titles: list[str]) -> list[dict]:
        """从标题中识别钩子类型分布。

        Returns:
            [{"type": "数字型", "count": 15, "examples": ["3个技巧...", ...]}, ...]
        """
        if not titles:
            return []

        results = []
        for hook_type, pattern in HOOK_PATTERNS.items():
            matches = []
            for title in titles:
                if re.search(pattern, title):
                    matches.append(title)
            if matches:
                results.append({
                    "type": hook_type,
                    "count": len(matches),
                    "ratio": round(len(matches) / max(len(titles), 1), 3),
                    "examples": matches[:3],
                })

        # 按数量降序
        results.sort(key=lambda x: -x["count"])
        return results

    @classmethod
    def get_cross_platform_topics(
        cls, platform_results: dict[str, list[str]], min_platforms: int = 2
    ) -> list[dict]:
        """跨平台热点发现 — 同一话题出现在多个平台 → 标记为跨平台爆款。

        Args:
            platform_results: {"抖音": ["话题A", ...], "B站": ["话题A", ...], ...}
            min_platforms: 最少出现在几个平台才视为跨平台

        Returns:
            [{"topic": "话题A", "platforms": ["抖音", "B站"], "score": 2}, ...]
        """
        topic_platforms: dict[str, set[str]] = {}
        for platform, topics in platform_results.items():
            for topic in topics:
                if topic not in topic_platforms:
                    topic_platforms[topic] = set()
                topic_platforms[topic].add(platform)

        cross = []
        for topic, platforms in topic_platforms.items():
            if len(platforms) >= min_platforms:
                cross.append({
                    "topic": topic,
                    "platforms": sorted(platforms),
                    "platform_count": len(platforms),
                    "score": len(platforms) * 10,
                })

        cross.sort(key=lambda x: -x["score"])
        return cross

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_titles(raw_data: Any) -> list[str]:
        """从各种形状的原始数据中提取标题列表。"""
        titles: list[str] = []

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    t = item.get("title", item.get("word", item.get("name", item.get("text", ""))))
                    if t:
                        titles.append(str(t).strip())
                elif isinstance(item, str):
                    titles.append(item.strip())
        elif isinstance(raw_data, dict):
            # 尝试常见字段
            for key in ("titles", "words", "items", "data", "list"):
                val = raw_data.get(key)
                if val:
                    titles.extend(HotContentParser._extract_titles(val))
            # 如果没有找到，尝试递归
            if not titles:
                for v in raw_data.values():
                    if isinstance(v, str) and len(v) < 200:
                        titles.append(v.strip())
        elif isinstance(raw_data, str):
            titles.append(raw_data.strip())

        return titles

    @staticmethod
    def _clean(titles: list[str]) -> list[str]:
        """清洗管道：去重 → 去噪 → 长度过滤 → 排序。"""
        seen: set[str] = set()
        cleaned: list[str] = []

        for t in titles:
            if not t:
                continue

            # 去除 HTML 标签
            t = re.sub(r"<[^>]+>", "", t)

            # 去除纯 emoji 前缀
            t = re.sub(
                r"^[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
                r"\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF"
                r"☀-➿\s]+", "", t
            )

            # 压缩空白
            t = re.sub(r"\s+", " ", t).strip()

            # 去噪过滤
            if len(t) < 2 or len(t) > 200:
                continue
            # 纯数字/符号
            if re.match(r"^[\d\s.,，。、！!？?+\-*/=#@￥$%^&()（）\[\]【】]+$", t):
                continue
            # 纯 URL
            if re.match(r"^https?://", t):
                continue

            # 去重（忽略大小写+空白差异）
            dedup_key = re.sub(r"\s+", "", t).lower()
            if dedup_key not in seen:
                seen.add(dedup_key)
                cleaned.append(t)

        return cleaned

    @staticmethod
    def _compute_stats(titles: list[str], hook_patterns: list[dict]) -> dict:
        """计算统计摘要。"""
        if not titles:
            return {"total_items": 0, "avg_title_length": 0, "top_words": []}

        lengths = [len(t) for t in titles]
        avg_len = round(sum(lengths) / len(lengths), 1)

        # 高频词（2-4 字中文词）
        word_freq: Counter[str] = Counter()
        for title in titles:
            for gram_len in (3, 4, 2):
                for i in range(len(title) - gram_len + 1):
                    gram = title[i:i + gram_len]
                    if re.match(r'^[一-鿿]+$', gram):
                        word_freq[gram] += 1

        top_words = word_freq.most_common(10)

        return {
            "total_items": len(titles),
            "avg_title_length": avg_len,
            "min_length": min(lengths),
            "max_length": max(lengths),
            "top_words": [(w, c) for w, c in top_words],
            "hook_distribution": [
                {"type": h["type"], "count": h["count"], "ratio": h["ratio"]}
                for h in hook_patterns[:6]
            ],
        }

    @staticmethod
    def _build_result(titles: list[str]) -> dict:
        """快捷构建解析结果（供平台解析器使用）。"""
        cleaned = HotContentParser._clean(titles)
        return {
            "titles": cleaned[:100],
            "topics": HotContentParser.extract_topics(cleaned),
            "hook_patterns": HotContentParser.extract_hook_patterns(cleaned),
            "stats": HotContentParser._compute_stats(
                cleaned, HotContentParser.extract_hook_patterns(cleaned)
            ),
        }
