"""浏览器自动化采集 - 通过 Playwright 获取各平台真实热门数据
提供 BrowserPool (浏览器实例池管理) 和 PlatformBrowser (平台级页面交互)，
支持 13 个主流平台的热搜/热门内容采集。
典型用法:
    pool = await get_browser_pool()       # 全局单例
    pb = PlatformBrowser(pool)
    result = await pb.scrape_platform("B站")
    # result.hot_items   → 热搜列表
    # result.topics      → 提取的热门话题
    
"""
import asyncio
import json
import os
import random
import re
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from services.logging import logger
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    
except ImportError as e:
    logger.warning(f"playwright 未安装，浏览器采集功能不可用: {e}")
    async_playwright = None  # type: ignore
    
# -------------------------------------------------------
# ScrapeResult — 统一采集结果
# -------------------------------------------------------
@dataclass
class ScrapeResult:
    """单次采集结果"""
    platform: str
    hot_items: list[dict] = field(default_factory=list)  # 热搜/热门内容列表
    raw_titles: list[str] = field(default_factory=list)  # 去重后的标题文本
    topics: list[str] = field(default_factory=list)       # 提取的热门话题
    collected_at: str = ""                                # ISO 时间
    source_url: str = ""                                  # 来源 URL
    success: bool = False
    error: str = ""

# -------------------------------------------------------
# 反检测脚本
# -------------------------------------------------------
_STEALTH_SCRIPT = """
// 隐藏 webdriver 标记
Object.defineProperty(navigator, 'webdriver', { get: () => false });
// 覆盖 chrome 对象
window.chrome = { runtime: {} };
// 覆盖 permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
    
);
// 覆盖 plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
    
});
// 覆盖 language
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en'],
    
});
"""
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    
]
# -------------------------------------------------------
# BrowserPool
# -------------------------------------------------------
class BrowserPool:
    """Playwright 浏览器实例池 - 单例模式管理浏览器实例和多个无头上下文."""
    BROWSER_ARGS = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--window-size=1920,1080",
        
    ]
    def __init__(self, headless: bool = True, max_contexts: int = 4):
        self._headless = headless
        self._max_contexts = max_contexts
        self._browser: Browser | None = None
        self._playwright: Any = None
        self._semaphore = asyncio.Semaphore(max_contexts)
        self._page_count = 0
        self._error_count = 0
        self._started = False
        self._active = True
        
    async def start(self):
        """启动浏览器实例。应用启动时调用一次。"""
        if self._started:
            return

        if async_playwright is None:
            raise RuntimeError("playwright 未安装，无法启动浏览器")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=self.BROWSER_ARGS,

        )
        self._started = True
        self._active = True
        logger.info("BrowserPool 已启动", headless=self._headless, max_contexts=self._max_contexts)

    async def stop(self):
        """关闭浏览器实例。应用关闭时调用。"""
        self._active = False
        if self._browser:
            await self._browser.close()

        if self._playwright:
            await self._playwright.stop()

        # 强制清理残留的 Chromium 子进程
        self._kill_orphaned_processes()

        self._started = False
        logger.info("BrowserPool 已停止")

    async def __aenter__(self):
        """支持 async with 语法。"""
        await self.start()
        return self

    async def __aexit__(self, *args):
        """async with 退出时自动关闭浏览器。"""
        await self.stop()
        return False

    def _kill_orphaned_processes(self):
        """清理残留的 Chromium/Playwright 子进程。"""
        try:
            import platform
            system = platform.system()
            if system == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "chromium.exe"],
                    capture_output=True, timeout=5,
                )
            elif system == "Darwin":
                subprocess.run(
                    ["pkill", "-f", "chromium"],
                    capture_output=True, timeout=5,
                )
            else:
                subprocess.run(
                    ["pkill", "-f", "chromium"],
                    capture_output=True, timeout=5,
                )
            logger.info("已清理残留 Chromium 进程")
        except Exception as e:
            logger.warning(f"清理残留进程失败: {e}")

    async def new_context(self) -> BrowserContext:
        """创建一个新的浏览器上下文（带 stealth 伪装 + 随机 user-agent）。"""
        if not self._started or not self._browser:
            raise RuntimeError("BrowserPool 未启动")

        user_agent = random.choice(_USER_AGENTS)
        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent,
            locale="zh-CN",

        )
        await context.add_init_script(_STEALTH_SCRIPT)
        return context

    async def new_page(self, context: BrowserContext | None = None) -> Page:
        """获取一个新页面（带反检测脚本注入）。
        返回的 page 应在使用完毕后调用 page.close() + context.close()。
        """
        if context is None:
            context = await self.new_context()

        page = await context.new_page()
        page.set_default_timeout(30000)
        self._page_count += 1
        return page

    async def acquire_page(self) -> "PageContext":
        """获取受信号量控制的页面上下文。推荐用法:
        async with pool.acquire_page() as page:
            await page.goto(...)
            content = await page.content()
            
        """
        return PageContext(self)

    def health(self) -> dict:
        return {
            "started": self._started,
            "active_pages": self._page_count,
            "max_contexts": self._max_contexts,
            "error_count": self._error_count,
            "headless": self._headless,

        }

    def record_error(self):
        self._error_count += 1

class PageContext:
    """页面上下文管理器，自动管理 context 和 page 的生命周期。"""
    def __init__(self, pool: BrowserPool):
        self._pool = pool
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def __aenter__(self) -> Page:
        await self._pool._semaphore.acquire()
        try:
            self._context = await self._pool.new_context()
            self._page = await self._pool.new_page(context=self._context)
            return self._page

        except Exception:
            await self._pool._semaphore.release()
            raise

    async def __aexit__(self, *args):
        try:
            if self._context:
                await self._context.close()

        finally:
            await self._pool._semaphore.release()

# -------------------------------------------------------
# PlatformBrowser — 平台级采集器
# -------------------------------------------------------
class PlatformBrowser:
    """平台级浏览器采集器。
    每个平台有独立的配置:
    - hot_url: 热搜/发现页面 URL
    - wait_selector: 页面加载完成的标志
    - scroll: 是否需要滚动加载更多
    - extract_method: 提取方法名 (指 _extract_xxx)
    """
    PLATFORM_CONFIGS: dict[str, dict[str, Any]] = {
        "抖音": {
            "hot_url": "https://www.douyin.com/hot",
            "wait_selector": '[data-e2e="hot-list"] li',
            "scroll": True,
            "scroll_times": 3,
            "extract_method": "_extract_douyin",
            "category": "短视频",

        },
        "小红书": {
            "hot_url": "https://www.xiaohongshu.com/explore",
            "wait_selector": ".note-item",
            "scroll": True,
            "scroll_times": 5,
            "extract_method": "_extract_from_ssr_or_dom",
            "ssr_key": "__INITIAL_STATE__",
            "category": "种草",

        },
        "B站": {
            "hot_url": "https://www.bilibili.com/v/popular/rank/all",
            "wait_selector": ".video-card",
            "scroll": True,
            "scroll_times": 3,
            "extract_method": "_extract_bilibili",
            "category": "中长视频",

        },
        "微博": {
            "hot_url": "https://weibo.com/ajax/side/hotSearch",
            "wait_selector": "pre",  # JSON 裸响应
            "scroll": False,
            "is_api": True,
            "extract_method": "_extract_weibo",
            "category": "社交",

        },
        "知乎": {
            "hot_url": "https://www.zhihu.com/hot",
            "wait_selector": ".HotList-list .HotItem-content",
            "scroll": True,
            "scroll_times": 2,
            "extract_method": "_extract_zhihu",
            "category": "问答",

        },
        "头条": {
            "hot_url": "https://www.toutiao.com/",
            "wait_selector": ".feed-card-wrapper, .news-card",
            "scroll": True,
            "scroll_times": 4,
            "extract_method": "_extract_from_ssr_or_dom",
            "ssr_key": "__TOUTIAO_STATE__",
            "category": "资讯",

        },
        "快手": {
            "hot_url": "https://www.kuaishou.com/new-reco",
            "wait_selector": ".video-card, .video-item",
            "scroll": True,
            "scroll_times": 4,
            "extract_method": "_extract_from_ssr_or_dom",
            "ssr_key": "__APOLLO_STATE__",
            "category": "短视频",

        },
        "YouTube": {
            "hot_url": "https://www.youtube.com/feed/trending",
            "wait_selector": "ytd-video-renderer",
            "scroll": True,
            "scroll_times": 3,
            "extract_method": "_extract_youtube",
            "category": "中长视频",

        },
        "TikTok": {
            "hot_url": "https://www.tiktok.com/trending",
            "wait_selector": '[data-e2e="trending-item"], .tiktok-feed',
            "scroll": True,
            "scroll_times": 5,
            "extract_method": "_extract_tiktok",
            "category": "短视频",

        },
        "公众号": {
            "hot_url": "https://weixin.sogou.com/",
            "wait_selector": ".news-list, .news-item",
            "scroll": False,
            "extract_method": "_extract_weixin",
            "category": "图文",

        },
        "视频号": {
            "hot_url": "https://channels.weixin.qq.com/",
            "wait_selector": ".channel-item, .feed-item",
            "scroll": True,
            "scroll_times": 3,
            "extract_method": "_extract_generic",
            "category": "短视频",

        },
        "百度热搜": {
            "hot_url": "https://top.baidu.com/board?tab=realtime",
            "wait_selector": ".category-wrap_iQLoo, .hot-list",
            "scroll": False,
            "extract_method": "_extract_baidu",
            "category": "资讯",

        },
        "Instagram": {
            "hot_url": "https://www.instagram.com/explore/",
            "wait_selector": "article",
            "scroll": True,
            "scroll_times": 4,
            "extract_method": "_extract_from_ssr_or_dom",
            "ssr_key": "__INITIAL_STATE__",
            "category": "社交",

        },

    }
    def __init__(self, pool: BrowserPool):
        self._pool = pool

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def scrape_platform(self, platform: str) -> ScrapeResult:
        """采集单个平台的热门数据。
        流程：
        打开页面 → 等待关键元素 → 滚动加载 → 提取数据 → 解析 → 返回
        """
        config = self.PLATFORM_CONFIGS.get(platform)
        if not config:
            return ScrapeResult(
                platform=platform,
                success=False,
                error=f"不支持的平台: {platform}",

            )

        result = ScrapeResult(
            platform=platform,
            source_url=config["hot_url"],
            collected_at=datetime.now(timezone.utc).isoformat(),

        )
        try:
            async with self._pool.acquire_page() as page:
                # 1. 导航
                await self._navigate(page, config)
                # 2. 等待关键元素
                await self._wait_for_content(page, config)
                # 3. 滚动加载更多
                if config.get("scroll"):
                    await self._scroll_load(page, config.get("scroll_times", 3))

                # 4. 提取数据
                raw_data = await self._extract_data(page, platform, config)
                # 5. 解析
                from monitors.parser import HotContentParser
                parsed = HotContentParser.parse(platform, raw_data)
                result.hot_items = raw_data if isinstance(raw_data, list) else []
                result.raw_titles = parsed.get("titles", [])
                result.topics = parsed.get("topics", [])
                result.success = len(result.raw_titles) > 0
                logger.info(
                    f"Browser 采集 {platform} 完成",
                    titles=len(result.raw_titles),
                    topics=len(result.topics),

                )

        except Exception as e:
            self._pool.record_error()
            result.success = False
            result.error = str(e)
            logger.warning(f"Browser 采集 {platform} 失败: {e}")

        return result

    async def scrape_all(
        self, platforms: list[str] | None = None, concurrency: int = 3

    ) -> dict[str, ScrapeResult]:
        """并发采集多个平台，带信号量控制并发数。
        Args:
            platforms: 平台名称列表，默认全部 13 个
            concurrency: 最大并发数
            
        """
        targets = platforms or list(self.PLATFORM_CONFIGS.keys())
        semaphore = asyncio.Semaphore(concurrency)
        async def _scrape_one(p: str) -> ScrapeResult:
            async with semaphore:
                return await self.scrape_platform(p)

        tasks = [_scrape_one(p) for p in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: dict[str, ScrapeResult] = {}
        for p, r in zip(targets, results):
            if isinstance(r, Exception):
                out[p] = ScrapeResult(
                    platform=p, success=False, error=str(r),
                    collected_at=datetime.now(timezone.utc).isoformat(),

                )

            else:
                out[p] = r

        return out

    def get_supported_platforms(self) -> list[dict]:
        """获取所有支持的平台列表。"""
        return [
            {
                "name": name,
                "category": cfg.get("category", ""),
                "hot_url": cfg.get("hot_url", ""),

            }
            for name, cfg in self.PLATFORM_CONFIGS.items()

        ]

    # ------------------------------------------------------------------
    # 页面交互
    # ------------------------------------------------------------------
    async def _navigate(self, page: Page, config: dict):
        """导航到目标页面，带重试。"""
        url = config["hot_url"]
        if config.get("is_api"):
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return

        for attempt in range(3):
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                return

            except Exception:
                if attempt == 2:
                    raise

                await asyncio.sleep(1 + attempt)

    async def _wait_for_content(self, page: Page, config: dict):
        """等待关键元素出现。"""
        selector = config.get("wait_selector")
        if not selector:
            return

        if config.get("is_api"):
            # API 响应是裸 JSON，等 body 加载即可
            await page.wait_for_selector("body", timeout=15000)
            return

        try:
            await page.wait_for_selector(selector, timeout=15000)

        except Exception:
            pass  # 超时不致命，继续提取

        # 随机模拟人类行为
        await page.wait_for_timeout(random.randint(500, 2000))

    async def _scroll_load(self, page: Page, times: int):
        """模拟人类滚动行为加载更多内容。"""
        for _ in range(times):
            scroll_amount = random.randint(600, 1200)
            await page.evaluate(f"window.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }})")
            await page.wait_for_timeout(random.randint(800, 2500))

        # 滚回顶部
        await page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        await page.wait_for_timeout(500)

    # ------------------------------------------------------------------
    # 数据提取
    # ------------------------------------------------------------------
    async def _extract_data(self, page: Page, platform: str, config: dict) -> list[dict]:
        """根据平台配置调用对应的提取方法。"""
        method_name = config.get("extract_method", "_extract_generic")
        method = getattr(self, method_name, self._extract_generic)
        return await method(page, platform, config)

    async def _extract_from_ssr_or_dom(self, page: Page, platform: str, config: dict) -> list[dict]:
        """从页面 SSR 状态变量或 DOM 中提取数据。
        优先尝试 window.<ssr_key> 获取内嵌 JSON 数据，
        失败时回退到 DOM CSS 选择器提取。
        """
        items: list[dict] = []
        ssr_key = config.get("ssr_key")
        if ssr_key:
            try:
                ssr = await page.evaluate(f"""
                    () => {{
                        const state = window[{json.dumps(ssr_key)}];
                        return state ? JSON.stringify(state) : null;
                    
                    }}
                    
                """)
                if ssr:
                    state = json.loads(ssr)
                    titles = self._recurse_titles(state, max_depth=5)
                    for t in titles[:50]:
                        items.append({"title": t})
                    
                    if items:
                        return items
                    
            except Exception:
                pass
                    
        # 回退到 DOM 提取
        return await self._extract_generic(page, platform, config)
                    
    def _recurse_titles(self, obj: Any, depth: int = 0) -> list[str]:
        """递归搜索 SSR 状态对象中的标题字段。"""
        titles: list[str] = []
        if depth <= 0 or obj is None:
            return titles

        if isinstance(obj, str):
            # 需要是合理的标题长度
            cleaned = obj.strip()
            if 2 < len(cleaned) < 200 and not cleaned.startswith("http"):
                titles.append(cleaned)

        elif isinstance(obj, dict):
            for key, val in obj.items():
                if key in ("title", "word", "name", "caption", "desc", "description"):
                    if isinstance(val, str) and 2 < len(val) < 200:
                        titles.append(val.strip())

                titles.extend(self._recurse_titles(val, depth - 1))

        elif isinstance(obj, list):
            for item in obj[:30]:
                titles.extend(self._recurse_titles(item, depth - 1))

        return list(dict.fromkeys(titles))  # 保持顺序去重

    async def _extract_generic(self, page: Page, platform: str, config: dict) -> list[dict]:
        """通用 DOM 提取器 — 兜底用。
        尝试多种通用选择器来获取标题文本。
        """
        items: list[dict] = []
        # 尝试多个通用选择器组合
        generic_selectors = [
            "a[href] h3", "a[href] .title", "a[href] .content",
            "h3", ".title", ".card-title", ".item-title",
            "a .text", ".text-content", ".desc",
            "li a", ".list-item a",

        ]
        for selector in generic_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for el in elements[:50]:
                    try:
                        text = (await el.inner_text()).strip()
                        if text and text not in {i["title"] for i in items}:
                            items.append({"title": text})

                    except Exception:
                        continue

                if len(items) >= 10:
                    break

            except Exception:
                continue

        return items[:50]

    # ------------------------------------------------------------------
    # 平台专用提取器
    # ------------------------------------------------------------------
    async def _extract_douyin(self, page: Page, platform: str, config: dict) -> list[dict]:
        """抖音热搜提取。
        抖音热搜页结构：
        - SSR JSON: window.__INITIAL_STATE__ → hotList.data.word_list
        - DOM: [data-e2e="hot-list"] li → .title
        """
        # 优先 SSR 数据
        try:
            ssr = await page.evaluate("""
                () => {
                    const state = window.__INITIAL_STATE__;
                    return state ? JSON.stringify(state) : null;
                
                }
                
            """)
            if ssr:
                state = json.loads(ssr)
                word_list = (
                    state.get("hotList", {})
                    .get("data", {})
                    .get("wordList", [])
                
                )
                items = []
                seen = set()
                for w in word_list[:50]:
                    title = (w.get("word") or w.get("title") or "").strip()
                    if title and title not in seen:
                        seen.add(title)
                        items.append({
                            "title": title,
                            "heat": w.get("hotValue", w.get("hot_value", 0)),
                            "tag": str(w.get("wordType", w.get("label", ""))),
                            "category": w.get("groupName", ""),
                
                        })
                
                if items:
                    return items
                
        except Exception:
            pass
                
        # DOM 回退
        return await self._extract_generic(page, platform, config)
                
    async def _extract_bilibili(self, page: Page, platform: str, config: dict) -> list[dict]:
        """B站热门提取。
        页面结构：.video-list .video-card
        - .title → 标题
        - .play-count → 播放量
        - .pts → 综合得分
        """
        items = []
        try:
            cards = await page.query_selector_all(".video-card, .video-list .rank-item")
            for i, card in enumerate(cards[:50]):
                try:
                    title_el = await card.query_selector(".title, h3 a, .info a")
                    if not title_el:
                        continue
            
                    title = (await title_el.inner_text()).strip()
                    if not title:
                        continue
            
                    item = {"title": title, "rank": i + 1}
                    try:
                        play_el = await card.query_selector(".play-count, .view, .count")
                        if play_el:
                            item["heat"] = self._parse_count((await play_el.inner_text()).strip())
            
                    except Exception:
                        pass
            
                    items.append(item)
            
                except Exception:
                    continue
            
        except Exception:
            pass
            
        if not items:
            return await self._extract_generic(page, platform, config)
            
        return items
            
    async def _extract_weibo(self, page: Page, platform: str, config: dict) -> list[dict]:
        """微博热搜提取。
        微博 /ajax/side/hotSearch 返回 JSON:
        { data: { realtime: [ { note, num, category }, ... ] } }
        """
        items = []
        try:
            # 获取页面 body 中的 JSON 文本
            body_text = await page.evaluate("() => document.body.innerText")
            data = json.loads(body_text)
            realtime = data.get("data", {}).get("realtime", [])
            for item in realtime[:50]:
                note = (item.get("note") or item.get("word") or "").strip()
                if note:
                    items.append({
                        "title": note,
                        "heat": item.get("num", item.get("hot_value", 0)),
                        "tag": item.get("category", ""),
            
                    })
            
        except (json.JSONDecodeError, Exception):
            pass
            
        if not items:
            return await self._extract_generic(page, platform, config)
            
        return items
            
    async def _extract_zhihu(self, page: Page, platform: str, config: dict) -> list[dict]:
        """知乎热榜提取。
        知乎热榜结构：
        .HotList-list .HotItem-content
        - .HotItem-title → 标题
        - .HotItem-metrics → 热度
        """
        items = []
        try:
            cards = await page.query_selector_all(".HotList-list .HotItem-content, .HotItem")
            for i, card in enumerate(cards[:50]):
                try:
                    title_el = await card.query_selector(".HotItem-title, h2, .title, a")
                    if not title_el:
                        continue
            
                    title = (await title_el.inner_text()).strip()
                    if not title:
                        continue
            
                    item = {"title": title, "rank": i + 1}
                    try:
                        metrics_el = await card.query_selector(".HotItem-metrics, .metrics")
                        if metrics_el:
                            metric_text = (await metrics_el.inner_text()).strip()
                            item["heat"] = self._parse_heat(metric_text)
            
                    except Exception:
                        pass
            
                    items.append(item)
            
                except Exception:
                    continue
            
        except Exception:
            pass
            
        if not items:
            return await self._extract_generic(page, platform, config)
            
        return items
            
    async def _extract_youtube(self, page: Page, platform: str, config: dict) -> list[dict]:
        """YouTube Trending 提取。
        页面结构：ytd-video-renderer
        - #video-title → 标题
        - #metadata-line → 播放量/时长
        """
        items = []
        try:
            renders = await page.query_selector_all("ytd-video-renderer")
            for i, render in enumerate(renders[:50]):
                try:
                    title_el = await render.query_selector("#video-title")
                    if not title_el:
                        continue
            
                    title = (await title_el.inner_text()).strip()
                    if not title:
                        continue
            
                    item = {"title": title, "rank": i + 1}
                    try:
                        meta_el = await render.query_selector("#metadata-line")
                        if meta_el:
                            meta_text = (await meta_el.inner_text()).strip()
                            item["heat"] = self._parse_count(meta_text)
            
                    except Exception:
                        pass
            
                    items.append(item)
            
                except Exception:
                    continue
            
        except Exception:
            pass
            
        if not items:
            return await self._extract_generic(page, platform, config)
            
        return items
            
    async def _extract_tiktok(self, page: Page, platform: str, config: dict) -> list[dict]:
        """TikTok Trending 提取。反爬较强，尝试多种策略。"""
        items = []
        # 尝试 SSR
        try:
            ssr = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    for (const s of scripts) {
                        try {
                            const d = JSON.parse(s.textContent);
                            if (d && d.props && d.props.pageProps) return JSON.stringify(d);
                
                        } catch {}
                
                    }
                    return null;
                
                }
                
            """)
            if ssr:
                titles = self._recurse_titles(json.loads(ssr))
                for t in titles[:30]:
                    items.append({"title": t})
                
            if items:
                return items
                
        except Exception:
            pass
                
        # DOM fallback
        return await self._extract_generic(page, platform, config)
                
    async def _extract_weixin(self, page: Page, platform: str, config: dict) -> list[dict]:
        """公众号热文提取（搜狗微信搜索）。"""
        return await self._extract_generic(page, platform, config)

    async def _extract_baidu(self, page: Page, platform: str, config: dict) -> list[dict]:
        """百度热搜提取。
        百度热搜页结构：
        .category-wrap_iQLoo .title_dIF3B / .content_1YWBm
        """
        items = []
        try:
            items_els = await page.query_selector_all(".category-wrap_iQLoo li, .hot-list [data-index]")
            for i, el in enumerate(items_els[:50]):
                try:
                    title_el = await el.query_selector(".title_dIF3B, .content_1YWBm, .c-single-text-ellipsis, a .text")
                    if not title_el:
                        title_el = await el.query_selector("a")

                    if not title_el:
                        continue

                    title = (await title_el.inner_text()).strip()
                    if title:
                        items.append({"title": title, "rank": i + 1})

                except Exception:
                    continue

        except Exception:
            pass

        if not items:
            return await self._extract_generic(page, platform, config)

        return items

    # ------------------------------------------------------------------
    # 数字解析工具
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_heat(text: str) -> int:
        """解析热度文本：'1234.5万 热度' → 12345000"""
        match = re.search(r"([\d.]+)\s*(万|亿)?", str(text).replace(",", ""))
        if not match:
            return 0

        num = float(match.group(1))
        unit = match.group(2)
        if unit == "万":
            num *= 10000

        elif unit == "亿":
            num *= 100_000_000

        return int(num)

    @staticmethod
    def _parse_count(text: str) -> int:
        """解析计数文本：'1.2万播放' → 12000"""
        return PlatformBrowser._parse_heat(text)

# -------------------------------------------------------
# 全局单例
# -------------------------------------------------------
_browser_pool: BrowserPool | None = None
async def get_browser_pool(
    headless: bool | None = None, max_contexts: int | None = None

) -> BrowserPool:
    """获取全局浏览器池（懒初始化单例）。
    首次调用时根据环境变量创建：
    - BROWSER_HEADLESS: 是否为无头模式（默认 true）
    - BROWSER_MAX_CONTEXTS: 最大并发上下文数（默认 4）
    """
    global _browser_pool
    if _browser_pool is None:
        headless = headless if headless is not None else (
            os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

        )
        max_contexts = max_contexts or int(os.getenv("BROWSER_MAX_CONTEXTS", "4"))
        _browser_pool = BrowserPool(headless=headless, max_contexts=max_contexts)
        await _browser_pool.start()

    return _browser_pool

def is_browser_enabled() -> bool:
    """检查浏览器采集是否启用。"""
    return os.getenv("BROWSER_SCRAPE_ENABLED", "true").lower() == "true"
