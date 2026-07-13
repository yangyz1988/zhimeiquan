"""集成测试 — 验证 7 个新 API 路由"""

import sys
import os

# 直接添加 database.py 所在目录，避免 services/__init__ 的循环导入
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

# 直接导入 database 模块（不走 __init__）
import importlib.util
spec = importlib.util.spec_from_file_location("database", os.path.join(BASE, "services", "database.py"))
database = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database)

get_db = database.get_db
generate_id = database.generate_id

def test_database_tables():
    """验证数据库表已创建"""
    db = get_db()
    tables = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t["name"] for t in tables]

    expected = [
        "media_assets", "comments", "tags", "tag_groups", "content_tags",
        "subscriptions", "invoices", "billing_cycles",
        "distribution_channels", "publish_logs", "channel_metrics",
        "trend_events", "trend_snapshots"
    ]

    missing = [t for t in expected if t not in table_names]
    if missing:
        print(f"❌ 缺少表: {missing}")
        return False

    print(f"✅ 所有 {len(expected)} 张表已创建")
    return True


def test_insert_and_query():
    """测试插入和查询"""
    db = get_db()

    # 测试 media_assets
    asset_id = generate_id()
    db.conn.execute("""
        INSERT INTO media_assets (id, user_id, file_name, mime_type, size, url, created_at, updated_at)
        VALUES (?, 'test-user', 'test.png', 'image/png', 1024, '/test.png', datetime('now'), datetime('now'))
    """, [asset_id])

    row = db.conn.execute("SELECT * FROM media_assets WHERE id = ?", [asset_id]).fetchone()
    assert row is not None, "插入失败"
    assert row["file_name"] == "test.png", "数据不匹配"

    # 清理
    db.conn.execute("DELETE FROM media_assets WHERE id = ?", [asset_id])
    db.conn.commit()

    print("✅ media_assets 插入/查询/删除正常")
    return True


def test_routers_import():
    """测试路由模块可导入"""
    try:
        from routers import (
            media_assets, comments, tags,
            subscriptions, channels, publish_logs, trends
        )
        print("✅ 7 个路由模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 路由导入失败: {e}")
        return False


def test_router_endpoints():
    """测试路由端点定义"""
    from routers import media_assets, comments, tags, subscriptions, channels, publish_logs, trends

    routers = [
        ("media_assets", media_assets),
        ("comments", comments),
        ("tags", tags),
        ("subscriptions", subscriptions),
        ("channels", channels),
        ("publish_logs", publish_logs),
        ("trends", trends),
    ]

    for name, router in routers:
        routes = [r.path for r in router.routes]
        if not routes:
            print(f"❌ {name} 没有定义路由")
            return False
        print(f"  {name}: {len(routes)} 个端点")

    print("✅ 所有路由端点已定义")
    return True


def main():
    print("=" * 50)
    print("智媒圈 API 集成测试")
    print("=" * 50)

    tests = [
        ("数据库表", test_database_tables),
        ("插入查询", test_insert_and_query),
        ("路由导入", test_routers_import),
        ("路由端点", test_router_endpoints),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        print(f"\n测试: {name}")
        print("-" * 40)
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 异常: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())