"""环境变量校验模块 - 启动时集中校验所有必需环境变量

分类:
- required: 缺少时服务无法启动（valid=False）
- optional: 缺少时功能降级但服务仍可运行
- playwright: Playwright/浏览器采集相关依赖检查

返回:
    {
        "valid": bool,         # True = 所有 required 变量已配置
        "missing": [...],      # 缺失的 required 变量名
        "warnings": [...],     # 缺失的 optional 变量名（功能降级）
        "playwright_ready": bool,  # Playwright 依赖是否就绪
        "summary": str,        # 人类可读的摘要
    }
"""

import os
import sys
from typing import Any


# ====== 变量分类定义 ======


REQUIRED_VARS = [
    "DEEPSEEK_API_KEY",
]

OPTIONAL_VARS = [
    "QWEN_API_KEY",
    "ERNIE_API_KEY",
    "HUNYUAN_API_KEY",
    "SILICONFLOW_API_KEY",
]

# 生产环境额外要求
PRODUCTION_VARS = [
    "POSTGRES_PASSWORD",
    "API_SECRET",
    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
    "CLERK_SECRET_KEY",
]

# 配置类变量（有默认值，通常不缺失，但校验值有效性）
CONFIG_VARS = {
    "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
    "REDIS_URL": "redis://localhost:6379",
    "FRONTEND_URL": "https://www.zhimeiquan.com",
    "LOG_LEVEL": "info",
    "LOG_FORMAT": "json",
}

# Playwright / 浏览器采集所需环境变量
PLAYWRIGHT_VARS = [
    "BROWSER_SCRAPE_ENABLED",
    "BROWSER_HEADLESS",
    "BROWSER_MAX_CONTEXTS",
]


def _is_set(value: str | None) -> bool:
    """判断环境变量是否被有效设置了值（排除空字符串和占位符）"""
    if value is None:
        return False
    stripped = value.strip()
    if not stripped:
        return False
    # 排除常见的占位符值
    placeholders = (
        "sk-your-key-here",
        "your-key-here",
        "your-secret-key",
        "your-key",
        "pk_test_your-publishable-key",
        "sk_test_your-secret-key",
        "change-me",
        "changeme",
        "placeholder",
    )
    if stripped.lower() in placeholders:
        return False
    # 排除以 your- 或 sk-your- 开头的明显占位符
    if stripped.startswith(("sk-your-", "pk_test_your-", "your-")):
        return False
    return True


def _check_playwright_browsers() -> dict[str, bool]:
    """检查 Playwright 浏览器是否已安装

    优先尝试导入 Playwright 并查询已安装的浏览器。
    如果 Playwright 未安装，返回相应的错误状态。
    """
    result: dict[str, bool] = {}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"playwright_installed": False, "chromium_ready": False, "firefox_ready": False}

    result["playwright_installed"] = True

    try:
        with sync_playwright() as p:
            browsers = getattr(p, "chromium", None)
            if browsers is not None:
                try:
                    browser = browsers.launch(headless=True)
                    browser.close()
                    result["chromium_ready"] = True
                except Exception:
                    result["chromium_ready"] = False
            else:
                result["chromium_ready"] = False

            firefox = getattr(p, "firefox", None)
            if firefox is not None:
                try:
                    browser = firefox.launch(headless=True)
                    browser.close()
                    result["firefox_ready"] = True
                except Exception:
                    result["firefox_ready"] = False
            else:
                result["firefox_ready"] = False
    except Exception:
        result.setdefault("chromium_ready", False)
        result.setdefault("firefox_ready", False)

    return result


def _check_playwright_deps(system_packages: bool = True) -> dict[str, Any]:
    """检查 Playwright 系统级依赖

    在 Docker 容器中，检查 libgbm, libnss3 等系统库是否已安装。
    设置 system_packages=False 可跳过系统包检查（非 Linux 环境）。
    """
    result: dict[str, Any] = {
        "system_deps_checked": system_packages,
    }

    if not system_packages:
        result["system_deps_ready"] = True
        return result

    import platform
    if platform.system() != "Linux":
        result["system_deps_ready"] = True
        result["note"] = f"skipped on {platform.system()}"
        return result

    # 检查关键的 Playwright 系统依赖
    critical_libs = [
        "libgbm.so.1",
        "libnss3.so",
        "libnspr4.so",
        "libatk-1.0.so.0",
        "libatk-bridge-2.0.so.0",
        "libcups.so.2",
        "libdrm.so.2",
        "libxkbcommon.so.0",
    ]

    missing_libs: list[str] = []
    import ctypes.util

    for lib in critical_libs:
        path = ctypes.util.find_library(lib.replace(".so", "").replace(".so.0", "").replace(".so.1", ""))
        if path is None:
            missing_libs.append(lib)

    result["missing_libs"] = missing_libs
    result["system_deps_ready"] = len(missing_libs) == 0
    if missing_libs:
        result["note"] = (
            "Run: playwright install-deps chromium  to install missing system dependencies"
        )

    return result


def validate_env(env: str | None = None, check_playwright: bool = True) -> dict[str, Any]:
    """校验所有环境变量，返回结构化的校验结果

    Args:
        env: 环境标识（"development" / "production"）。默认从 ENV 环境变量读取。
        check_playwright: 是否检查 Playwright 浏览器依赖。

    Returns:
        dict with keys: valid, missing, warnings, playwright, summary
    """
    env = env or os.getenv("ENV", "development")
    is_production = env == "production"

    missing: list[str] = []
    warnings: list[str] = []

    # 1. 检查 required 变量
    for var_name in REQUIRED_VARS:
        value = os.getenv(var_name)
        if not _is_set(value):
            missing.append(var_name)

    # 2. 检查 optional 变量
    for var_name in OPTIONAL_VARS:
        value = os.getenv(var_name)
        if not _is_set(value):
            warnings.append(var_name)

    # 3. 生产环境额外检查
    if is_production:
        for var_name in PRODUCTION_VARS:
            value = os.getenv(var_name)
            if not _is_set(value):
                warnings.append(var_name)

    # 4. Playwright 检查
    playwright_info: dict[str, Any] = {"configured": True, "ready": True, "details": {}}

    if check_playwright:
        browser_scrape = os.getenv("BROWSER_SCRAPE_ENABLED", "true").lower()
        playwright_info["configured"] = browser_scrape in ("true", "1", "yes")

        if playwright_info["configured"]:
            browser_check = _check_playwright_browsers()
            playwright_info["ready"] = browser_check.get("chromium_ready", False)

            # 在 Linux/Docker 环境检查系统依赖
            import platform
            deps_check = _check_playwright_deps(system_packages=(platform.system() == "Linux"))
            playwright_info["details"] = {**browser_check, **deps_check}
        else:
            playwright_info["ready"] = True  # 未启用，不计为失败
            playwright_info["note"] = "浏览器采集已禁用"

    # 5. 配置变量状态（仅记录，不影响 valid）
    config_status: dict[str, str] = {}
    for var_name, default in CONFIG_VARS.items():
        value = os.getenv(var_name)
        if _is_set(value):
            config_status[var_name] = "custom"
        elif value and not _is_set(value):
            config_status[var_name] = "default"
        else:
            config_status[var_name] = f"default ({default})"

    # 6. 构建摘要
    valid = len(missing) == 0
    summary_parts: list[str] = []

    if valid:
        summary_parts.append("[PASS] 所有必需环境变量已配置")
    else:
        summary_parts.append(f"[FAIL] 缺少 {len(missing)} 个必需环境变量: {', '.join(missing)}")

    if warnings:
        summary_parts.append(f"[WARN] 缺少 {len(warnings)} 个可选变量: {', '.join(warnings)}")

    if check_playwright and not playwright_info.get("ready"):
        if playwright_info.get("configured"):
            summary_parts.append(
                "[WARN] Playwright 浏览器未就绪，浏览器采集功能将不可用"
            )

    return {
        "valid": valid,
        "missing": missing,
        "warnings": warnings,
        "playwright": playwright_info,
        "config": config_status,
        "environment": env,
        "summary": " | ".join(summary_parts),
    }


def print_validation(use_stderr: bool = True) -> bool:
    """打印校验结果到控制台，返回 valid 状态

    适合在 startup.sh 或 main.py 启动时调用。
    设置 use_stderr=False 可输出到 stdout。

    Returns:
        True = 校验通过（所有 required 已配置）
    """
    result = validate_env()

    output = sys.stderr if use_stderr else sys.stdout

    print("=" * 56, file=output)
    print("  智媒圈 - 环境变量校验", file=output)
    print("=" * 56, file=output)

    # 环境标识
    env_label = f"[{result['environment'].upper()}]"
    print(f"  环境模式: {env_label}", file=output)

    # 必需变量
    if result["missing"]:
        print(f"\n  [FAIL] 缺少必需环境变量:", file=output)
        for var in result["missing"]:
            print(f"    - {var}", file=output)
    else:
        print(f"\n  [PASS] 所有必需环境变量已配置", file=output)

    # 可选变量警告
    if result["warnings"]:
        print(f"\n  [WARN] 缺少可选环境变量 (功能降级):", file=output)
        for var in result["warnings"]:
            print(f"    - {var}", file=output)

    # Playwright
    pw = result["playwright"]
    if not pw.get("ready", True):
        pw_details = pw.get("details", {})
        print(f"\n  [WARN] Playwright 浏览器未就绪", file=output)
        if not pw_details.get("playwright_installed", True):
            print(f"    - playwright 包未安装", file=output)
        if not pw_details.get("chromium_ready", True):
            print(f"    - Chromium 浏览器未安装 (运行: playwright install chromium)", file=output)
        if pw_details.get("missing_libs"):
            for lib in pw_details["missing_libs"]:
                print(f"    - 缺少系统库: {lib}", file=output)
            print(f"    - 修复: playwright install-deps chromium", file=output)

    # 配置覆盖
    custom_configs = {k: v for k, v in result["config"].items() if v == "custom"}
    if custom_configs:
        print(f"\n  [INFO] 使用自定义配置:", file=output)
        for var in sorted(custom_configs):
            print(f"    - {var}", file=output)

    print("=" * 56, file=output)

    return result["valid"]


def quick_check() -> dict[str, Any]:
    """快速校验（无打印，适合程序化调用）"""
    return validate_env(check_playwright=False)


# ====== 便捷断言 ======


def assert_env(var_name: str, friendly_name: str | None = None) -> str:
    """断言变量已设置并返回其值，未设置时抛出明确的异常

    Args:
        var_name: 环境变量名
        friendly_name: 人类友好的名称（用于错误消息）

    Returns:
        str: 环境变量的值

    Raises:
        RuntimeError: 当变量未设置或为空时
    """
    value = os.getenv(var_name)
    if not _is_set(value):
        label = friendly_name or var_name
        raise RuntimeError(
            f"环境变量 {var_name} ({label}) 未配置。"
            f"请在 .env 文件中设置该变量。"
        )
    return value.strip()
