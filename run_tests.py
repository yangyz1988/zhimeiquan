"""
测试运行脚本
"""

import subprocess
import sys

def run_backend_tests():
    """运行后端测试"""
    print("=" * 50)
    print("运行后端单元测试...")
    print("=" * 50)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd="scripts"
    )
    return result.returncode

def run_frontend_tests():
    """运行前端测试"""
    print("=" * 50)
    print("运行前端 E2E 测试...")
    print("=" * 50)

    result = subprocess.run(
        ["npx", "playwright", "test"],
        cwd="saas"
    )
    return result.returncode

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description="运行测试")
    parser.add_argument("--backend", action="store_true", help="只运行后端测试")
    parser.add_argument("--frontend", action="store_true", help="只运行前端测试")
    args = parser.parse_args()

    exit_code = 0

    if not args.frontend:
        exit_code |= run_backend_tests()

    if not args.backend:
        exit_code |= run_frontend_tests()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()