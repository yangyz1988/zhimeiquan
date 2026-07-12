"""轻量级知识图谱 - 关键词检索系统

基于方法论文件和模板文件构建结构化知识库。
无外部向量数据库依赖，纯文件解析 + 内存缓存。
"""

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from services.logging import logger


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTENT_DIR = PROJECT_ROOT / "content"
METHODOLOGY_DIR = CONTENT_DIR / "methodology"
TEMPLATES_DIR = CONTENT_DIR / "templates"
PROMPTS_DIR = CONTENT_DIR / "prompts"
CACHE_FILE = PROJECT_ROOT / "data" / "knowledge_cache.json"


class KnowledgeGraph:
    """轻量级知识图谱 - 基于关键词的检索系统"""

    # 已知的方法论分类标签
    METHODOLOGY_TAGS: dict[str, list[str]] = {
        "hook": ["钩子", "hook", "前3秒", "注意力", "标题"],
        "trust": ["信任", "trust", "权威", "背书", "可信"],
        "retention": ["留存", "retention", "完播", "停留", "时长"],
        "conversion": ["转化", "conversion", "CTA", "引导", "行动"],
        "emotion": ["情绪", "emotion", "共鸣", "情感", "共情"],
        "viral": ["爆款", "viral", "裂变", "传播", "算法"],
        "platform": ["平台", "算法", "推荐", "流量"],
        "comment": ["评论", "互动", "运营", "社群"],
        "publishing": ["发布", "时机", "频率", "排期"],
    }

    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self._methodology_cache: list[dict] | None = None
        self._template_cache: list[dict] | None = None
        self._prompt_cache: list[dict] | None = None
        self._cache_hash: str | None = None
        self._last_refresh: str | None = None

    def _get_content_hash(self) -> str:
        """计算所有知识文件的内容哈希，用于缓存失效检测"""
        hasher = hashlib.md5()
        for md_file in sorted(METHODOLOGY_DIR.glob("*.md")):
            hasher.update(md_file.read_bytes())
        for tmpl_file in sorted(TEMPLATES_DIR.glob("*.md")):
            hasher.update(tmpl_file.read_bytes())
        for prompt_file in sorted(PROMPTS_DIR.glob("*.md")):
            hasher.update(prompt_file.read_bytes())
        return hasher.hexdigest()

    def _load_cached(self) -> bool:
        """尝试从磁盘加载缓存"""
        if not CACHE_FILE.exists():
            return False
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if data.get("hash") == self._get_content_hash():
                self._methodology_cache = data.get("methodology", [])
                self._template_cache = data.get("templates", [])
                self._prompt_cache = data.get("prompts", [])
                self._last_refresh = data.get("refreshed_at")
                logger.info(f"知识图谱缓存命中: {len(self._methodology_cache)} 方法论, {len(self._template_cache)} 模板")
                return True
        except Exception as e:
            logger.warning(f"知识图谱缓存加载失败: {e}")
        return False

    def _save_cache(self):
        """将解析结果缓存到磁盘"""
        if not self.cache_enabled:
            return
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "hash": self._cache_hash or self._get_content_hash(),
                "refreshed_at": self._last_refresh or datetime.now().isoformat(),
                "methodology": self._methodology_cache or [],
                "templates": self._template_cache or [],
                "prompts": self._prompt_cache or [],
            }
            CACHE_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            logger.info("知识图谱缓存已保存")
        except Exception as e:
            logger.warning(f"知识图谱缓存保存失败: {e}")

    def _parse_methodology_file(self, filepath: Path) -> dict:
        """解析单个方法论 Markdown 文件到结构化条目"""
        text = filepath.read_text(encoding="utf-8")
        filename = filepath.stem

        # 提取标题 (第一行 # 标题)
        title_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else filename

        # 提取描述 (引用块 > ...)
        desc_match = re.search(r"^>\s*(.+)", text, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else ""

        # 提取所有二级标题作为章节
        sections = re.findall(r"^##\s+(.+)", text, re.MULTILINE)

        # 提取关键词标签
        tags = []
        lower_text = text.lower()
        for tag_name, keywords in self.METHODOLOGY_TAGS.items():
            for kw in keywords:
                if kw.lower() in lower_text:
                    tags.append(tag_name)
                    break

        # 提取所有列表项作为知识点
        knowledge_points = re.findall(r"^- \*\*(.+?)\*\*(?::|：)(.+)", text)
        if not knowledge_points:
            knowledge_points = re.findall(r"^- (.+)", text, re.MULTILINE)

        # 提取表格
        tables = re.findall(r"^\|.+\|$", text, re.MULTILINE)

        entry = {
            "id": filename,
            "title": title,
            "description": description,
            "tags": list(set(tags)),
            "sections": sections,
            "knowledge_points": [kp[0] if isinstance(kp, tuple) else kp for kp in knowledge_points[:10]],
            "has_tables": len(tables) > 0,
            "source": str(filepath.relative_to(PROJECT_ROOT)),
            "text_preview": text[:500],
        }
        return entry

    def _parse_template_file(self, filepath: Path) -> dict:
        """解析单个模板 Markdown 文件到结构化条目"""
        text = filepath.read_text(encoding="utf-8")
        filename = filepath.stem

        # 提取平台名称 (文件名去掉 -template)
        platform = filename.replace("-template", "").replace("-", "")

        # 提取标题
        title_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else platform

        # 提取描述 (引用块)
        desc_match = re.search(r"^>\s*(.+)", text, re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else ""

        # 提取所有二级标题
        sections = re.findall(r"^##\s+(.+)", text, re.MULTILINE)

        # 提取钩子示例
        hooks = re.findall(r"\d+\.\s+\*\*(.+?)\*\*(?::|：)?(.+)", text)

        # 提取代码块中的结构模板
        code_blocks = re.findall(r"```(?:\w*)\n(.*?)```", text, re.DOTALL)

        entry = {
            "id": filename,
            "platform": platform,
            "title": title,
            "description": description,
            "sections": sections,
            "hooks": [h[0] if isinstance(h, tuple) else h for h in hooks[:10]],
            "structures": [cb.strip() for cb in code_blocks[:3]],
            "source": str(filepath.relative_to(PROJECT_ROOT)),
            "text_preview": text[:500],
        }
        return entry

    def _parse_prompt_file(self, filepath: Path) -> dict:
        """解析单个提示词文件"""
        text = filepath.read_text(encoding="utf-8")
        filename = filepath.stem

        title_match = re.search(r"^#\s+(.+)", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else filename

        # 提取所有二级标题作为 prompt 分类
        sections = re.findall(r"^##\s+(.+)", text, re.MULTILINE)

        return {
            "id": filename,
            "title": title,
            "sections": sections,
            "source": str(filepath.relative_to(PROJECT_ROOT)),
            "text_preview": text[:500],
        }

    def refresh(self, force: bool = False):
        """刷新知识图谱缓存"""
        if not force and self._methodology_cache is not None:
            return

        if self.cache_enabled and self._load_cached() and not force:
            return

        logger.info("正在解析知识文件...")

        # 解析方法论文件
        self._methodology_cache = []
        if METHODOLOGY_DIR.exists():
            for md_file in sorted(METHODOLOGY_DIR.glob("*.md")):
                try:
                    entry = self._parse_methodology_file(md_file)
                    self._methodology_cache.append(entry)
                except Exception as e:
                    logger.warning(f"解析方法论文件失败 {md_file.name}: {e}")

        # 解析模板文件
        self._template_cache = []
        if TEMPLATES_DIR.exists():
            for tmpl_file in sorted(TEMPLATES_DIR.glob("*.md")):
                try:
                    entry = self._parse_template_file(tmpl_file)
                    self._template_cache.append(entry)
                except Exception as e:
                    logger.warning(f"解析模板文件失败 {tmpl_file.name}: {e}")

        # 解析提示词文件
        self._prompt_cache = []
        if PROMPTS_DIR.exists():
            for prompt_file in sorted(PROMPTS_DIR.glob("*.md")):
                try:
                    entry = self._parse_prompt_file(prompt_file)
                    self._prompt_cache.append(entry)
                except Exception as e:
                    logger.warning(f"解析提示词文件失败 {prompt_file.name}: {e}")

        self._cache_hash = self._get_content_hash()
        self._last_refresh = datetime.now().isoformat()
        self._save_cache()

        logger.info(
            f"知识图谱加载完成: {len(self._methodology_cache)} 方法论, "
            f"{len(self._template_cache)} 模板, {len(self._prompt_cache)} 提示词"
        )

    def search(
        self,
        query: str,
        category: str | None = None,
        platform: str | None = None,
        max_results: int = 10,
    ) -> list[dict]:
        """搜索知识图谱

        Args:
            query: 搜索关键词
            category: 过滤类别 (methodology/template/prompt/all)
            platform: 按平台过滤 (仅对 template 有效)
            max_results: 最大返回数
        """
        self.refresh()
        query_lower = query.lower()
        results: list[dict] = []

        # 搜索方法论
        if category in (None, "all", "methodology"):
            for entry in self._methodology_cache or []:
                score = self._calc_relevance(entry, query_lower)
                if score > 0:
                    results.append({
                        "type": "methodology",
                        "score": score,
                        **entry,
                    })

        # 搜索模板
        if category in (None, "all", "template"):
            for entry in self._template_cache or []:
                if platform and entry.get("platform", "").lower() != platform.lower():
                    continue
                score = self._calc_relevance(entry, query_lower)
                if score > 0:
                    results.append({
                        "type": "template",
                        "score": score,
                        **entry,
                    })

        # 搜索提示词
        if category in (None, "all", "prompt"):
            for entry in self._prompt_cache or []:
                score = self._calc_relevance(entry, query_lower)
                if score > 0:
                    results.append({
                        "type": "prompt",
                        "score": score,
                        **entry,
                    })

        # 按相关度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    def _calc_relevance(self, entry: dict, query_lower: str) -> float:
        """计算条目与查询的相关度分数"""
        score = 0.0
        text = json.dumps(entry, ensure_ascii=False).lower()

        # 精确匹配加权
        if query_lower in text:
            score += 10.0

        # 分词匹配
        terms = re.findall(r"[\w一-鿿]+", query_lower)
        matched = sum(1 for t in terms if t in text)
        if terms:
            score += (matched / len(terms)) * 5.0

        # 标题匹配额外加分
        title = (entry.get("title") or "").lower()
        if query_lower in title:
            score += 5.0

        # 标签匹配加分
        tags = [t.lower() for t in entry.get("tags", [])]
        if any(t in query_lower for t in tags):
            score += 3.0

        return score

    def get_relevant_context(
        self,
        topic: str,
        platform: str | None = None,
        persona: str | None = None,
        max_sources: int = 3,
    ) -> str:
        """获取与主题相关的上下文文本，适合作为 Prompt 上下文插入

        Args:
            topic: 内容主题
            platform: 目标平台 (可选)
            persona: 创作人设 (可选)
            max_sources: 最大引用源数
        """
        self.refresh()

        # 搜索方法论
        methodology_results = self.search(topic, category="methodology", max_results=max_sources)
        template_results = self.search(topic, category="template", platform=platform, max_results=max_sources) if platform else []
        prompt_results = self.search(topic, category="prompt", max_results=1)

        context_parts: list[str] = []

        # 添加方法论上下文
        if methodology_results:
            context_parts.append("## 方法论参考")
            for i, entry in enumerate(methodology_results[:max_sources], 1):
                preview = entry.get("text_preview", "")[:300]
                context_parts.append(f"\n### {i}. {entry['title']}\n{preview}\n")

        # 添加模板上下文
        if template_results:
            context_parts.append("## 平台模板参考")
            for i, entry in enumerate(template_results[:max_sources], 1):
                platform_name = entry.get("platform", entry.get("title", ""))
                hooks = entry.get("hooks", [])
                structures = entry.get("structures", [])
                context_parts.append(f"\n### {i}. {platform_name}")
                if hooks:
                    context_parts.append(f"钩子示例: {', '.join(hooks[:5])}")
                if structures:
                    context_parts.append(f"内容结构:\n{structures[0]}")
                context_parts.append("")

        # 添加人设上下文
        if persona:
            persona_file = PROJECT_ROOT / "content" / "experts" / f"{persona}-persona.md"
            if persona_file.exists():
                context_parts.append("## 人设参考")
                context_parts.append(persona_file.read_text(encoding="utf-8")[:500])
                context_parts.append("")

        # 添加提示词参考
        if prompt_results:
            context_parts.append("## 提示词参考")
            for entry in prompt_results[:1]:
                preview = entry.get("text_preview", "")[:300]
                context_parts.append(f"\n{entry['title']}\n{preview}\n")

        return "\n".join(context_parts)

    def get_platform_knowledge(self, platform: str) -> dict:
        """获取指定平台的全部知识"""
        self.refresh()
        templates = [t for t in (self._template_cache or []) if platform.lower() in t.get("platform", "").lower()]
        return {
            "platform": platform,
            "templates": templates,
            "related_methodology": self._methodology_cache or [],
        }

    def get_all_categories(self) -> list[str]:
        """获取所有方法论分类标签"""
        self.refresh()
        tags = set()
        for entry in self._methodology_cache or []:
            tags.update(entry.get("tags", []))
        return sorted(tags)

    def get_knowledge_stats(self) -> dict:
        """获取知识图谱统计信息"""
        self.refresh()
        return {
            "methodology_count": len(self._methodology_cache or []),
            "template_count": len(self._template_cache or []),
            "prompt_count": len(self._prompt_cache or []),
            "categories": self.get_all_categories(),
            "last_refresh": self._last_refresh,
            "cache_enabled": self.cache_enabled,
        }


# 全局单例
knowledge_graph = KnowledgeGraph()
