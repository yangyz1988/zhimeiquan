#!/usr/bin/env python3
"""部署健康检查脚本 - 验证所有服务正常运行

用法:
    python health_check.py                     # 检查 localhost:8000
    python health_check.py http://prod:8000   # 检查指定地址
"""

import sys
import requests


def check_service(url: str, name: str) -> bool:
    """检查单个服务端点"""
    try:
        r = requests.get(url, timeout=5)
        status = r.status_code
        if status < 500:
            print(f"  [PASS] {name}: {url} -> {status}")
            return True
        else:
            print(f"  [FAIL] {name}: {url} -> {status} (服务器错误)")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] {name}: {url} -> 连接失败")
        return False
    except requests.exceptions.Timeout:
        print(f"  [FAIL] {name}: {url} -> 超时")
        return False
    except Exception as e:
        print(f"  [FAIL] {name}: {url} -> {e}")
        return False


def main() -> int:
    """运行所有健康检查"""
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    frontend = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"

    print("=" * 50)
    print("  智媒圈 部署健康检查")
    print("=" * 50)
    print(f"  API 地址:   {base}")
    print(f"  前端地址:   {frontend}")
    print("=" * 50)

    checks = [
        # API 后端核心端点
        (f"{base}/health", "API Health (存活)"),
        (f"{base}/ready", "API Readiness (就绪)"),
        (f"{base}/docs", "API Swagger 文档"),
        (f"{base}/metrics", "API Prometheus 指标"),
        # 业务 API
        (f"{base}/api/v1/router/profiles", "模型路由配置"),
        (f"{base}/api/v1/templates/list", "内容模板列表"),
        # 前端
        (f"{frontend}", "前端首页"),
    ]

    results = [check_service(url, name) for url, name in checks]

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print("=" * 50)
    print(f"  结果: {passed}/{total} 通过", end="")
    if failed > 0:
        print(f", {failed} 失败")
    else:
        print()
    print("=" * 50)

    # 返回 0 表示全部通过，1 表示有失败
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
