"""
智媒圈前端 E2E 测试 (Playwright)
运行: npx playwright test
"""

import pytest
from playwright.sync_api import Page, expect

# ========================================
# 配置
# ========================================

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"

# ========================================
# Fixtures
# ========================================

@pytest.fixture(scope="function")
def page(browser):
    """创建页面"""
    page = browser.new_page()
    yield page
    page.close()


# ========================================
# 首页测试
# ========================================

class TestHomePage:
    """首页测试"""

    def test_home_loads(self, page: Page):
        """测试首页加载"""
        page.goto(BASE_URL)
        # 等待页面加载
        page.wait_for_load_state("networkidle")
        # 检查标题
        expect(page).to_have_title(/智媒圈/)

    def test_navigation_visible(self, page: Page):
        """测试导航栏可见"""
        page.goto(BASE_URL)
        # 检查导航元素
        nav = page.locator("nav").first
        expect(nav).to_be_visible()


# ========================================
# 媒体管理页面测试
# ========================================

class TestMediaPage:
    """媒体管理页面测试"""

    def test_media_page_loads(self, page: Page):
        """测试媒体页面加载"""
        page.goto(f"{BASE_URL}/media")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("媒体资产")

    def test_upload_button_visible(self, page: Page):
        """测试上传按钮可见"""
        page.goto(f"{BASE_URL}/media")

        # 查找上传按钮
        upload_btn = page.get_by_role("button", name="上传")
        expect(upload_btn).to_be_visible()

    def test_search_functionality(self, page: Page):
        """测试搜索功能"""
        page.goto(f"{BASE_URL}/media")

        # 查找搜索框
        search_input = page.get_by_placeholder("搜索")
        expect(search_input).to_be_visible()

        # 输入搜索词
        search_input.fill("test")
        # 触发搜索
        page.keyboard.press("Enter")


# ========================================
# 评论页面测试
# ========================================

class TestCommentsPage:
    """评论页面测试"""

    def test_comments_page_loads(self, page: Page):
        """测试评论页面加载"""
        page.goto(f"{BASE_URL}/comments")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("协作评论")

    def test_comment_form_visible(self, page: Page):
        """测试评论表单可见"""
        page.goto(f"{BASE_URL}/comments")

        # 查找评论输入框
        textarea = page.locator("textarea").first
        expect(textarea).to_be_visible()

    def test_submit_comment(self, page: Page):
        """测试提交评论"""
        page.goto(f"{BASE_URL}/comments")

        # 输入评论
        textarea = page.locator("textarea").first
        textarea.fill("这是一条测试评论")

        # 点击提交
        submit_btn = page.get_by_role("button", name="提交")
        submit_btn.click()


# ========================================
# 标签页面测试
# ========================================

class TestTagsPage:
    """标签页面测试"""

    def test_tags_page_loads(self, page: Page):
        """测试标签页面加载"""
        page.goto(f"{BASE_URL}/tags")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("标签体系")

    def test_create_tag_button(self, page: Page):
        """测试创建标签按钮"""
        page.goto(f"{BASE_URL}/tags")

        # 查找创建按钮
        create_btn = page.get_by_role("button", name="创建标签")
        expect(create_btn).to_be_visible()


# ========================================
# 订阅页面测试
# ========================================

class TestSubscriptionPage:
    """订阅页面测试"""

    def test_subscription_page_loads(self, page: Page):
        """测试订阅页面加载"""
        page.goto(f"{BASE_URL}/subscription")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("订阅管理")

    def test_plans_displayed(self, page: Page):
        """测试计划显示"""
        page.goto(f"{BASE_URL}/subscription")

        # 检查计划卡片
        cards = page.locator('[class*="Card"]').all()
        assert len(cards) >= 4  # 至少 4 个计划

    def test_upgrade_button_visible(self, page: Page):
        """测试升级按钮可见"""
        page.goto(f"{BASE_URL}/subscription")

        # 查找升级按钮
        upgrade_btn = page.get_by_role("button", name="升级")
        expect(upgrade_btn.first).to_be_visible()


# ========================================
# 渠道页面测试
# ========================================

class TestChannelsPage:
    """渠道页面测试"""

    def test_channels_page_loads(self, page: Page):
        """测试渠道页面加载"""
        page.goto(f"{BASE_URL}/channels")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("分发渠道")

    def test_add_channel_button(self, page: Page):
        """测试添加渠道按钮"""
        page.goto(f"{BASE_URL}/channels")

        # 查找添加按钮
        add_btn = page.get_by_role("button", name="添加渠道")
        expect(add_btn).to_be_visible()


# ========================================
# 热点页面测试
# ========================================

class TestTrendsPage:
    """热点页面测试"""

    def test_trends_page_loads(self, page: Page):
        """测试热点页面加载"""
        page.goto(f"{BASE_URL}/trends")
        page.wait_for_load_state("networkidle")

        # 检查页面标题
        title = page.locator("h1").first
        expect(title).to_contain_text("热点追踪")

    def test_scan_button_visible(self, page: Page):
        """测试扫描按钮可见"""
        page.goto(f"{BASE_URL}/trends")

        # 查找扫描按钮
        scan_btn = page.get_by_role("button", name="扫描热点")
        expect(scan_btn).to_be_visible()

    def test_platform_filters(self, page: Page):
        """测试平台筛选"""
        page.goto(f"{BASE_URL}/trends")

        # 检查平台筛选按钮
        buttons = page.get_by_role("button").all()
        platforms = ["抖音", "小红书", "B站"]

        for platform in platforms:
            btn = page.get_by_role("button", name=platform)
            expect(btn.first).to_be_visible()


# ========================================
# API 端点测试
# ========================================

class TestAPIEndpoints:
    """API 端点测试"""

    def test_health_endpoint(self, page: Page):
        """测试健康检查端点"""
        # 使用 page 请求 API
        response = page.request.get(f"{API_URL}/health")
        assert response.ok

    def test_media_api(self, page: Page):
        """测试媒体 API"""
        response = page.request.get(f"{API_URL}/api/v1/media/list")
        # 可能返回 401（未认证）或 200
        assert response.status in [200, 401]

    def test_trends_api(self, page: Page):
        """测试热点 API"""
        response = page.request.get(f"{API_URL}/api/v1/trends/")
        assert response.status in [200, 401]


# ========================================
# 响应式测试
# ========================================

class TestResponsive:
    """响应式测试"""

    @pytest.mark.parametrize("viewport", [
        {"width": 1920, "height": 1080},  # 桌面
        {"width": 1366, "height": 768},   # 笔记本
        {"width": 768, "height": 1024},   # 平板
        {"width": 375, "height": 667},    # 手机
    ])
    def test_responsive_layout(self, page: Page, viewport):
        """测试响应式布局"""
        page.set_viewport_size(viewport)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # 检查页面可见
        expect(page).to_be_visible()


# ========================================
# 性能测试
# ========================================

class TestPerformance:
    """性能测试"""

    def test_page_load_time(self, page: Page):
        """测试页面加载时间"""
        import time
        start = time.time()

        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        load_time = time.time() - start

        # 加载时间应小于 5 秒
        assert load_time < 5.0, f"页面加载时间过长: {load_time:.2f}s"

    def test_api_response_time(self, page: Page):
        """测试 API 响应时间"""
        import time
        start = time.time()

        response = page.request.get(f"{API_URL}/health")

        response_time = time.time() - start

        # 响应时间应小于 1 秒
        assert response_time < 1.0, f"API 响应时间过长: {response_time:.2f}s"
        assert response.ok