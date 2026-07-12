"""浏览器采集模块测试

测试 BrowserPool 生命周期、PlatformBrowser 配置、数据清洗管道。
由于 Playwright 需要浏览器环境，核心逻辑通过 mock 测试。
"""

import pytest


# ================================================
# BrowserPool 测试
# ================================================

class TestBrowserPool:
    """BrowserPool 生命周期测试"""

    def test_browser_pool_init_defaults(self):
        """测试默认初始化参数"""
        from monitors.browser import BrowserPool
        pool = BrowserPool()
        assert pool._headless is True
        assert pool._max_contexts == 4
        assert pool._started is False
        assert pool._browser is None

    def test_browser_pool_init_custom(self):
        """测试自定义参数"""
        from monitors.browser import BrowserPool
        pool = BrowserPool(headless=False, max_contexts=2)
        assert pool._headless is False
        assert pool._max_contexts == 2

    def test_browser_pool_health(self):
        """测试健康状态报告"""
        from monitors.browser import BrowserPool
        pool = BrowserPool()
        health = pool.health()
        assert health["started"] is False
        assert "active_pages" in health
        assert "max_contexts" in health

    def test_browser_pool_record_error(self):
        """测试错误计数"""
        from monitors.browser import BrowserPool
        pool = BrowserPool()
        assert pool.health()["error_count"] == 0
        pool.record_error()
        assert pool.health()["error_count"] == 1


# ================================================
# PlatformBrowser 配置测试
# ================================================

class TestPlatformBrowser:
    """PlatformBrowser 配置测试"""

    def test_platform_configs_complete(self):
        """验证 13 个平台配置完整"""
        from monitors.browser import PlatformBrowser
        configs = PlatformBrowser.PLATFORM_CONFIGS

        expected = {
            "抖音", "小红书", "B站", "微博", "知乎", "头条", "快手",
            "YouTube", "TikTok", "公众号", "视频号", "百度热搜", "Instagram",
        }
        assert set(configs.keys()) == expected

    def test_platform_config_has_required_fields(self):
        """每个平台配置包含必要字段"""
        from monitors.browser import PlatformBrowser
        configs = PlatformBrowser.PLATFORM_CONFIGS

        for platform, config in configs.items():
            assert "hot_url" in config, f"{platform} 缺少 hot_url"
            assert "extract_method" in config, f"{platform} 缺少 extract_method"
            assert "category" in config, f"{platform} 缺少 category"
            assert isinstance(config["hot_url"], str)
            assert config["hot_url"].startswith("http")

    def test_get_supported_platforms(self):
        """测试获取平台列表"""
        from monitors.browser import PlatformBrowser, BrowserPool

        pool = BrowserPool()
        pb = PlatformBrowser(pool)
        platforms = pb.get_supported_platforms()
        assert len(platforms) == 13
        assert all("name" in p and "category" in p for p in platforms)

    def test_scrape_result_defaults(self):
        """测试 ScrapeResult 默认值"""
        from monitors.browser import ScrapeResult
        result = ScrapeResult(platform="测试")
        assert result.platform == "测试"
        assert result.success is False
        assert result.hot_items == []
        assert result.raw_titles == []


# ================================================
# ScrapeResult 测试
# ================================================

class TestScrapeResult:
    """ScrapeResult 数据类测试"""

    def test_successful_result(self):
        """测试成功结果"""
        from monitors.browser import ScrapeResult
        result = ScrapeResult(
            platform="B站",
            hot_items=[{"title": "测试视频"}],
            raw_titles=["测试视频"],
            topics=["测试"],
            collected_at="2026-07-04T00:00:00Z",
            source_url="https://www.bilibili.com/v/popular/rank/all",
            success=True,
        )
        assert result.success is True
        assert len(result.hot_items) == 1
        assert len(result.raw_titles) == 1
        assert result.error == ""

    def test_failed_result(self):
        """测试失败结果"""
        from monitors.browser import ScrapeResult
        result = ScrapeResult(
            platform="抖音",
            success=False,
            error="页面加载超时",
        )
        assert result.success is False
        assert result.error == "页面加载超时"


# ================================================
# 数字解析工具测试
# ================================================

class TestParseNumbers:
    """热度数字解析测试"""

    def test_parse_heat_wan(self):
        from monitors.browser import PlatformBrowser
        assert PlatformBrowser._parse_heat("1234.5万") == 12345000
        assert PlatformBrowser._parse_heat("1.2万") == 12000

    def test_parse_heat_yi(self):
        from monitors.browser import PlatformBrowser
        assert PlatformBrowser._parse_heat("1.5亿") == 150000000

    def test_parse_heat_plain(self):
        from monitors.browser import PlatformBrowser
        assert PlatformBrowser._parse_heat("12345") == 12345
        assert PlatformBrowser._parse_heat("0") == 0

    def test_parse_heat_invalid(self):
        from monitors.browser import PlatformBrowser
        assert PlatformBrowser._parse_heat("") == 0
        assert PlatformBrowser._parse_heat("abc") == 0

    def test_parse_count(self):
        from monitors.browser import PlatformBrowser
        assert PlatformBrowser._parse_count("3.4k播放") == 3400
        assert PlatformBrowser._parse_count("5.2万次观看") == 52000


# ================================================
# is_browser_enabled 测试
# ================================================

class TestBrowserEnabled:
    """浏览器启用状态测试"""

    def test_default_enabled(self):
        """默认启用（无环境变量时）"""
        import os
        # 确保没有环境变量干扰
        old_val = os.environ.pop("BROWSER_SCRAPE_ENABLED", None)
        try:
            from monitors.browser import is_browser_enabled
            assert is_browser_enabled() is True
        finally:
            if old_val is not None:
                os.environ["BROWSER_SCRAPE_ENABLED"] = old_val

    def test_explicit_disabled(self):
        """显式禁用"""
        import os
        os.environ["BROWSER_SCRAPE_ENABLED"] = "false"
        try:
            from monitors.browser import is_browser_enabled
            assert is_browser_enabled() is False
        finally:
            os.environ.pop("BROWSER_SCRAPE_ENABLED", None)
