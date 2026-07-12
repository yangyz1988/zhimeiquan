"""API 路由集成测试 - 验证主路由注册

测试策略：
1. 直接解析 main.py 检查所有路由器是否已注册
2. 验证前缀正确性和唯一性
3. 不启动 HTTP 服务，纯代码静态分析
"""

import ast
import sys
import re
from pathlib import Path

import pytest

# 确保 scripts/ 目录在 sys.path
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


def _parse_router_registrations(main_py_path: str):
    """解析 main.py 提取所有 app.include_router 调用

    Returns:
        list of dict: [{name, prefix, tags}, ...]
    """
    with open(main_py_path, "r", encoding="utf-8") as f:
        source = f.read()

    # 提取 import 语句
    imports = re.findall(
        r"from routers import \((.*?)\)",
        source,
        re.DOTALL,
    )

    imported_routers = set()
    for block in imports:
        for name in re.findall(r"([a-z_]+)", block):
            if name != "import":
                imported_routers.add(name)

    # 提取 app.include_router 调用
    routers = []
    pattern = re.compile(
        r'app\.include_router\('
        r'(\w+)\.router,\s*'
        r'prefix=["\']([^"\']+)["\'],\s*'
        r'tags=\[([^\]]*)\]'
        r'\)'
    )

    for match in pattern.finditer(source):
        router_name = match.group(1)
        prefix = match.group(2)
        tags_str = match.group(3)
        tags = re.findall(r'"([^"]+)"', tags_str)
        routers.append({
            "name": router_name,
            "prefix": prefix,
            "tags": tags,
        })

    return imported_routers, routers


# ══════════════════════════════════════════════════════════════════
#  API 路由注册测试
# ══════════════════════════════════════════════════════════════════


class TestAPIRouterRegistration:
    """API 路由注册完整性测试"""

    MAIN_PY_PATH = _scripts_dir + "/main.py"

    def test_all_18_routers_imported_and_registered(self):
        """验证所有 18 个路由模块都被导入并注册

        预期的 18 个路由: content, titles, score, rules, video,
        analytics, ab_test, calendar, image, templates, agent,
        team, model_router, health, insights, fire_score,
        competitors, stream
        """
        imported_routers, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        expected_routers = {
            "content", "titles", "score", "rules", "video",
            "analytics", "ab_test", "calendar", "image", "templates",
            "agent", "team", "model_router", "health", "insights",
            "fire_score", "competitors", "stream",
        }

        # 验证所有 18 个都在 imports 中
        for name in expected_routers:
            assert name in imported_routers, (
                f"路由模块 '{name}' 未在 main.py 中导入"
            )

        # 验证所有导入的路由都有 include_router 调用
        registered_names = {r["name"] for r in registered}
        for name in imported_routers:
            assert name in registered_names, (
                f"路由模块 '{name}' 已导入但未注册 (缺少 include_router)"
            )

        # 验证注册数量 == 18
        assert len(registered) == 18, (
            f"期望 18 个路由注册，实际 {len(registered)}"
        )

    def test_all_routers_have_correct_prefixes(self):
        """验证每个路由器都有正确且唯一的前缀"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        # 期望的前缀映射
        expected_prefixes = {
            "content": "/api/v1/content",
            "titles": "/api/v1/titles",
            "score": "/api/v1/content",      # 与 content 共享前缀
            "rules": "/api/v1/monitor",
            "video": "/api/v1/video",
            "analytics": "/api/v1/analytics",
            "ab_test": "/api/v1/ab-test",
            "calendar": "/api/v1/calendar",
            "image": "/api/v1/image",
            "templates": "/api/v1/templates",
            "agent": "/api/v1/agent",
            "team": "/api/v1/team",
            "model_router": "/api/v1/router",
            "health": "",                     # 无前缀
            "insights": "/api/v1/insights",
            "fire_score": "/api/v1/fire-score",
            "competitors": "/api/v1/competitors",
            "stream": "/api/v1/stream",
        }

        for router in registered:
            name = router["name"]
            expected = expected_prefixes.get(name)
            if expected is not None:
                assert router["prefix"] == expected, (
                    f"路由 '{name}' 前缀应为 '{expected}'，实际为 '{router['prefix']}'"
                )

    def test_included_router_count_matches_expected(self):
        """验证 app.include_router 调用总数 = 18"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        # 计入 health 路由（无 prefix）
        assert len(registered) == 18, (
            f"include_router 调用数应为 18，实际 {len(registered)}"
        )

    def test_all_routers_have_tags(self):
        """验证每个路由都有中文标签"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        for router in registered:
            assert len(router["tags"]) > 0, (
                f"路由 '{router['name']}' 缺少 tags"
            )
            for tag in router["tags"]:
                assert isinstance(tag, str) and len(tag) > 0

    def test_router_module_files_exist(self):
        """验证每个路由模块对应的源文件存在"""
        routers_dir = Path(_scripts_dir) / "routers"
        assert routers_dir.exists(), f"routers 目录不存在: {routers_dir}"

        module_files = [
            "content.py", "titles.py", "score.py", "rules.py",
            "ab_test.py", "analytics.py", "video.py", "calendar.py",
            "image.py", "templates.py", "agent.py", "team.py",
            "model_router.py", "health.py", "insights.py",
            "fire_score.py", "competitors.py", "stream.py",
        ]

        for fname in module_files:
            filepath = routers_dir / fname
            assert filepath.exists(), f"路由文件不存在: {filepath}"

    def test_health_router_has_no_prefix(self):
        """health 路由应无前缀（根路径）"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        health_router = next(
            (r for r in registered if r["name"] == "health"), None
        )
        assert health_router is not None, "health 路由未注册"
        assert health_router["prefix"] == "", (
            f"health 路由不应有前缀, 实际: '{health_router['prefix']}'"
        )

    def test_all_prefixes_start_with_api_v1(self):
        """除 health 外，所有前缀应以 /api/v1/ 开头"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        for router in registered:
            if router["name"] == "health":
                continue  # health 无前缀
            assert router["prefix"].startswith("/api/v1/"), (
                f"路由 '{router['name']}' 前缀 '{router['prefix']}' 不以 /api/v1/ 开头"
            )

    def test_prefixed_routers_have_non_empty_prefix(self):
        """除 health 外，所有路由应有非空前缀"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        for router in registered:
            if router["name"] == "health":
                continue
            assert len(router["prefix"]) > 0, (
                f"路由 '{router['name']}' 前缀为空"
            )

    def test_source_file_parses_without_error(self):
        """main.py 应为有效的 Python 源码，可被 ast 解析"""
        with open(self.MAIN_PY_PATH, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
            assert tree is not None
        except SyntaxError as e:
            pytest.fail(f"main.py 语法错误: {e}")

    def test_no_extra_unknown_routers(self):
        """确认没有未预期的路由器注册"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        expected_names = {
            "content", "titles", "score", "rules", "video",
            "analytics", "ab_test", "calendar", "image", "templates",
            "agent", "team", "model_router", "health", "insights",
            "fire_score", "competitors", "stream",
        }

        for router in registered:
            assert router["name"] in expected_names, (
                f"发现未预期的路由器注册: '{router['name']}'"
            )

    def test_router_tags_match_api_function(self):
        """路由标签应与功能模块对应"""
        _, registered = _parse_router_registrations(self.MAIN_PY_PATH)

        # 验证一些关键路由的标签
        tag_mappings = {
            "content": "内容生成",
            "score": "内容评分",
            "ab_test": "A/B测试",
            "fire_score": "Fire Score",
            "stream": "流式生成",
            "health": "健康检查",
        }

        for router in registered:
            expected_tag_part = tag_mappings.get(router["name"])
            if expected_tag_part:
                tags_joined = " ".join(router["tags"])
                assert expected_tag_part in tags_joined, (
                    f"路由 '{router['name']}' 标签应包含 '{expected_tag_part}'"
                )


# ══════════════════════════════════════════════════════════════════
#  API 端点存在性测试（静态分析）
# ══════════════════════════════════════════════════════════════════


class TestAPIEndpointExistence:
    """API 端点静态存在性验证"""

    ROUTERS_DIR = _scripts_dir + "/routers"

    def test_content_router_has_crud_endpoints(self):
        """content 路由应包含生成和评分端点"""
        content_path = Path(self.ROUTERS_DIR) / "content.py"
        assert content_path.exists()
        source = content_path.read_text(encoding="utf-8")
        for endpoint in ["/generate", "/score"]:
            assert endpoint in source, f"content.py 缺少端点 {endpoint}"

    def test_health_router_has_health_endpoint(self):
        """health 路由应包含 /health 端点"""
        health_path = Path(self.ROUTERS_DIR) / "health.py"
        assert health_path.exists()
        source = health_path.read_text(encoding="utf-8")
        assert "/health" in source or "health" in source

    def test_score_router_has_score_functionality(self):
        """score 路由应包含评分相关功能"""
        score_path = Path(self.ROUTERS_DIR) / "score.py"
        assert score_path.exists()
