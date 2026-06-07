"""数据闭环 + A/B 测试"""

import pytest
import tempfile
from pathlib import Path
from services.data_loop import DataTracker, ABTester


def test_record_publish():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = DataTracker(data_dir=tmpdir)
        record = tracker.record_publish(
            project_id="proj_1",
            platform="抖音",
            title="测试标题",
            content_id="content_1",
        )
        assert record["project_id"] == "proj_1"
        assert record["metrics"]["views"] == 0
        assert Path(
            record is not None and (Path(tmpdir) / "proj_1_content_1.json")
        ).exists()


def test_update_metrics():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = DataTracker(data_dir=tmpdir)
        tracker.record_publish("proj_1", "抖音", "标题", "content_1")
        result = tracker.update_metrics(
            "proj_1",
            "content_1",
            {
                "views": 1000,
                "likes": 50,
            },
        )
        assert result["metrics"]["views"] == 1000
        assert result["metrics"]["likes"] == 50


def test_get_project_analytics():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = DataTracker(data_dir=tmpdir)
        tracker.record_publish("proj_1", "抖音", "标题1", "c1")
        tracker.record_publish("proj_1", "小红书", "标题2", "c2")
        tracker.update_metrics(
            "proj_1", "c1", {"views": 100, "likes": 10, "comments": 2, "shares": 1}
        )
        tracker.update_metrics(
            "proj_1", "c2", {"views": 200, "likes": 20, "comments": 4, "shares": 2}
        )

        analytics = tracker.get_project_analytics("proj_1")
        assert analytics["total_content"] == 2
        assert analytics["total_views"] == 300
        assert analytics["total_likes"] == 30


def test_get_platform_summary():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = DataTracker(data_dir=tmpdir)
        tracker.record_publish("p1", "抖音", "t1", "c1")
        tracker.record_publish("p1", "抖音", "t2", "c2")
        tracker.record_publish("p1", "小红书", "t3", "c3")
        tracker.update_metrics("p1", "c1", {"views": 100, "likes": 10})
        tracker.update_metrics("p1", "c2", {"views": 200, "likes": 20})
        tracker.update_metrics("p1", "c3", {"views": 50, "likes": 5})

        summary = tracker.get_platform_summary()
        assert summary["抖音"]["count"] == 2
        assert summary["抖音"]["views"] == 300
        assert summary["小红书"]["count"] == 1


def test_ab_tester_create():
    with tempfile.TemporaryDirectory() as tmpdir:
        tester = ABTester(data_dir=tmpdir)
        test = tester.create_test(
            "test_1",
            "proj_1",
            [
                {"title": "标题A", "content": "内容A"},
                {"title": "标题B", "content": "内容B"},
            ],
        )
        assert test["test_id"] == "test_1"
        assert len(test["variants"]) == 2
        assert test["status"] == "running"


def test_ab_tester_winner():
    with tempfile.TemporaryDirectory() as tmpdir:
        tester = ABTester(data_dir=tmpdir)
        tester.create_test(
            "test_1",
            "proj_1",
            [
                {"title": "A", "content": "A"},
                {"title": "B", "content": "B"},
            ],
        )
        # 给 A 较少数据，B 较多
        tester.update_variant_metrics(
            "test_1",
            "variant_0",
            {"views": 100, "likes": 5, "comments": 1, "shares": 0},
        )
        tester.update_variant_metrics(
            "test_1",
            "variant_1",
            {"views": 1000, "likes": 100, "comments": 20, "shares": 5},
        )

        result = tester.get_winner("test_1")
        assert result["winner"]["id"] == "variant_1"
