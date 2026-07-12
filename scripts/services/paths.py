"""统一数据路径解析 - 支持所有 data/ 子目录

使用方法：
    from services.paths import get_dir, ensure_all, DATA_BASE

    # 获取某个子目录路径（自动创建）
    rules_dir = get_dir("rules")
    analytics_dir = get_dir("analytics")

    # 确保所有子目录存在（例如启动时调用）
    ensure_all()
"""

import os
from pathlib import Path


def _resolve_base() -> Path:
    """解析 data/ 目录的绝对路径

    优先级：
    1. 环境变量 ZHIMEIQUAN_DATA_DIR（适用于 Docker 等场景）
    2. 默认路径：相对于本文件（scripts/services/paths.py）的 ../../data/
    """
    env = os.environ.get("ZHIMEIQUAN_DATA_DIR")
    if env:
        return Path(env)
    # 本文件在 scripts/services/paths.py
    # data/ 在项目根目录
    return Path(__file__).resolve().parent.parent.parent / "data"


DATA_BASE = _resolve_base()

# 所有已知子目录
DIRS = {
    "rules": "rules",
    "analytics": "analytics",
    "scheduled": "scheduled",
    "agents": "agents",
    "templates": "templates",
    "ab_tests": "ab_tests",
    "teams": "teams",
    "videos": "videos",
    "images": "images",
    "competitors": "competitors",
    "calibration": "calibration",
    "rewrites": "rewrites",
    "router_history": "router_history",
    "insights": "insights",
    "workflows": "workflows",
}


def get_dir(name: str) -> Path:
    """获取子目录路径（不存在则自动创建）"""
    if name not in DIRS:
        raise KeyError(f"未知的数据子目录: {name}，可选: {list(DIRS.keys())}")
    p = DATA_BASE / DIRS[name]
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_all() -> Path:
    """确保所有子目录存在，返回 DATA_BASE 路径"""
    for name in DIRS:
        get_dir(name)
    return DATA_BASE
