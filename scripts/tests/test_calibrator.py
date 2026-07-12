"""Fire Score 校准器单元测试

覆盖: 记录表现、权重校准、皮尔逊相关系数计算、
预测互动率、校准报告、全历史校准。
"""

import json
import os
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from analyzers.calibrator import (
    FireScoreCalibrator,
    DEFAULT_WEIGHTS,
    DIMENSIONS,
    _pearson,
)


# ── _pearson 函数 ─────────────────────────────────


class TestPearson:
    def test_perfect_positive_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        assert abs(_pearson(x, y) - 1.0) < 1e-10

    def test_perfect_negative_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        assert abs(_pearson(x, y) - (-1.0)) < 1e-10

    def test_no_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 3, 7, 2, 8]
        # 相关系数接近 0
        assert abs(_pearson(x, y)) < 0.5

    def test_constant_x(self):
        x = [1, 1, 1, 1, 1]
        y = [1, 2, 3, 4, 5]
        assert _pearson(x, y) == 0.0

    def test_constant_y(self):
        x = [1, 2, 3, 4, 5]
        y = [3, 3, 3, 3, 3]
        assert _pearson(x, y) == 0.0

    def test_single_element(self):
        assert _pearson([1], [2]) == 0.0

    def test_two_elements(self):
        x = [1, 2]
        y = [3, 6]
        assert abs(_pearson(x, y) - 1.0) < 1e-10


# ── FireScoreCalibrator ───────────────────────────


@pytest.fixture
def calibrator(tmp_path):
    """创建一个使用临时 SQLite 数据库的校准器"""
    db_path = tmp_path / "test_tracker.db"
    c = FireScoreCalibrator(db_path=db_path)
    yield c
    c.close()


class TestRecordPerformance:
    def test_record_performance_basic(self, calibrator):
        result = calibrator.record_performance(
            content_id="c1",
            user_id="u1",
            platform="抖音",
            fire_score=85.0,
            dimension_scores={"hook": 80, "trust": 90, "retention": 85, "conversion": 75, "emotion": 88},
            actual_metrics={"views": 1000, "likes": 100, "comments": 20, "shares": 10, "favorites": 5},
        )
        assert result["recorded"] is True
        assert result["engagement_rate"] > 0

    def test_record_performance_zero_views(self, calibrator):
        result = calibrator.record_performance(
            content_id="c2",
            user_id="u1",
            platform="抖音",
            fire_score=70.0,
            dimension_scores={"hook": 70, "trust": 65, "retention": 72, "conversion": 68, "emotion": 70},
            actual_metrics={"views": 0, "likes": 0, "comments": 0, "shares": 0, "favorites": 0},
        )
        assert result["engagement_rate"] == 0.0

    def test_record_performance_missing_dimensions(self, calibrator):
        result = calibrator.record_performance(
            content_id="c3",
            user_id="u1",
            platform="小红书",
            fire_score=None,
            dimension_scores={},
            actual_metrics={"views": 500, "likes": 50},
        )
        assert result["recorded"] is True


class TestCalibrate:
    def test_insufficient_data(self, calibrator):
        result = calibrator.calibrate("u1", "抖音")
        assert result["status"] == "insufficient_data"
        assert "至少需要" in result["message"]

    def test_calibrate_with_enough_data(self, calibrator):
        # 插入 10 条数据
        for i in range(10):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=70 + i * 2,
                dimension_scores={
                    "hook": 60 + i * 3,
                    "trust": 70 + i * 2,
                    "retention": 65 + i * 2,
                    "conversion": 55 + i * 3,
                    "emotion": 60 + i * 2,
                },
                actual_metrics={
                    "views": 1000 + i * 100,
                    "likes": 50 + i * 10,
                    "comments": 5 + i * 2,
                    "shares": 2 + i,
                    "favorites": 3 + i * 3,
                },
            )

        result = calibrator.calibrate("u1", "抖音")
        assert result["status"] == "calibrated"
        assert result["sample_count"] == 10
        weights = result["weights"]
        assert abs(sum(weights.values()) - 100.0) < 0.2  # 权重总和约 100

    def test_calibrate_default_when_no_correlation(self, calibrator):
        # 插入 10 条完全相同的数据（相关系数为 0）
        for i in range(10):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=80.0,
                dimension_scores={
                    "hook": 80, "trust": 80, "retention": 80,
                    "conversion": 80, "emotion": 80,
                },
                actual_metrics={"views": 1000, "likes": 100, "comments": 10, "shares": 5, "favorites": 5},
            )

        result = calibrator.calibrate("u1", "抖音")
        assert result["status"] == "calibrated"
        # 当无相关系数时回退到默认权重
        weights = result["weights"]
        for dim in DIMENSIONS:
            assert abs(weights[dim] - DEFAULT_WEIGHTS[dim]) < 0.5


class TestGetCalibratedWeights:
    def test_returns_default_when_no_data(self, calibrator):
        weights = calibrator.get_calibrated_weights("u1", "抖音")
        assert weights == DEFAULT_WEIGHTS

    def test_returns_calibrated_weights(self, calibrator):
        for i in range(10):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=70 + i,
                dimension_scores={
                    "hook": 60 + i * 2, "trust": 70 + i, "retention": 65 + i,
                    "conversion": 55 + i * 3, "emotion": 60 + i,
                },
                actual_metrics={"views": 1000, "likes": 100, "comments": 10, "shares": 5, "favorites": 5},
            )
        calibrator.calibrate("u1", "抖音")
        weights = calibrator.get_calibrated_weights("u1", "抖音")
        assert all(d in weights for d in DIMENSIONS)
        assert abs(sum(weights.values()) - 100.0) < 0.2


class TestPredictEngagement:
    def test_predict_with_default_weights(self, calibrator):
        scores = {"hook": 80, "trust": 75, "retention": 90, "conversion": 60, "emotion": 85}
        prediction = calibrator.predict_engagement("u1", "抖音", scores)
        # 基于默认权重计算
        expected = sum(scores[d] * DEFAULT_WEIGHTS[d] for d in DIMENSIONS) / 100
        assert abs(prediction - expected) < 0.1

    def test_predict_zero_scores(self, calibrator):
        prediction = calibrator.predict_engagement("u1", "抖音", {})
        assert prediction == 0.0


class TestGetHistory:
    def test_empty_history(self, calibrator):
        history = calibrator.get_history("u1", "抖音")
        assert history == []

    def test_history_with_data(self, calibrator):
        for i in range(5):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=80 + i,
                dimension_scores={"hook": 80, "trust": 75, "retention": 85, "conversion": 70, "emotion": 80},
                actual_metrics={"views": 1000, "likes": 100, "comments": 10, "shares": 5, "favorites": 5},
            )
        history = calibrator.get_history("u1", "抖音", limit=3)
        assert len(history) == 3
        assert history[0]["content_id"] == "c4"  # 按时间倒序


class TestCalibrateFromHistory:
    def test_insufficient_data(self, calibrator):
        result = calibrator.calibrate_from_history("u1", "抖音")
        assert result["status"] == "insufficient_data"

    def test_with_full_history(self, calibrator):
        for i in range(10):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=70 + i * 2,
                dimension_scores={
                    "hook": 60 + i * 3, "trust": 70 + i * 2, "retention": 65 + i * 2,
                    "conversion": 55 + i * 3, "emotion": 60 + i * 2,
                },
                actual_metrics={
                    "views": 1000 + i * 100, "likes": 50 + i * 10,
                    "comments": 5 + i * 2, "shares": 2 + i, "favorites": 3 + i * 3,
                },
            )
        result = calibrator.calibrate_from_history("u1", "抖音")
        assert result["status"] == "calibrated"
        assert result["method"] == "full_history_with_stability_check"
        assert result["sample_count"] == 10
        assert result["history_used"] == "all"
        assert "stability_check" in result


class TestGetCalibrationReport:
    def test_report_insufficient_data(self, calibrator):
        report = calibrator.get_calibration_report("u1", "抖音")
        assert report["summary"]["data_quality"] == "insufficient"
        assert report["summary"]["sample_count"] == 0

    def test_report_with_data(self, calibrator):
        for i in range(15):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=70 + i,
                dimension_scores={
                    "hook": 65 + i * 2, "trust": 70 + i, "retention": 68 + i,
                    "conversion": 60 + i * 2, "emotion": 65 + i,
                },
                actual_metrics={
                    "views": 1000 + i * 100, "likes": 50 + i * 10,
                    "comments": 5 + i * 2, "shares": 2 + i, "favorites": 3 + i * 3,
                },
            )
        report = calibrator.get_calibration_report("u1", "抖音")
        assert report["summary"]["data_quality"] == "low"  # 15 条 < 20
        assert report["summary"]["sample_count"] == 15
        assert "weights" in report
        assert "correlations" in report
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)

    def test_report_high_quality(self, calibrator):
        for i in range(60):
            calibrator.record_performance(
                content_id=f"c{i}",
                user_id="u1",
                platform="抖音",
                fire_score=70 + i,
                dimension_scores={
                    "hook": 65 + i * 2, "trust": 70 + i, "retention": 68 + i,
                    "conversion": 60 + i * 2, "emotion": 65 + i,
                },
                actual_metrics={
                    "views": 1000 + i * 100, "likes": 50 + i * 10,
                    "comments": 5 + i * 2, "shares": 2 + i, "favorites": 3 + i * 3,
                },
            )
        report = calibrator.get_calibration_report("u1", "抖音")
        assert report["summary"]["data_quality"] == "high"
        assert report["summary"]["sample_count"] == 60


class TestClose:
    def test_close_connection(self, calibrator):
        # 先建立连接
        _ = calibrator.conn
        assert calibrator._conn is not None
        calibrator.close()
        assert calibrator._conn is None
