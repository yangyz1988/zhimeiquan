"""性能优化工具测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.performance import (
    PaginationOptimizer,
    ImageOptimizer,
    LazyLoader,
)


class TestPagination:
    """分页测试"""

    def test_offset_calculation(self):
        """测试偏移量计算"""
        assert PaginationOptimizer.calculate_offset(1, 20) == 0
        assert PaginationOptimizer.calculate_offset(2, 20) == 20
        assert PaginationOptimizer.calculate_offset(3, 10) == 20

    def test_page_size_validation(self):
        """测试页面大小验证"""
        assert PaginationOptimizer.validate_page_size(0) == 20
        assert PaginationOptimizer.validate_page_size(50) == 50
        assert PaginationOptimizer.validate_page_size(200) == 100

    def test_pagination_response(self):
        """测试分页响应构建"""
        items = [{"id": i} for i in range(5)]
        result = PaginationOptimizer.build_pagination_response(
            items=items,
            total=100,
            page=1,
            page_size=20
        )

        assert result["items"] == items
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total"] == 100
        assert result["pagination"]["total_pages"] == 5
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False


class TestImageOptimization:
    """图片优化测试"""

    def test_responsive_srcset(self):
        """测试响应式 srcset"""
        srcset = ImageOptimizer.get_responsive_srcset(
            "https://example.com/image.jpg",
            sizes=[320, 640, 1024]
        )

        assert "320w" in srcset
        assert "640w" in srcset
        assert "1024w" in srcset
        assert srcset.count(",") == 2  # 三个尺寸，两个逗号

    def test_optimized_url(self):
        """测试优化 URL"""
        url = ImageOptimizer.get_optimized_url(
            "https://example.com/image.jpg",
            width=800,
            quality=75,
            format="webp"
        )

        assert "w=800" in url
        assert "q=75" in url
        assert "f=webp" in url


class TestLazyLoading:
    """懒加载测试"""

    def test_lazy_attributes(self):
        """测试懒加载属性"""
        attrs = LazyLoader.get_lazy_attributes(
            threshold="200px",
            placeholder="data:image/gif;base64,..."
        )

        assert attrs["loading"] == "lazy"
        assert attrs["data-threshold"] == "200px"
        assert "src" in attrs

    def test_intersection_observer_script(self):
        """测试 Intersection Observer 脚本"""
        script = LazyLoader.get_intersection_observer_script()

        assert "IntersectionObserver" in script
        assert "lazy" in script


if __name__ == "__main__":
    pytest.main([__file__, "-v"])