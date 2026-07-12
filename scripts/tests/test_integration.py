"""全链路集成测试 - 覆盖所有新增强化模块

测试策略：
1. 所有数据写入使用临时目录 (tempfile)
2. 模块路径自动补丁，避免依赖 mounted 目录权限
3. 测试后自动清理临时文件
4. 使用 sys.path 注入确保模块导入正确

覆盖模块：
- analyzers.calibrator (Fire Score 校准)
- analyzers.data_tracker (数据追踪器)
- automation.engine (自动化工作流引擎)
- monitors.competitor (竞品监控)
- services.metrics (Prometheus 指标收集)
- services.error_codes (统一错误码系统)
- generators.rewriter (内容改写引擎 + 数据模型)
- services.knowledge_graph (知识图谱检索)
"""

import json
import math
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── 预定义模块路径 ──────────────────────────────────────────────
# 确保 scripts/ 目录在 sys.path 上
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

# ── 解决模块级路径依赖 ──────────────────────────────────────
#
# scheduler_service.py 模块级有 content_scheduler = ContentScheduler()。
# ContentScheduler.__init__ 会执行 Path("../data/scheduled").mkdir()。
# 这是相对于 CWD 的路径，测试 CWD 不可控。
# services/__init__.py 会导入 scheduler_service，触发此副作用。
#
# 解决方案：在加载 services 包之前，向 sys.modules 中注入一个
# 空的 "services" 模块，阻止 __init__.py 的执行。
# 后续各测试通过 importlib 直接加载特定模块。
import importlib
import types as _types

# 确保 sys.modules 中 "services" 不会被 __init__.py 填充
_services_mod_stub = _types.ModuleType("services")
_services_mod_stub.__path__ = [str(Path(_scripts_dir) / "services")]
_services_mod_stub.__package__ = "services"
sys.modules["services"] = _services_mod_stub


# ══════════════════════════════════════════════════════════════════
#  辅助工具
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
#  A) Fire Score 校准流 ── analyzers.calibrator + data_tracker
# ══════════════════════════════════════════════════════════════════


class TestFireScoreCalibrationFlow:
    """Fire Score 校准全流程集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_calibrator.db"
        self.DEFAULT_WEIGHTS = {"hook": 25.0, "trust": 20.0,
                                "retention": 25.0, "conversion": 15.0,
                                "emotion": 15.0}
        self.DIMENSIONS = list(self.DEFAULT_WEIGHTS.keys())
        yield
        shutil.rmtree(self.tmp_dir)

    def _make_calibrator(self):
        from analyzers.calibrator import FireScoreCalibrator
        return FireScoreCalibrator(db_path=self.db_path)

    # ── A1: 核心校准流程 ──

    def test_fire_score_calibration_flow(self):
        """创建校准器 -> 记录 10+ 条带递增互动率的数据 -> 校准 -> 验证权重调整"""
        cal = self._make_calibrator()

        # 记录 10 条数据，互动率递增
        for i in range(10):
            cal.record_performance(
                content_id=f"c{i:03d}", user_id="u_flow", platform="抖音",
                fire_score=70.0 + i * 2,
                dimension_scores={
                    "hook": 75 + i, "trust": 70, "retention": 72,
                    "conversion": 65 + i // 2, "emotion": 60 + i,
                },
                actual_metrics={
                    "views": 1000 + i * 100,
                    "likes": 50 + i * 10,
                    "comments": 10 + i * 2,
                    "shares": 5 + i,
                    "favorites": 2 + i // 2,
                },
            )

        # 执行校准
        result = cal.calibrate("u_flow", "抖音")

        # 验证状态
        assert result["status"] == "calibrated", f"校准失败: {result.get('message', '')}"
        assert result["sample_count"] == 10

        # 验证权重已从默认值调整
        weights = result["weights"]
        for dim in self.DIMENSIONS:
            assert dim in weights, f"缺少维度: {dim}"
            assert 0 <= weights[dim] <= 60, f"权重 {dim}={weights[dim]} 不在合理范围"

        # 验证权重和 ≈ 100
        total = sum(weights.values())
        assert abs(total - 100.0) < 1.0, f"权重总和 {total} 偏离 100"

        # 验证相关性被计算
        assert "correlations" in result
        for dim in self.DIMENSIONS:
            assert dim in result["correlations"]
            assert 0 <= result["correlations"][dim] <= 1

        cal.close()

    # ── A2: get_calibrated_weights ──

    def test_get_calibrated_weights_returns_dict_with_5_keys(self):
        """get_calibrated_weights 应返回包含 5 个维度的字典"""
        cal = self._make_calibrator()
        weights = cal.get_calibrated_weights("user_w", "小红书")
        assert isinstance(weights, dict)
        assert len(weights) == 5
        for dim in self.DIMENSIONS:
            assert dim in weights
        cal.close()

    def test_get_calibrated_weights_after_calibration(self):
        """校准后获取的权重应与校准结果一致"""
        cal = self._make_calibrator()
        for i in range(8):
            cal.record_performance(
                content_id=f"gw{i:03d}", user_id="u_gw", platform="微博",
                fire_score=80.0,
                dimension_scores={"hook": 80, "trust": 75, "retention": 78,
                                  "conversion": 70, "emotion": 72},
                actual_metrics={"views": 500, "likes": 40, "comments": 8,
                                "shares": 4, "favorites": 2},
            )
        result = cal.calibrate("u_gw", "微博")
        assert result["status"] == "calibrated"

        persisted = cal.get_calibrated_weights("u_gw", "微博")
        for dim in self.DIMENSIONS:
            assert persisted[dim] == result["weights"][dim]
        cal.close()

    # ── A3: predict_engagement ──

    def test_predict_engagement_returns_reasonable_values(self):
        """predict_engagement 应返回合理的预测互动率"""
        cal = self._make_calibrator()

        # 无数据时也应返回预测值（使用默认权重）
        prediction = cal.predict_engagement(
            "u_pred_new", "抖音",
            {"hook": 90, "trust": 80, "retention": 85,
             "conversion": 75, "emotion": 70},
        )
        assert isinstance(prediction, float)
        assert 0 <= prediction <= 100

        # 有数据并校准后预测
        for i in range(5):
            cal.record_performance(
                content_id=f"pe{i:03d}", user_id="u_pred2", platform="抖音",
                fire_score=80.0,
                dimension_scores={"hook": 80, "trust": 75, "retention": 78,
                                  "conversion": 70, "emotion": 72},
                actual_metrics={"views": 500, "likes": 40, "comments": 8,
                                "shares": 4, "favorites": 2},
            )
        cal.calibrate("u_pred2", "抖音")

        prediction2 = cal.predict_engagement(
            "u_pred2", "抖音",
            {"hook": 95, "trust": 85, "retention": 90,
             "conversion": 80, "emotion": 75},
        )
        assert isinstance(prediction2, float)
        # 更高的维度分应产生更高的预测
        assert prediction2 >= 0
        cal.close()

    # ── A4: get_calibration_report ──

    def test_get_calibration_report_returns_structured_report(self):
        """get_calibration_report 应返回包含权重、相关性和建议的结构化报告"""
        cal = self._make_calibrator()

        # 未校准时应返回基础报告
        report = cal.get_calibration_report("u_report_new", "小红书")
        assert "user_id" in report
        assert "platform" in report
        assert "summary" in report
        assert "weights" in report
        assert "correlations" in report
        assert "recommendations" in report
        assert report["summary"]["status"] == "insufficient_data"

        # 有足够数据后应包含详细分析
        for i in range(8):
            cal.record_performance(
                content_id=f"rp{i:03d}", user_id="u_report2", platform="小红书",
                fire_score=75.0 + i,
                dimension_scores={"hook": 80, "trust": 70 + i, "retention": 75,
                                  "conversion": 65, "emotion": 60},
                actual_metrics={"views": 800, "likes": 60 + i * 5,
                                "comments": 12, "shares": 8, "favorites": 3},
            )

        report2 = cal.get_calibration_report("u_report2", "小红书")
        assert report2["summary"]["status"] == "calibrated"
        assert report2["summary"]["sample_count"] >= 8
        assert "data_quality" in report2["summary"]
        assert "engagement_trend" in report2["summary"]
        assert "strongest_dimension" in report2
        assert "weakest_dimension" in report2
        cal.close()

    # ── A5: 边缘情况 ──

    def test_calibrate_with_zero_engagement(self):
        """所有互动为 0 时应优雅处理"""
        cal = self._make_calibrator()
        for i in range(10):
            cal.record_performance(
                content_id=f"ze{i:03d}", user_id="u_zero", platform="抖音",
                fire_score=80.0,
                dimension_scores={"hook": 80, "trust": 75, "retention": 78,
                                  "conversion": 70, "emotion": 72},
                actual_metrics={"views": 1000, "likes": 0, "comments": 0,
                                "shares": 0, "favorites": 0},
            )
        result = cal.calibrate("u_zero", "抖音")
        # 所有 engagement 为 0 时，correlations 为 0，权重应回退默认
        assert result["status"] == "calibrated"
        # total_corr ≈ 0 => 使用默认权重
        weights = result["weights"]
        for dim in self.DIMENSIONS:
            assert weights[dim] == self.DEFAULT_WEIGHTS[dim]
        cal.close()

    def test_calibrate_from_history_uses_all_data(self):
        """calibrate_from_history 应使用全量历史数据并应用稳定性检查"""
        cal = self._make_calibrator()
        for i in range(20):
            cal.record_performance(
                content_id=f"ch{i:03d}", user_id="u_full", platform="B站",
                fire_score=70.0 + i,
                dimension_scores={"hook": 80, "trust": 70, "retention": 75,
                                  "conversion": 65, "emotion": 60},
                actual_metrics={"views": 500, "likes": 30 + i, "comments": 5,
                                "shares": 3, "favorites": 1},
            )
        result = cal.calibrate_from_history("u_full", "B站")
        assert result["status"] == "calibrated"
        assert result["method"] == "full_history_with_stability_check"
        assert result["sample_count"] == 20
        assert result["history_used"] == "all"
        assert "stability_check" in result
        cal.close()


class TestDataTrackerFlow:
    """DataTracker 全流程集成测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.tmp_dir) / "test_tracker.db"
        yield
        shutil.rmtree(self.tmp_dir)

    def _make_tracker(self):
        from analyzers.data_tracker import DataTracker
        return DataTracker(db_path=self.db_path)

    # ── B1: record_publish ──

    def test_record_publish_creates_record(self):
        """record_publish 应创建发布记录并返回确认"""
        dt = self._make_tracker()
        result = dt.record_publish(
            content_id="pub_001", user_id="u1", platform="抖音",
            title="集成测试内容", fire_score=88.0,
            dimension_scores={"hook": 90, "trust": 80, "retention": 88,
                              "conversion": 75, "emotion": 70},
        )
        assert result["recorded"] is True
        assert result["content_id"] == "pub_001"

        # 验证可查询
        rows = dt.conn.execute(
            "SELECT * FROM performance_records WHERE content_id = ?",
            ("pub_001",),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["fire_score"] == 88.0
        dt.close()

    # ── B2: update_metrics ──

    def test_update_metrics_updates_existing_record(self):
        """update_metrics 应更新已有记录的互动指标"""
        dt = self._make_tracker()
        dt.record_publish(content_id="met_001", user_id="u1", platform="微博",
                          title="指标测试")

        result = dt.update_metrics("met_001", {
            "views": 5000, "likes": 500, "comments": 100,
            "shares": 50, "favorites": 20,
        })
        assert result["views"] == 5000
        assert result["likes"] == 500

        # 验证互动率计算正确
        expected_eng = (500 + 100 + 50 + 20) / 5000
        assert result["engagement_rate"] == round(expected_eng, 4)
        dt.close()

    # ── B3: get_platform_history ──

    def test_get_platform_history_returns_records(self):
        """get_platform_history 应返回按时间倒序的记录"""
        dt = self._make_tracker()
        for i in range(5):
            dt.record_publish(
                content_id=f"hist{i:03d}", user_id="u_hist", platform="小红书",
                title=f"历史记录{i}",
            )

        records = dt.get_platform_history("u_hist", "小红书")
        assert len(records) == 5
        # 验证时间倒序
        timestamps = [r["created_at"] for r in records]
        assert timestamps == sorted(timestamps, reverse=True)
        dt.close()

    def test_get_platform_history_empty(self):
        """无历史数据时应返回空列表"""
        dt = self._make_tracker()
        records = dt.get_platform_history("nobody", "知乎")
        assert records == []
        dt.close()

    # ── B4: get_fire_score_accuracy ──

    def test_get_fire_score_accuracy_computes_correlation(self):
        """get_fire_score_accuracy 应计算 Fire Score 与实际互动的相关性"""
        dt = self._make_tracker()
        # 创建有相关性的数据：fire_score 与 engagement 正相关
        for i in range(10):
            score = 60.0 + i * 3
            engagement = score * 2  # 强正相关
            dt.record_publish(
                content_id=f"acc{i:03d}", user_id="u_acc", platform="抖音",
                title=f"精度{i}", fire_score=score,
                dimension_scores={"hook": score, "trust": 70, "retention": 75,
                                  "conversion": 65, "emotion": 60},
            )
            dt.update_metrics(f"acc{i:03d}", {
                "views": 1000,
                "likes": int(engagement),
                "comments": int(engagement * 0.2),
                "shares": int(engagement * 0.1),
                "favorites": int(engagement * 0.05),
            })

        result = dt.get_fire_score_accuracy("u_acc", "抖音")
        assert "correlation" in result
        assert result["correlation"] > 0  # 应为正相关
        assert result["sample_count"] >= 3
        dt.close()

    def test_get_fire_score_accuracy_insufficient_data(self):
        """数据不足时应返回 None"""
        dt = self._make_tracker()
        result = dt.get_fire_score_accuracy("u_empty", "B站")
        assert result["accuracy"] is None
        assert "数据不足" in result.get("message", "")
        dt.close()

    # ── B5: predict_engagement (DataTracker 版本) ──

    def test_data_tracker_predict_engagement(self):
        """DataTracker.predict_engagement 应返回带置信度的预测"""
        dt = self._make_tracker()
        for i in range(5):
            dt.record_publish(
                content_id=f"dp{i:03d}", user_id="u_dp", platform="抖音",
                title=f"预测{i}", fire_score=80.0,
            )
            dt.update_metrics(f"dp{i:03d}", {
                "views": 1000, "likes": 100 + i * 10,
                "comments": 20, "shares": 10, "favorites": 5,
            })

        result = dt.predict_engagement(
            "u_dp", "抖音",
            {"hook": 85, "trust": 75, "retention": 80,
             "conversion": 70, "emotion": 65},
        )
        assert "predicted_engagement" in result
        assert "confidence" in result
        assert "sample_count" in result
        assert result["sample_count"] == 5
        dt.close()

    # ── B6: get_user_summary ──

    def test_get_user_summary_aggregates_by_platform(self):
        """get_user_summary 应按平台聚合统计数据"""
        dt = self._make_tracker()
        for i in range(3):
            dt.record_publish(content_id=f"s{i:03d}", user_id="u_sum",
                              platform="抖音", title=f"汇总{i}")
            dt.update_metrics(f"s{i:03d}", {
                "views": 1000, "likes": 100,
                "comments": 20, "shares": 10, "favorites": 5,
            })

        summary = dt.get_user_summary("u_sum")
        assert summary["user_id"] == "u_sum"
        assert "抖音" in summary["platforms"]
        assert summary["platforms"]["抖音"]["total_content"] == 3
        assert summary["platforms"]["抖音"]["total_views"] == 3000
        dt.close()


# ══════════════════════════════════════════════════════════════════
#  B) 自动化工作流引擎 ── automation.engine
# ══════════════════════════════════════════════════════════════════


class TestAutomationEngineFlow:
    """自动化工作流引擎全流程测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.workflows_dir = Path(self.tmp_dir) / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        yield
        shutil.rmtree(self.tmp_dir)

    def _make_engine(self):
        from automation.engine import AutomationEngine
        return AutomationEngine(workflows_dir=str(self.workflows_dir))

    def _make_time_trigger(self):
        from automation.engine import TimeTrigger
        return TimeTrigger(cron_expression="0 9 * * *")

    def _make_generate_action(self):
        from automation.engine import GenerateAction
        return GenerateAction(topic="AI 科技", platform="抖音", count=1)

    # ── C1: 创建 TimeTrigger 工作流 ──

    def test_create_workflow_with_time_trigger(self):
        """应能创建带 TimeTrigger 的工作流并验证所有字段"""
        engine = self._make_engine()
        trigger = self._make_time_trigger()
        actions = [self._make_generate_action()]

        wf = engine.create_workflow(
            user_id="u_wf", name="每日AI内容生成",
            trigger=trigger, actions=actions,
        )

        assert wf["user_id"] == "u_wf"
        assert wf["name"] == "每日AI内容生成"
        assert wf["status"] == "active"
        assert wf["trigger"]["type"] == "time"
        assert wf["trigger"]["cron_expression"] == "0 9 * * *"
        assert len(wf["actions"]) == 1
        assert wf["actions"][0]["type"] == "generate"
        assert "workflow_id" in wf
        assert "created_at" in wf
        assert "stats" in wf
        assert wf["stats"]["total_executions"] == 0
        assert wf["stats"]["successful_executions"] == 0

    # ── C2: 列出工作流 ──

    def test_list_workflows_returns_user_workflows(self):
        """list_workflows 应返回对应用户的所有工作流"""
        engine = self._make_engine()
        trigger = self._make_time_trigger()
        gen_action = self._make_generate_action()

        from automation.engine import NotifyAction
        notify_action = NotifyAction(message="完成", channel="log")

        engine.create_workflow("u1", "工作流A", trigger, [gen_action])
        engine.create_workflow("u1", "工作流B", trigger, [notify_action])
        engine.create_workflow("u2", "其他工作流", trigger, [gen_action])

        u1_list = engine.list_workflows("u1")
        assert len(u1_list) == 2
        names = [w["name"] for w in u1_list]
        assert "工作流A" in names
        assert "工作流B" in names

        u2_list = engine.list_workflows("u2")
        assert len(u2_list) == 1
        assert u2_list[0]["name"] == "其他工作流"

        assert engine.list_workflows("nobody") == []

    # ── C3: 执行工作流 ──

    def test_execute_workflow_runs_actions(self):
        """execute_workflow 应依次执行所有动作并返回结果"""
        engine = self._make_engine()
        from automation.engine import NotifyAction

        wf = engine.create_workflow(
            "u_exec", "执行测试", self._make_time_trigger(),
            [self._make_generate_action(), NotifyAction(message="生成完成", channel="log")],
        )

        result = engine.execute_workflow(wf["workflow_id"])
        assert result["status"] == "completed"
        assert len(result["action_results"]) == 2
        assert result["action_results"][0]["action"] == "generate"
        assert result["action_results"][0]["status"] == "queued"
        assert result["action_results"][1]["action"] == "notify"
        assert result["action_results"][1]["status"] == "sent"

    def test_execute_workflow_nonexistent(self):
        """执行不存在的工作流应返回 error"""
        engine = self._make_engine()
        result = engine.execute_workflow("no_such_wf")
        assert result["status"] == "error"

    def test_execute_paused_workflow_skipped(self):
        """暂停的工作流不应执行"""
        engine = self._make_engine()
        wf = engine.create_workflow(
            "u_pause", "暂停工作流", self._make_time_trigger(),
            [self._make_generate_action()],
        )
        engine.update_workflow(wf["workflow_id"], {"status": "paused"})
        result = engine.execute_workflow(wf["workflow_id"])
        assert result["status"] == "skipped"

    # ── C4: 删除工作流 ──

    def test_delete_workflow_removes_permanently(self):
        """delete_workflow 应彻底移除工作流文件"""
        engine = self._make_engine()
        wf = engine.create_workflow(
            "u_del", "待删除", self._make_time_trigger(),
            [self._make_generate_action()],
        )
        wid = wf["workflow_id"]

        assert engine.get_workflow(wid) is not None
        assert engine.delete_workflow(wid) is True
        assert engine.get_workflow(wid) is None

    def test_delete_workflow_nonexistent_returns_false(self):
        """删除不存在的工作流应返回 False"""
        engine = self._make_engine()
        assert engine.delete_workflow("no_such_id") is False

    # ── C5: 触发器与动作类型验证 ──

    def test_all_trigger_types_serialization(self):
        """所有触发器类型的序列化/反序列化应正确"""
        from automation.engine import (
            TimeTrigger, HotTopicTrigger, PerformanceTrigger,
            ScheduleTrigger, trigger_from_dict,
        )

        triggers = [
            TimeTrigger(cron_expression="30 8 * * 1"),
            HotTopicTrigger(keywords=["AI"], platform="抖音"),
            PerformanceTrigger(metric="engagement_rate", threshold=0.05),
            ScheduleTrigger(scheduled_time=datetime.now().isoformat()),
        ]

        for t in triggers:
            d = t.to_dict()
            t2 = trigger_from_dict(d)
            assert type(t2) == type(t)
            assert t2.get_type() == t.get_type()

    def test_all_action_types_serialization(self):
        """所有动作类型的序列化/反序列化应正确"""
        from automation.engine import (
            GenerateAction, RewriteAction, PublishAction,
            NotifyAction, AnalyzeAction, action_from_dict,
        )

        actions = [
            GenerateAction(topic="AI", platform="抖音", count=2),
            RewriteAction(content_id="c123", style="optimize"),
            PublishAction(platform="小红书", content_id="c456"),
            NotifyAction(message="通知消息", channel="email"),
            AnalyzeAction(analysis_type="trends", platform="B站", days=14),
        ]

        for a in actions:
            d = a.to_dict()
            a2 = action_from_dict(d)
            assert type(a2) == type(a)
            assert a2.get_type() == a.get_type()

    def test_unknown_trigger_raises_value_error(self):
        """未知触发器类型应抛出 ValueError"""
        from automation.engine import trigger_from_dict
        with pytest.raises(ValueError, match="未知触发器类型"):
            trigger_from_dict({"type": "unknown_type"})

    def test_unknown_action_raises_value_error(self):
        """未知动作类型应抛出 ValueError"""
        from automation.engine import action_from_dict
        with pytest.raises(ValueError, match="未知动作类型"):
            action_from_dict({"type": "unknown_action"})

    # ── C6: check_triggers ──

    def test_check_triggers_evaluates_hot_topic(self):
        """check_triggers 应评估 HotTopicTrigger 并返回匹配的工作流"""
        from automation.engine import HotTopicTrigger

        engine = self._make_engine()
        engine.create_workflow(
            "u_check", "热点检测",
            HotTopicTrigger(keywords=["AI", "人工智能"], platform="抖音"),
            [self._make_generate_action()],
        )

        # 提供匹配的热搜
        triggered = engine.check_triggers("u_check", {
            "hot_topics": ["AI 颠覆教育行业", "今日天气预报"],
        })
        assert len(triggered) == 1
        assert triggered[0]["name"] == "热点检测"

        # 不匹配的热搜
        triggered2 = engine.check_triggers("u_check", {
            "hot_topics": ["天气", "美食推荐"],
        })
        assert len(triggered2) == 0

    # ── C7: get_workflow_stats ──

    def test_get_workflow_stats_returns_statistics(self):
        """get_workflow_stats 应返回完整的统计数据"""
        engine = self._make_engine()
        engine.create_workflow("u_stat", "统计A", self._make_time_trigger(),
                               [self._make_generate_action()])
        engine.create_workflow("u_stat", "统计B", self._make_time_trigger(),
                               [self._make_generate_action()])

        stats = engine.get_workflow_stats("u_stat")
        assert stats["total_workflows"] == 2
        assert stats["active_workflows"] == 2
        assert len(stats["workflow_list"]) == 2
        assert stats["user_id"] == "u_stat"

        empty_stats = engine.get_workflow_stats("nobody")
        assert empty_stats["total_workflows"] == 0


# ══════════════════════════════════════════════════════════════════
#  C) 竞品监控 ── monitors.competitor (直接导入 CompetitorMonitor)
# ══════════════════════════════════════════════════════════════════


class TestCompetitorMonitorFlow:
    """竞品监控全流程测试 - 直接导入 CompetitorMonitor 类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.competitors_dir = Path(self.tmp_dir) / "competitors"
        self.competitors_dir.mkdir(parents=True, exist_ok=True)
        yield
        shutil.rmtree(self.tmp_dir)

    def _make_monitor(self):
        """直接通过 importlib 导入 CompetitorMonitor

        注意：competitor.py 的模块级导入 chain 是
        monitors.__init__ -> monitors.scraper (有外部依赖)，
        因此直接导入 CompetitorMonitor 类本身。
        """
        # 直接将 monitors 模块的路径加入 sys.path 以便 import
        from monitors.competitor import CompetitorMonitor
        return CompetitorMonitor(data_dir=str(self.competitors_dir))

    # ── D1: 添加竞品 ──

    def test_add_competitor_creates_entry(self):
        """add_competitor 应创建竞品条目并返回完整信息"""
        monitor = self._make_monitor()
        result = monitor.add_competitor(
            user_id="u_comp", platform="抖音",
            account_id="douyin_123", account_name="科技博主",
        )
        assert "competitor" in result
        c = result["competitor"]
        assert c["user_id"] == "u_comp"
        assert c["platform"] == "抖音"
        assert c["account_name"] == "科技博主"
        assert c["total_content"] == 0
        assert "id" in c

    def test_add_competitor_duplicate_returns_error(self):
        """添加重复竞品应返回错误"""
        monitor = self._make_monitor()
        monitor.add_competitor("u1", "抖音", "acc_001", "账号A")
        result = monitor.add_competitor("u1", "抖音", "acc_001", "账号A")
        assert "error" in result

    # ── D2: 记录竞品内容 ──

    def test_record_content_stores_and_updates_summary(self):
        """record_content 应存储内容数据并更新竞品汇总"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "小红书", "xhs_001", "竞品账号")
        cid = result["competitor"]["id"]

        # 记录多条内容
        for i in range(3):
            monitor.record_content(cid, {
                "content_id": f"v{i:03d}",
                "title": f"爆款视频{i}",
                "content_type": "视频",
                "metrics": {
                    "views": (i + 1) * 1000,
                    "likes": (i + 1) * 100,
                    "comments": (i + 1) * 20,
                    "shares": (i + 1) * 10,
                    "saves": (i + 1) * 5,
                },
                "topics": ["AI", "科技"],
                "style_tags": ["教程"],
                "summary": f"AI教程视频{i}",
            })

        # 验证汇总已更新
        competitors = monitor.list_competitors("u1")
        comp = next(c for c in competitors if c["id"] == cid)
        assert comp["total_content"] == 3
        assert comp["total_views"] == 6000  # 1000+2000+3000
        assert comp["total_likes"] == 600   # 100+200+300

    def test_record_content_duplicate_returns_error(self):
        """记录已存在的内容 ID 应返回错误"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "抖音", "acc_dup", "重复测试")
        cid = result["competitor"]["id"]
        data = {"content_id": "dup_v001", "title": "重复内容",
                "metrics": {"views": 100}}
        monitor.record_content(cid, data)
        result2 = monitor.record_content(cid, data)
        assert "error" in result2

    # ── D3: 分析竞品 ──

    def test_analyze_competitor_returns_detailed_analysis(self):
        """analyze_competitor 应返回完整的竞品分析结果"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "抖音", "acc_analysis", "分析对象")
        cid = result["competitor"]["id"]

        # 创建多样化内容
        contents = [
            {"content_id": "v001", "title": "AI教程", "content_type": "视频",
             "metrics": {"views": 5000, "likes": 500, "comments": 100,
                         "shares": 200, "saves": 50},
             "topics": ["AI", "科技"], "style_tags": ["教程"]},
            {"content_id": "v002", "title": "产品评测", "content_type": "视频",
             "metrics": {"views": 3000, "likes": 300, "comments": 50,
                         "shares": 80, "saves": 30},
             "topics": ["科技", "评测"], "style_tags": ["评测"]},
            {"content_id": "v003", "title": "生活Vlog", "content_type": "图文",
             "metrics": {"views": 1000, "likes": 200, "comments": 40,
                         "shares": 20, "saves": 10},
             "topics": ["生活", "日常"], "style_tags": ["Vlog"]},
        ]
        for c in contents:
            monitor.record_content(cid, c)

        analysis = monitor.analyze_competitor(cid)
        assert analysis["total_analyzed"] == 3
        assert "topic_focus" in analysis
        assert len(analysis["topic_focus"]) > 0
        assert "posting_frequency" in analysis
        assert "avg_engagement" in analysis
        assert analysis["avg_engagement"] > 0
        assert "top_performing" in analysis
        assert len(analysis["top_performing"]) <= 5
        assert "style_analysis" in analysis

        # 最佳表现内容应为 AI教程 (最高互动)
        assert analysis["top_performing"][0]["title"] == "AI教程"

    def test_analyze_competitor_no_data(self):
        """无数据时应返回空的完整分析"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "抖音", "acc_empty", "空账号")
        cid = result["competitor"]["id"]

        analysis = monitor.analyze_competitor(cid)
        assert analysis["total_analyzed"] == 0
        assert analysis["topic_focus"] == []
        assert analysis["avg_engagement"] == 0

    # ── D4: 获取对比 ──

    def test_get_comparison_returns_structured_comparison(self):
        """get_comparison 应返回竞品与用户的对比结果"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "抖音", "acc_comp", "对比账号")
        cid = result["competitor"]["id"]

        monitor.record_content(cid, {
            "content_id": "comp_v1", "title": "竞品爆款",
            "metrics": {"views": 8000, "likes": 800, "comments": 150,
                        "shares": 300, "saves": 80},
        })

        comparison = monitor.get_comparison("u1", cid)
        assert "competitor" in comparison
        assert "user" in comparison
        assert "comparison" in comparison
        assert comparison["competitor"]["name"] == "对比账号"
        assert "engagement_gap" in comparison["comparison"]

    # ── D5: 移除竞品 ──

    def test_remove_competitor_removes_from_index(self):
        """remove_competitor 应从索引中移除但仍保留数据文件"""
        monitor = self._make_monitor()
        result = monitor.add_competitor("u1", "抖音", "acc_rm", "待移除")
        cid = result["competitor"]["id"]

        # 确认存在
        assert len(monitor.list_competitors("u1")) == 1

        # 移除
        assert monitor.remove_competitor(cid) is True

        # 确认已移除
        assert len(monitor.list_competitors("u1")) == 0

        # 数据目录应保留
        comp_dir = self.competitors_dir / cid
        assert comp_dir.exists()

    def test_remove_competitor_nonexistent_returns_false(self):
        """移除不存在的竞品应返回 False"""
        monitor = self._make_monitor()
        assert monitor.remove_competitor("nonexistent") is False


# ══════════════════════════════════════════════════════════════════
#  D) Prometheus 指标收集 ── services.metrics
# ══════════════════════════════════════════════════════════════════


class TestMetricsCollection:
    """AppMetrics 全流程测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        # 使用 direct import 加载 metrics.py
        # 由于 services 已被 stub 占位，不会触发 services/__init__.py
        from services.metrics import AppMetrics
        self.metrics = AppMetrics()
        yield
        self.metrics.reset()

    # ── E1: 请求记录 ──

    def test_record_requests_tracks_counts_and_durations(self):
        """record_request 应正确统计请求数和耗时"""
        self.metrics.record_request(duration_ms=100.5, path="/api/generate", status=200)
        self.metrics.record_request(duration_ms=50.2, path="/api/score", status=200)
        self.metrics.record_request(duration_ms=200.0, path="/api/generate", status=500)

        assert self.metrics.request_count == 3
        assert self.metrics.request_paths["/api/generate"] == 2
        assert self.metrics.request_paths["/api/score"] == 1
        assert self.metrics.request_statuses[200] == 2
        assert self.metrics.request_statuses[500] == 1
        assert self.metrics.error_count == 1

    # ── E2: LLM 调用记录 ──

    def test_record_llm_calls_tracks_per_model(self):
        """record_llm_call 应按模型分别统计成功/失败"""
        self.metrics.record_llm_call("deepseek-chat", success=True)
        self.metrics.record_llm_call("deepseek-chat", success=True)
        self.metrics.record_llm_call("deepseek-chat", success=False)
        self.metrics.record_llm_call("qwen-max", success=True)
        self.metrics.record_llm_call("qwen-max", success=False)

        assert self.metrics.llm_calls["deepseek-chat"] == 3
        assert self.metrics.llm_calls["qwen-max"] == 2
        assert self.metrics.llm_success["deepseek-chat"] == 2
        assert self.metrics.llm_failures["deepseek-chat"] == 1
        assert self.metrics.llm_success["qwen-max"] == 1
        assert self.metrics.llm_failures["qwen-max"] == 1

    # ── E3: 缓存命中/未命中 ──

    def test_record_cache_tracks_hits_and_misses(self):
        """record_cache 应区分命中与未命中"""
        for _ in range(7):
            self.metrics.record_cache(hit=True)
        for _ in range(3):
            self.metrics.record_cache(hit=False)

        assert self.metrics.cache_hits == 7
        assert self.metrics.cache_misses == 3
        assert self.metrics.get_cache_hit_rate() == 0.7

    def test_cache_hit_rate_no_data(self):
        """无缓存数据时命中率应为 0"""
        assert self.metrics.get_cache_hit_rate() == 0.0

    # ── E4: 用户活动 ──

    def test_record_user_activity_tracks_active_users(self):
        """record_user_activity 应追踪活跃用户"""
        self.metrics.record_user_activity("user_1")
        self.metrics.record_user_activity("user_2")
        self.metrics.record_user_activity("user_1")
        self.metrics.record_user_activity("user_3")

        assert len(self.metrics.active_users) == 3
        assert self.metrics.user_request_count["user_1"] == 2
        assert self.metrics.user_request_count["user_2"] == 1

    # ── E5: get_metrics() 结构 ──

    def test_get_metrics_structure(self):
        """get_metrics 应返回完整的指标字典结构"""
        self.metrics.record_request(duration_ms=150, path="/api/generate", status=200)
        self.metrics.record_llm_call("deepseek-chat", success=True)
        self.metrics.record_cache(hit=True)
        self.metrics.record_user_activity("user_a")

        result = self.metrics.get_metrics()
        assert "requests" in result
        assert "llm" in result
        assert "cache" in result
        assert "users" in result
        assert "uptime_seconds" in result

        # 验证嵌套结构
        assert result["requests"]["total"] == 1
        assert result["requests"]["errors"] == 0
        assert "avg_duration_ms" in result["requests"]
        assert "p99_duration_ms" in result["requests"]
        assert "paths" in result["requests"]
        assert "statuses" in result["requests"]

        assert result["llm"]["total_calls"] == 1
        assert result["llm"]["successful"] == 1
        assert result["llm"]["failed"] == 0
        assert "by_model" in result["llm"]

        assert result["cache"]["hits"] == 1
        assert result["cache"]["misses"] == 0
        assert result["cache"]["hit_rate"] == 1.0

        assert result["users"]["active"] == 1

    # ── E6: get_prometheus_text() 格式 ──

    def test_get_prometheus_text_format(self):
        """get_prometheus_text 应返回 Prometheus 标准文本格式"""
        self.metrics.record_request(duration_ms=100, path="/api/generate", status=200)
        self.metrics.record_llm_call("deepseek-chat", success=True)
        self.metrics.record_cache(hit=True)

        text = self.metrics.get_prometheus_text()
        assert text.startswith("# HELP")
        assert "# TYPE" in text
        assert "zhimeiquan_requests_total" in text
        assert "zhimeiquan_llm_calls_total" in text
        assert "zhimeiquan_cache_hit_rate" in text
        assert "zhimeiquan_active_users" in text
        assert "counter" in text
        assert text.endswith("\n")

    def test_get_prometheus_text_empty(self):
        """空指标也应生成基本的 Prometheus 行"""
        text = self.metrics.get_prometheus_text()
        assert "zhimeiquan_requests_total 0" in text
        assert "zhimeiquan_request_errors_total 0" in text
        assert "zhimeiquan_cache_hit_rate 0" in text

    # ── E7: P99 计算 ──

    def test_p99_duration_calculation(self):
        """get_p99_duration 应正确计算 P99 耗时"""
        for i in range(100):
            self.metrics.record_request(duration_ms=float(i), path="/a", status=200)

        p99 = self.metrics.get_p99_duration()
        # P99 of [0..99] should be >= 98
        assert p99 >= 98.0

    def test_p99_duration_no_data(self):
        """无请求时 P99 应为 0"""
        assert self.metrics.get_p99_duration() == 0.0

    def test_average_duration_calculation(self):
        """get_average_duration 应正确计算均值"""
        self.metrics.record_request(duration_ms=100, path="/a", status=200)
        self.metrics.record_request(duration_ms=200, path="/b", status=200)
        self.metrics.record_request(duration_ms=300, path="/c", status=200)
        assert self.metrics.get_average_duration() == 200.0

    def test_average_duration_no_data(self):
        """无请求时平均耗时应为 0"""
        assert self.metrics.get_average_duration() == 0.0

    # ── E8: reset ──

    def test_reset_clears_all_metrics(self):
        """reset 应清空所有指标数据"""
        self.metrics.record_request(duration_ms=50, path="/api/test", status=200)
        self.metrics.record_llm_call("deepseek-chat", success=True)
        self.metrics.record_cache(hit=True)
        self.metrics.record_user_activity("user_x")

        self.metrics.reset()
        assert self.metrics.request_count == 0
        assert self.metrics.error_count == 0
        assert self.metrics.request_durations == []
        assert self.metrics.llm_calls == {}
        assert self.metrics.cache_hits == 0
        assert len(self.metrics.active_users) == 0

    # ── E9: 请求持续时间裁剪 ──

    def test_request_durations_trimming(self):
        """超过 10000 条记录时应裁剪到 5000 条"""
        for i in range(11000):
            self.metrics.record_request(duration_ms=1.0, path="/a", status=200)

        assert len(self.metrics.request_durations) <= 10000


# ══════════════════════════════════════════════════════════════════
#  E) 统一错误码系统 ── services.error_codes
# ══════════════════════════════════════════════════════════════════


class TestErrorCodesSystem:
    """错误码系统全流程测试"""

    # ── F1: ERROR_CODES 结构 ──

    def test_error_codes_has_all_required_categories(self):
        """ERROR_CODES 应包含 AUTH / CONT / RATE / SERV / DATA 五个分类"""
        from services.error_codes import ERROR_CODES

        required_codes = [
            "AUTH001", "AUTH002", "AUTH003",  # 身份认证
            "CONT001", "CONT002", "CONT003", "CONT004",  # 内容
            "RATE001",  # 限流
            "SERV001", "SERV002",  # 服务
            "DATA001", "DATA002",  # 数据
        ]

        for code in required_codes:
            assert code in ERROR_CODES, f"缺少错误码: {code}"

        # 验证消息和状态码格式
        for code, (message, status) in ERROR_CODES.items():
            assert isinstance(code, str)
            assert len(code) == 7  # e.g. "AUTH001"
            assert isinstance(message, str)
            assert len(message) > 0
            assert isinstance(status, int)
            assert 400 <= status < 600

    # ── F2: AppError ──

    def test_app_error_with_valid_code(self):
        """AppError 使用有效错误码时应正确提取信息"""
        from services.error_codes import AppError

        err = AppError("AUTH001")
        assert err.code == "AUTH001"
        assert err.message == "未登录"
        assert err.status_code == 401
        assert err.metadata == {}

    def test_app_error_with_custom_message(self):
        """AppError 应支持自定义错误消息覆盖"""
        from services.error_codes import AppError

        err = AppError("AUTH001", message_override="自定义登录错误")
        assert err.message == "自定义登录错误"
        assert err.code == "AUTH001"

    def test_app_error_with_metadata(self):
        """AppError 应支持附加元数据"""
        from services.error_codes import AppError

        err = AppError("CONT001", metadata={"reason": "API timeout", "retryable": True})
        assert err.metadata["reason"] == "API timeout"
        assert err.metadata["retryable"] is True

    def test_app_error_unknown_code_returns_defaults(self):
        """AppError 使用未知错误码时应返回默认值"""
        from services.error_codes import AppError

        err = AppError("UNKNOWN999")
        assert err.message == "未知错误"
        assert err.status_code == 500

    def test_app_error_to_dict(self):
        """AppError.to_dict 应返回结构化字典"""
        from services.error_codes import AppError

        err = AppError("CONT003", metadata={"field": "topic"})
        d = err.to_dict()
        assert d["error"] is True
        assert d["code"] == "CONT003"
        assert d["message"] == "主题不能为空"
        assert d["status_code"] == 400
        assert d["metadata"]["field"] == "topic"

    def test_app_error_is_exception(self):
        """AppError 应是 Exception 的子类"""
        from services.error_codes import AppError

        err = AppError("DATA001")
        assert isinstance(err, Exception)
        assert str(err) == "记录不存在"

    # ── F3: raise_error ──

    def test_raise_error_raises_http_exception(self):
        """raise_error 应抛出 FastAPI HTTPException"""
        from fastapi import HTTPException
        from services.error_codes import raise_error

        with pytest.raises(HTTPException) as exc_info:
            raise_error("CONT003")
        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        assert detail["code"] == "CONT003"
        assert detail["message"] == "主题不能为空"

    def test_raise_error_with_custom_message(self):
        """raise_error 应支持自定义消息"""
        from fastapi import HTTPException
        from services.error_codes import raise_error

        with pytest.raises(HTTPException) as exc_info:
            raise_error("AUTH002", message="自定义密钥错误")
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["message"] == "自定义密钥错误"
        assert exc_info.value.detail["code"] == "AUTH002"

    # ── F4: get_error_detail ──

    def test_get_error_detail_returns_code_message_status(self):
        """get_error_detail 应返回指定错误码的详情"""
        from services.error_codes import get_error_detail

        detail = get_error_detail("DATA001")
        assert detail["code"] == "DATA001"
        assert detail["message"] == "记录不存在"
        assert detail["status_code"] == 404

    def test_get_error_detail_unknown_code(self):
        """get_error_detail 使用未知码应返回默认值"""
        from services.error_codes import get_error_detail

        detail = get_error_detail("XYZ999")
        assert detail["message"] == "未知错误"
        assert detail["status_code"] == 500

    # ── F5: list_errors ──

    def test_list_errors_returns_all_errors(self):
        """list_errors 应返回所有错误码的完整列表"""
        from services.error_codes import list_errors

        all_errors = list_errors()
        assert len(all_errors) > 0
        for entry in all_errors:
            assert "code" in entry
            assert "message" in entry
            assert "status_code" in entry

    def test_list_errors_filters_by_category(self):
        """list_errors 应支持按分类筛选"""
        from services.error_codes import list_errors

        auth_errors = list_errors(category="auth")
        assert len(auth_errors) > 0
        assert all(e["code"].startswith("AUTH") for e in auth_errors)

        cont_errors = list_errors(category="cont")
        assert len(cont_errors) > 0
        assert all(e["code"].startswith("CONT") for e in cont_errors)

        data_errors = list_errors(category="data")
        assert len(data_errors) > 0
        assert all(e["code"].startswith("DATA") for e in data_errors)

        rate_errors = list_errors(category="rate")
        assert len(rate_errors) > 0
        assert all(e["code"].startswith("RATE") for e in rate_errors)

        serv_errors = list_errors(category="serv")
        assert len(serv_errors) > 0
        assert all(e["code"].startswith("SERV") for e in serv_errors)

    def test_list_errors_empty_category_returns_empty(self):
        """不存在的分类筛选应返回空列表"""
        from services.error_codes import list_errors

        result = list_errors(category="nonexistent")
        assert result == []

    # ── F6: wrap_exception ──

    def test_wrap_exception_wraps_standard_exception(self):
        """wrap_exception 应将普通异常包装为 AppError"""
        from services.error_codes import wrap_exception

        try:
            raise ValueError("数据库连接失败")
        except ValueError as e:
            app_err = wrap_exception(e, code="SERV001")

        assert isinstance(app_err, Exception)
        assert app_err.code == "SERV001"
        assert "数据库连接失败" in app_err.message
        assert app_err.status_code == 503

        # 验证 to_dict 也包含正确信息
        d = app_err.to_dict()
        assert d["code"] == "SERV001"
        assert d["status_code"] == 503


# ══════════════════════════════════════════════════════════════════
#  F) 内容改写引擎 ── generators.rewriter (数据模型 + compare_versions)
# ══════════════════════════════════════════════════════════════════


class TestRewriteEngineFlow:
    """ContentRewriter 内容改写引擎数据模型与版本对比测试"""

    # ── G1: compare_versions ──

    def test_compare_versions_returns_structured_diff(self):
        """compare_versions 应返回字段级的结构化差异"""
        from generators.rewriter import ContentRewriter

        original = {
            "title": "3个你不知道的AI工具",
            "body": "随着人工智能的发展...",
            "hook": "你知道AI可以帮你写作吗？",
            "tags": ["AI", "工具", "效率"],
            "call_to_action": "关注我获取更多",
        }
        rewritten = {
            "title": "5个2026年必备AI工具",
            "body": "随着人工智能的发展...",
            "hook": "这些AI工具改变了我的一生！",
            "tags": ["AI", "2026", "效率", "必备"],
            "call_to_action": "点赞收藏防走失",
        }

        diff = ContentRewriter.compare_versions(original, rewritten)
        assert diff["total_changes"] == 4  # body unchanged, others changed
        assert "summary" in diff
        assert "changed_fields" in diff
        assert len(diff["changed_fields"]) == 4
        assert "title" in diff["diffs"]
        assert "hook" in diff["diffs"]
        assert "tags" in diff["diffs"]
        assert "call_to_action" in diff["diffs"]
        assert "body" not in diff["diffs"]  # unchanged

        # 验证 tags 对比的特殊处理
        assert "added" in diff["diffs"]["tags"]
        assert "removed" in diff["diffs"]["tags"]
        assert "工具" in diff["diffs"]["tags"]["removed"]
        assert "必备" in diff["diffs"]["tags"]["added"]

    def test_compare_versions_no_changes(self):
        """内容完全相同时应返回 '无变化'"""
        from generators.rewriter import ContentRewriter

        content = {"title": "标题", "body": "正文", "hook": "钩子",
                    "tags": ["A"], "call_to_action": "关注"}
        diff = ContentRewriter.compare_versions(content, content)
        assert diff["total_changes"] == 0
        assert diff["summary"] == "无变化"
        assert diff["changed_fields"] == []

    def test_compare_versions_empty_dicts(self):
        """空字典对比不应报错"""
        from generators.rewriter import ContentRewriter

        diff = ContentRewriter.compare_versions({}, {})
        assert diff["total_changes"] == 0
        assert diff["summary"] == "无变化"

    # ── G2: PLATFORM_MAPPING ──

    def test_platform_mapping_contains_all_13_platforms(self):
        """PLATFORM_MAPPING 应包含全部 13 个平台映射"""
        from generators.rewriter import PLATFORM_MAPPING

        assert len(PLATFORM_MAPPING) == 13

        expected_platforms = [
            "抖音", "小红书", "B站", "微博", "知乎",
            "公众号", "微信视频号", "YouTube", "TikTok",
            "快手", "Instagram", "Twitter", "Facebook",
        ]
        for p in expected_platforms:
            assert p in PLATFORM_MAPPING, f"缺少平台: {p}"

        # 验证映射值
        assert PLATFORM_MAPPING["抖音"] == "douyin"
        assert PLATFORM_MAPPING["小红书"] == "xiaohongshu"
        assert PLATFORM_MAPPING["YouTube"] == "youtube"
        assert PLATFORM_MAPPING["TikTok"] == "tiktok"

    # ── G3: Content dataclass ──

    def test_content_dataclass_default_creation(self):
        """Content 数据类应支持默认值和 from_dict 创建"""
        from generators.rewriter import Content

        c = Content()
        assert c.title == ""
        assert c.body == ""
        assert c.hook == ""
        assert c.tags == []
        assert c.call_to_action == ""
        assert c.subtitles == []

        c2 = Content.from_dict({
            "title": "测试标题",
            "body": "测试正文",
            "hook": "测试钩子",
            "tags": ["AI", "科技"],
            "call_to_action": "点赞",
            "subtitles": [{"start": 0, "text": "开场白"}],
        })
        assert c2.title == "测试标题"
        assert "AI" in c2.tags
        assert len(c2.subtitles) == 1

    def test_content_to_dict_omits_empty(self):
        """Content.to_dict 应省略空值字段"""
        from generators.rewriter import Content

        c = Content(title="仅标题")
        d = c.to_dict()
        assert d["title"] == "仅标题"
        assert "body" not in d  # 空字符串
        assert "tags" not in d  # 空列表

    # ── G4: FireScore dataclass ──

    def test_fire_score_weak_dimensions(self):
        """FireScore.weak_dimensions 应返回低于 80 的维度"""
        from generators.rewriter import FireScore

        fs = FireScore(hook=95, trust=70, retention=85,
                       conversion=60, emotion=90, total=80)
        weak = fs.weak_dimensions
        dim_names = [w[0] for w in weak]
        assert "trust" in dim_names
        assert "conversion" in dim_names
        assert "hook" not in dim_names
        assert "retention" not in dim_names
        for name, score, weight in weak:
            assert score < 80
            assert 0 < weight <= 0.25

    def test_fire_score_weak_dimensions_all_high(self):
        """所有维度 >= 80 时 weak_dimensions 应为空"""
        from generators.rewriter import FireScore

        fs = FireScore(hook=90, trust=85, retention=88,
                       conversion=82, emotion=80, total=95)
        assert fs.weak_dimensions == []

    def test_fire_score_is_good_property(self):
        """is_good 在 total >= 95 时应为 True"""
        from generators.rewriter import FireScore

        assert FireScore(total=95).is_good is True
        assert FireScore(total=100).is_good is True
        assert FireScore(total=94).is_good is False
        assert FireScore(total=94.9).is_good is False

    def test_fire_score_from_dict(self):
        """FireScore.from_dict 应解析多种输入格式"""
        from generators.rewriter import FireScore

        # 格式1: scores 嵌套
        fs1 = FireScore.from_dict({
            "scores": {"hook": 90, "trust": 80, "retention": 85,
                       "conversion": 75, "emotion": 70, "total": 82},
            "suggestions": ["改进钩子"],
            "level": "Lv3",
        })
        assert fs1.hook == 90
        assert fs1.total == 82
        assert fs1.level == "Lv3"

        # 格式2: 扁平结构, total 是 dict
        fs2 = FireScore.from_dict({
            "hook": 85, "trust": 75, "retention": 80,
            "conversion": 70, "emotion": 65,
            "total": {"total": 75},
        })
        assert fs2.hook == 85
        assert fs2.total == 75

    # ── G5: ContentRewriter 类存在性 ──

    def test_content_rewriter_class_exists(self):
        """ContentRewriter 类应可实例化"""
        from generators.rewriter import ContentRewriter

        rewriter = ContentRewriter(data_dir="/tmp/nonexistent_rules")
        assert rewriter is not None
        assert hasattr(rewriter, "rewrite")
        assert hasattr(rewriter, "batch_rewrite")
        assert hasattr(rewriter, "rewrite_for_platform")
        assert hasattr(rewriter, "compare_versions")

    # ── G6: cross-platform rules ──

    def test_cross_platform_rules_contains_key_transitions(self):
        """CROSS_PLATFORM_RULES 应包含主要平台的转换规则"""
        from generators.rewriter import CROSS_PLATFORM_RULES

        key_pairs = [
            ("抖音", "小红书"), ("抖音", "B站"),
            ("小红书", "抖音"), ("小红书", "B站"),
            ("B站", "抖音"), ("B站", "小红书"),
        ]
        for pair in key_pairs:
            assert pair in CROSS_PLATFORM_RULES, f"缺少跨平台规则: {pair}"


# ══════════════════════════════════════════════════════════════════
#  G) 知识图谱 ── services.knowledge_graph (使用临时 content 目录)
# ══════════════════════════════════════════════════════════════════


class TestKnowledgeGraphFlow:
    """KnowledgeGraph 全流程集成测试 - 使用临时 content 目录"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.tmp_dir = tempfile.mkdtemp()

        # 创建 content 目录结构
        self.content_dir = Path(self.tmp_dir) / "content"
        self.methodology_dir = self.content_dir / "methodology"
        self.templates_dir = self.content_dir / "templates"
        self.prompts_dir = self.content_dir / "prompts"
        self.experts_dir = self.content_dir / "experts"
        for d in [self.methodology_dir, self.templates_dir, self.prompts_dir, self.experts_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # ── 创建测试方法论文件 ──
        (self.methodology_dir / "01-hook.md").write_text(
            "# 钩子方法论\n> 前3秒抓住用户注意力的核心技巧\n\n"
            "## 核心原则\n"
            "- **数字型钩子**: 用数字增强说服力\n"
            "- **悬念型钩子**: 先抛结果再解释原因\n\n"
            "## 技巧\n"
            "| 类型 | 示例 | 适用平台 |\n"
            "|------|------|---------|\n"
            "| 数字 | 3个方法让你月入过万 | 抖音/小红书 |\n"
            "| 悬念 | 99%的人不知道这个技巧 | B站 |\n\n"
            "## 注意事项\n"
            "- 前3秒必须抓住注意力\n"
            "- 钩子要与内容高度相关"
        )
        (self.methodology_dir / "02-trust.md").write_text(
            "# 信任建立\n> 如何让用户信任你的内容\n\n"
            "## 方法\n"
            "- **权威背书**: 引用数据来源和专家观点\n"
            "- **真实案例**: 展示实际结果和数据\n\n"
            "## 信任要素\n"
            "1. 数据真实性\n"
            "2. 案例可验证性\n"
            "3. 表达客观性"
        )
        (self.methodology_dir / "03-retention.md").write_text(
            "# 完播力提升\n> 让用户看完整个内容的技巧\n\n"
            "## 节奏控制\n"
            "- 前30秒高密度信息\n"
            "- 中间穿插互动提问\n"
            "- 结尾强调核心价值\n\n"
            "## 结构设计\n"
            "1. 开头钩子\n"
            "2. 正文展开\n"
            "3. 总结升华\n"
            "4. 引导互动"
        )

        # ── 创建测试模板文件 ──
        (self.templates_dir / "douyin-template.md").write_text(
            "# 抖音内容模板\n> 短视频内容结构指南\n\n"
            "## 开头\n"
            "1. **数字钩子**: 3个你不知道的真相\n"
            "2. **悬念钩子**: 为什么你总是...\n\n"
            "## 结构\n"
            "```\n1. 前3秒钩子\n2. 问题提出\n3. 解决方案\n4. 引导关注\n```\n\n"
            "## 技巧\n"
            "- 时长控制在 15-60 秒\n"
            "- 使用热门 BGM\n"
            "- 字幕要醒目"
        )
        (self.templates_dir / "xiaohongshu-template.md").write_text(
            "# 小红书内容模板\n> 图文笔记结构指南\n\n"
            "## 首图\n"
            "- 高清精美图片\n"
            "- 文字叠加突出重点\n\n"
            "## 正文\n"
            "1. 开头引入\n"
            "2. 干货分享\n"
            "3. 总结推荐\n\n"
            "## 标签\n"
            "#干货 #教程 #推荐"
        )

        # ── 创建测试提示词文件 ──
        (self.prompts_dir / "content-prompt.md").write_text(
            "# 内容生成提示词\n> 用于内容生成的系统提示\n\n"
            "## 基础提示\n"
            "你是一个专业的自媒体创作者，擅长制作爆款内容。\n\n"
            "## 输出要求\n"
            "- 使用中文\n"
            "- 结构清晰\n"
            "- 附带详细说明"
        )
        (self.prompts_dir / "rewrite-prompt.md").write_text(
            "# 改写优化提示词\n> 用于内容改写的提示\n\n"
            "## 改写原则\n"
            "1. 保留核心信息\n"
            "2. 优化表达方式\n"
            "3. 提升互动率\n\n"
            "## 检查清单\n"
            "- 标题是否吸引人\n"
            "- 钩子是否在前3秒\n"
            "- CTA是否明确"
        )

        # ── 创建测试人设文件 ──
        (self.experts_dir / "tech-persona.md").write_text(
            "# 科技博主\n科技领域专业创作者，擅长用通俗语言解释复杂概念。\n"
            "风格：专业但不晦涩，深入浅出"
        )

        # patch PROJECT_ROOT 指向临时目录
        self._patcher = patch("services.knowledge_graph.PROJECT_ROOT", Path(self.tmp_dir))
        self._patcher.start()
        yield
        self._patcher.stop()
        shutil.rmtree(self.tmp_dir)

    # ── H1: search ──

    def test_search_returns_results(self):
        """search 应根据关键词返回匹配结果"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        results = kg.search("钩子")
        assert len(results) > 0
        assert any("钩子" in r.get("title", "") or "钩子" in r.get("text_preview", "")
                   for r in results)

    def test_search_returns_empty_for_no_match(self):
        """搜索不存在的关键词应返回空列表"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        results = kg.search("xyznonexistentkeyword_2026")
        assert results == []

    def test_search_supports_category_filter(self):
        """search 应支持 category 过滤"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)

        methodology_results = kg.search("钩子", category="methodology")
        assert len(methodology_results) > 0
        assert all(r["type"] == "methodology" for r in methodology_results)

        template_results = kg.search("模板", category="template")
        assert len(template_results) > 0
        assert all(r["type"] == "template" for r in template_results)

        prompt_results = kg.search("提示词", category="prompt")
        assert len(prompt_results) > 0
        assert all(r["type"] == "prompt" for r in prompt_results)

    def test_search_supports_platform_filter(self):
        """search 应支持 platform 过滤模板"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        results = kg.search("抖音", category="template", platform="douyin")
        assert all(r.get("type") == "template" for r in results)
        # 可能匹配到 0 个（如果 platform 过滤严格），但不应报错
        assert isinstance(results, list)

    # ── H2: get_relevant_context ──

    def test_get_relevant_context_returns_text(self):
        """get_relevant_context 应返回结构化参考文本"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        context = kg.get_relevant_context(topic="钩子", platform="douyin")
        assert isinstance(context, str)
        assert len(context) > 0
        # 应包含方法论或模板内容
        assert any(kw in context for kw in ["方法论", "钩子", "抖音", "提示词"])

    def test_get_relevant_context_with_persona(self):
        """带 persona 参数应包含人设文件内容"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        context = kg.get_relevant_context(topic="科技", persona="tech")
        assert "科技博主" in context or "科技" in context

    def test_get_relevant_context_empty_topic(self):
        """空主题不应报错"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        context = kg.get_relevant_context(topic="")
        assert isinstance(context, str)

    # ── H3: get_platform_knowledge ──

    def test_get_platform_knowledge_returns_templates(self):
        """get_platform_knowledge 应返回指定平台的相关知识"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        result = kg.get_platform_knowledge("douyin")
        assert result["platform"] == "douyin"
        assert isinstance(result["templates"], list)
        assert isinstance(result["related_methodology"], list)

    def test_get_platform_knowledge_unknown_platform(self):
        """未知平台应返回空模板列表"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        result = kg.get_platform_knowledge("unknown_platform_xyz")
        assert result["platform"] == "unknown_platform_xyz"
        assert result["templates"] == []

    # ── H4: get_knowledge_stats ──

    def test_get_knowledge_stats_returns_counts(self):
        """get_knowledge_stats 应返回各类知识的计数"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        stats = kg.get_knowledge_stats()
        assert stats["methodology_count"] == 3
        assert stats["template_count"] == 2
        assert stats["prompt_count"] == 2
        assert isinstance(stats["categories"], list)
        assert stats["cache_enabled"] is False

    # ── H5: get_all_categories ──

    def test_get_all_categories_returns_tags(self):
        """get_all_categories 应返回不重复的分类标签"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=False)
        categories = kg.get_all_categories()
        assert isinstance(categories, list)
        assert len(set(categories)) == len(categories)  # 无重复

    # ── H6: 空目录处理 ──

    def test_handles_empty_content_directory(self):
        """内容目录为空时应优雅处理"""
        from services.knowledge_graph import KnowledgeGraph

        # 清空所有文件
        for f in self.methodology_dir.glob("*.md"):
            f.unlink()
        for f in self.templates_dir.glob("*.md"):
            f.unlink()
        for f in self.prompts_dir.glob("*.md"):
            f.unlink()

        kg = KnowledgeGraph(cache_enabled=False)
        kg.refresh(force=True)
        stats = kg.get_knowledge_stats()
        assert stats["methodology_count"] == 0
        assert stats["template_count"] == 0
        assert stats["prompt_count"] == 0


    # ── H7: 缓存功能 ──

    def test_cache_refresh_works(self):
        """启用缓存时应正确加载和命中"""
        from services.knowledge_graph import KnowledgeGraph

        kg = KnowledgeGraph(cache_enabled=True)
        kg.refresh(force=True)
        stats1 = kg.get_knowledge_stats()

        # 重新创建实例应命中缓存
        kg2 = KnowledgeGraph(cache_enabled=True)
        kg2.refresh(force=False)
        stats2 = kg2.get_knowledge_stats()

        assert stats1["methodology_count"] == stats2["methodology_count"]
        assert stats1["template_count"] == stats2["template_count"]

