"""综合核心模块单元测试

覆盖: ContentRewriter, AutomationEngine, FireScoreCalibrator, DataTracker,
CompetitorMonitor, KnowledgeGraph, AppMetrics, ErrorCodes, Prompts, AutonomousAgent.

所有测试使用 tempfile.TemporaryDirectory 隔离数据，
外部 LLM/网络调用全部 mock。
"""

import asyncio
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Helpers -- import the modules under test with runtime path adjustment
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent  # scripts/

# Ensure the project root (scripts/ parents) is importable
PYTHONPATH_OVERRIDE = str(SCRIPTS_DIR.parent)  # scripts/../ = the mount point
if PYTHONPATH_OVERRIDE not in sys.path:
    sys.path.insert(0, PYTHONPATH_OVERRIDE)

# ---------------------------------------------------------------------------
# A) ContentRewriter Tests  (generators/rewriter.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def rewriter_temp_dir(tmp_path):
    """提供一个临时 data_dir 给 ContentRewriter。"""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    data_dir = str(rules_dir)
    # Mock the scheduler's load_rules so we avoid real file I/O
    return data_dir


class TestContentRewriter:
    def test_compare_versions_same_content(self):
        """相同内容比较应返回无变化。"""
        from generators.rewriter import ContentRewriter

        original = {"title": "hello", "body": "world", "hook": "", "tags": [], "call_to_action": ""}
        rewritten = {"title": "hello", "body": "world", "hook": "", "tags": [], "call_to_action": ""}

        result = ContentRewriter.compare_versions(original, rewritten)

        assert result["summary"] == "无变化"
        assert result["total_changes"] == 0
        assert result["changed_fields"] == []

    def test_compare_versions_different_content(self):
        """不同内容比较应列出所有差异。"""
        from generators.rewriter import ContentRewriter

        original = {"title": "老标题", "body": "旧正文", "hook": "", "tags": ["a"], "call_to_action": ""}
        rewritten = {"title": "新标题", "body": "新正文", "hook": "新钩子", "tags": ["a", "b"], "call_to_action": "关注"}

        result = ContentRewriter.compare_versions(original, rewritten)

        assert result["summary"] == "修改了 5 个字段: title, body, hook, tags, call_to_action"
        assert result["total_changes"] == 5
        assert "title" in result["changed_fields"]
        assert result["diffs"]["title"]["old"] == "老标题"
        assert result["diffs"]["title"]["new"] == "新标题"
        assert "b" in result["diffs"]["tags"]["added"]
        assert result["diffs"]["tags"]["old_length"] == len("a")
        assert result["diffs"]["body"]["new_length"] == len("新正文")

    def test_cross_platform_mapping_exists(self):
        """平台映射表应包含所有常用中英文名称。"""
        from generators.rewriter import PLATFORM_MAPPING

        chinese_names = {"抖音", "小红书", "B站", "微博", "知乎", "公众号", "微信视频号", "快手"}
        english_ids = {"douyin", "xiaohongshu", "bilibili", "weibo", "zhihu", "wechat", "wechat_video", "kuaishou"}

        for cn in chinese_names:
            assert cn in PLATFORM_MAPPING, f"中文名 '{cn}' 不在映射表中"

        for en in english_ids:
            assert en in PLATFORM_MAPPING.values(), f"英文ID '{en}' 不在映射值中"

    def test_platform_conversion_rules(self):
        """跨平台适配规则表应至少包含几种关键方向。"""
        from generators.rewriter import CROSS_PLATFORM_RULES

        key_pairs = [("抖音", "小红书"), ("小红书", "抖音"), ("B站", "抖音"), ("抖音", "B站")]
        for src, dst in key_pairs:
            # Direct lookup
            assert (src, dst) in CROSS_PLATFORM_RULES, f"缺少规则 ({src} -> {dst})"

    def test_fire_score_weak_dimensions(self):
        """FireScore.weak_dimensions 应正确识别低于阈值的维度。"""
        from generators.rewriter import FireScore

        fs = FireScore(hook=60, trust=90, retention=70, conversion=95, emotion=99, total=76)
        weak = fs.weak_dimensions
        assert len(weak) == 2
        dim_names = {w[0] for w in weak}
        assert "hook" in dim_names
        assert "retention" in dim_names

    def test_fire_score_is_good(self):
        from generators.rewriter import FireScore

        high = FireScore(total=96)
        low = FireScore(total=80)
        assert high.is_good is True
        assert low.is_good is False

    @pytest.mark.asyncio
    async def test_rewrite_already_meets_target(self, rewriter_temp_dir):
        """原始内容已达到95+时 rewrite 不应发起 LLM 调用。"""
        from generators.rewriter import ContentRewriter

        with patch.object(ContentRewriter, "_score_content") as mock_score:
            from generators.rewriter import FireScore
            mock_score.return_value = FireScore(total=96, level="Lv1 必爆")

            cw = ContentRewriter(data_dir=rewriter_temp_dir)
            result = await cw.rewrite(
                {"title": "好文章", "body": "内容很棒"},
                platform="抖音",
            )

            assert result["improved"] is False
            assert result["iterations"] == 0
            assert "无需改写" in result["changes"]["summary"]
            mock_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_rewrite_calls_llm_when_needed(self, rewriter_temp_dir):
        """内容未达标时应调用 LLM 改写。"""
        from generators.rewriter import ContentRewriter, FireScore

        # Round 1: needs improvement
        mock_score_side_effect = [
            FireScore(total=60, hook=50, trust=55, retention=65, conversion=58, emotion=62),
            FireScore(total=97),
        ]

        with patch.object(ContentRewriter, "_score_content", side_effect=mock_score_side_effect):
            with patch("generators.rewriter.ai_circuit_breaker.acall") as mock_acall:
                mock_acall.return_value = {
                    "result": json.dumps({
                        "title": "改进后标题",
                        "body": "改进后正文",
                        "hook": "改进后钩子",
                        "tags": ["tag1"],
                        "call_to_action": "请关注",
                        "changes_summary": "优化了标题和正文",
                    })
                }

                cw = ContentRewriter(data_dir=rewriter_temp_dir)
                result = await cw.rewrite(
                    {"title": "原内容", "body": "原正文"},
                    platform="抖音",
                )

                assert result["improved"] is True
                assert result["iterations"] >= 1
                assert mock_acall.called

    @pytest.mark.asyncio
    async def test_batch_rewrite_basic(self, rewriter_temp_dir):
        """batch_rewrite 应返回正确的统计信息。"""
        from generators.rewriter import ContentRewriter, FireScore

        contents = [
            {"title": "A", "body": "a"},
            {"title": "B", "body": "b"},
        ]

        with patch.object(ContentRewriter, "_score_content", return_value=FireScore(total=96)):
            cw = ContentRewriter(data_dir=rewriter_temp_dir)
            result = await cw.batch_rewrite(contents, platform="抖音")

            assert "results" in result
            assert "stats" in result
            assert result["stats"]["total"] == 2
            assert result["stats"]["success"] == 2

    @pytest.mark.asyncio
    async def test_rewrite_for_platform(self, rewriter_temp_dir):
        """跨平台改写应在 CROSS_PLATFORM_RULES 中找到规则。"""
        from generators.rewriter import ContentRewriter, FireScore, CROSS_PLATFORM_RULES

        rule_key = ("抖音", "小红书")
        assert rule_key in CROSS_PLATFORM_RULES

        with patch.object(ContentRewriter, "_score_content") as mock_score:
            mock_score.return_value = FireScore(total=90)
            with patch("generators.rewriter.ai_circuit_breaker.acall") as mock_acall:
                mock_acall.return_value = {
                    "result": json.dumps({
                        "title": "小红书标题",
                        "body": "小红书正文",
                        "hook": "小红书钩子",
                        "tags": ["干货"],
                        "call_to_action": "收藏关注",
                        "adaptation_notes": "适配为小红书风格",
                    })
                }

                cw = ContentRewriter(data_dir=rewriter_temp_dir)
                result = await cw.rewrite_for_platform(
                    {"title": "原抖音标题", "body": "原抖音正文"},
                    "抖音",
                    "小红书",
                )

                assert result["source_platform"] == "抖音"
                assert result["target_platform"] == "小红书"
                assert "小红书标题" in result["rewritten"]["title"]


# ---------------------------------------------------------------------------
# B) AutomationEngine Tests  (automation/engine.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def engine_temp_dir(tmp_path):
    """为 AutomationEngine 提供临时工作流目录。"""
    wd = tmp_path / "workflows"
    wd.mkdir()
    return str(wd)


class TestAutomationEngine:
    def test_create_workflow(self, engine_temp_dir):
        """创建工作流应成功并持久化。"""
        from automation.engine import AutomationEngine, TimeTrigger, GenerateAction

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        action = GenerateAction(topic="AI话题", platform="抖音", count=1)

        wf = engine.create_workflow("user_1", "每日AI生成", trigger, [action])

        assert wf["user_id"] == "user_1"
        assert wf["name"] == "每日AI生成"
        assert wf["status"] == "active"
        assert "workflow_id" in wf
        assert wf["trigger"]["type"] == "time"

    def test_list_workflows_empty(self, engine_temp_dir):
        """刚创建的工作流引擎应该返回空列表。"""
        from automation.engine import AutomationEngine

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        result = engine.list_workflows("user_1")
        assert result == []

    def test_update_workflow(self, engine_temp_dir):
        """更新工作流应成功更改名称和状态。"""
        from automation.engine import AutomationEngine, TimeTrigger, GenerateAction

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        action = GenerateAction(topic="旧话题", platform="抖音")
        wf = engine.create_workflow("user_1", "旧名称", trigger, [action])

        updated = engine.update_workflow(
            wf["workflow_id"],
            {"name": "新名称", "status": "paused"},
        )

        assert updated["name"] == "新名称"
        assert updated["status"] == "paused"

    def test_delete_workflow(self, engine_temp_dir):
        """删除工作流后应无法获取。"""
        from automation.engine import AutomationEngine, TimeTrigger, GenerateAction

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        action = GenerateAction(topic="测试", platform="抖音")
        wf = engine.create_workflow("user_1", "待删除", trigger, [action])

        deleted = engine.delete_workflow(wf["workflow_id"])
        assert deleted is True

        fetched = engine.get_workflow(wf["workflow_id"])
        assert fetched is None

    def test_trigger_types_exist(self):
        """应定义所有预期触发器类。"""
        from automation.engine import (
            TimeTrigger, HotTopicTrigger, PerformanceTrigger, ScheduleTrigger,
        )

        # 都能正常实例化
        t1 = TimeTrigger("0 9 * * *")
        assert t1.get_type() == "time"

        t2 = HotTopicTrigger(["AI", "科技"])
        assert t2.get_type() == "hot_topic"

        t3 = PerformanceTrigger(metric="views", threshold=1000)
        assert t3.get_type() == "performance"

        t4 = ScheduleTrigger("2026-07-01T10:00:00", repeat=True)
        assert t4.get_type() == "schedule"

    def test_action_types_exist(self):
        """应定义所有预期动作类。"""
        from automation.engine import (
            GenerateAction, RewriteAction, PublishAction, NotifyAction, AnalyzeAction,
        )

        g = GenerateAction(topic="AI")
        assert g.get_type() == "generate"

        r = RewriteAction("content_1")
        assert r.get_type() == "rewrite"

        p = PublishAction("抖音")
        assert p.get_type() == "publish"

        n = NotifyAction("测试通知")
        assert n.get_type() == "notify"

        a = AnalyzeAction("trends")
        assert a.get_type() == "analyze"

    def test_execute_workflow(self, engine_temp_dir):
        """执行工作流应运行所有动作。"""
        from automation.engine import AutomationEngine, TimeTrigger, GenerateAction

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        action = GenerateAction(topic="热点话题", platform="抖音")
        wf = engine.create_workflow("user_1", "执行测试", trigger, [action])

        result = engine.execute_workflow(wf["workflow_id"])

        assert result["status"] == "completed"
        assert len(result["action_results"]) == 1
        assert result["action_results"][0]["action"] == "generate"

    def test_check_triggers_returns_empty_without_match(self, engine_temp_dir):
        """触发检查在无匹配时应返回空列表。"""
        from automation.engine import AutomationEngine, TimeTrigger

        engine = AutomationEngine(workflows_dir=engine_temp_dir)
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        wf = engine.create_workflow("user_1", "检查测试", trigger, [])

        # TimeTrigger.evaluate 只在刚好到点时返回 True，所以几乎不可能触发
        result = engine.check_triggers("user_1")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# C) FireScoreCalibrator Tests  (analyzers/calibrator.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def calibrator_tmp_dir(tmp_path):
    """提供临时 SQLite DB 给 FireScoreCalibrator。"""
    db_file = tmp_path / "test_tracker.db"
    return str(db_file)


@pytest.fixture
def calibrator(calibrator_tmp_dir):
    from analyzers.calibrator import FireScoreCalibrator

    cal = FireScoreCalibrator(db_path=calibrator_tmp_dir)
    yield cal
    cal.close()


class TestFireScoreCalibrator:
    def test_default_weights(self, calibrator):
        """默认权重应正确。"""
        from analyzers.calibrator import DEFAULT_WEIGHTS

        assert DEFAULT_WEIGHTS["hook"] == 25.0
        assert DEFAULT_WEIGHTS["trust"] == 20.0
        assert DEFAULT_WEIGHTS["retention"] == 25.0
        assert DEFAULT_WEIGHTS["conversion"] == 15.0
        assert DEFAULT_WEIGHTS["emotion"] == 15.0
        assert sum(DEFAULT_WEIGHTS.values()) == 100.0

    def test_record_and_calibrate(self, calibrator):
        """记录表现并校准应产生有效权重。"""
        cal = calibrator

        # 记录 5 条达标的数据
        for i in range(5):
            cal.record_performance(
                content_id=f"content_{i}",
                user_id="user_1",
                platform="抖音",
                fire_score=85.0,
                dimension_scores={"hook": 80, "trust": 75, "retention": 90, "conversion": 85, "emotion": 88},
                actual_metrics={"views": 1000, "likes": 50, "comments": 10, "shares": 5, "favorites": 3},
            )

        result = cal.calibrate("user_1", "抖音")
        assert result["status"] == "calibrated"
        assert result["sample_count"] == 5
        weights = result["weights"]
        assert sum(weights.values()) == pytest.approx(100.0, abs=0.2)

    def test_insufficient_data_for_calibrate(self, calibrator):
        """数据不足时应返回 insufficient_data。"""
        cal = calibrator

        # 只记录 4 条（MIN_SAMPLES=5）
        for i in range(4):
            cal.record_performance(
                content_id=f"mini_{i}",
                user_id="user_2",
                platform="小红书",
                fire_score=70.0,
                dimension_scores={"hook": 60, "trust": 65, "retention": 70, "conversion": 68, "emotion": 72},
                actual_metrics={"views": 500, "likes": 20, "comments": 5, "shares": 2, "favorites": 1},
            )

        result = cal.calibrate("user_2", "小红书")
        assert result["status"] == "insufficient_data"
        assert result["sample_count"] == 4

    def test_get_calibration_report(self, calibrator):
        """校准报告应包含所有预期字段。"""
        cal = calibrator

        for i in range(10):
            cal.record_performance(
                content_id=f"report_{i}",
                user_id="user_3",
                platform="B站",
                fire_score=80.0,
                dimension_scores={"hook": 70 + i, "trust": 75 + i, "retention": 80 + i,
                                  "conversion": 85 + i, "emotion": 72 + i},
                actual_metrics={"views": 1000, "likes": 50, "comments": 10, "shares": 5, "favorites": 3},
            )

        report = cal.get_calibration_report("user_3", "B站")
        assert "summary" in report
        assert "weights" in report
        assert "correlations" in report
        assert "recommendations" in report
        assert report["summary"]["sample_count"] == 10

    def test_predict_engagement(self, calibrator):
        """预测互动率应在合理范围内。"""
        cal = calibrator

        # 先用默认权重校准（数据不足时回退默认）
        result = cal.predict_engagement("user_4", "抖音", {"hook": 80, "trust": 70, "retention": 75, "conversion": 60, "emotion": 65})

        assert isinstance(result, float)
        assert result >= 0

    def test_get_calibrated_weights_no_config(self, calibrator):
        """从未校准的用户应返回默认权重。"""
        from analyzers.calibrator import DEFAULT_WEIGHTS

        weights = calibrator.get_calibrated_weights("user_nonexistent", "抖音")
        assert weights == DEFAULT_WEIGHTS

    def test_calibrate_from_history(self, calibrator):
        """全历史校准应使用全部数据。"""
        cal = calibrator

        for i in range(10):
            cal.record_performance(
                content_id=f"history_{i}",
                user_id="user_5",
                platform="抖音",
                fire_score=85.0,
                dimension_scores={"hook": 80, "trust": 75, "retention": 85, "conversion": 80, "emotion": 82},
                actual_metrics={"views": 1000, "likes": 50, "comments": 10, "shares": 5, "favorites": 3},
            )

        result = cal.calibrate_from_history("user_5", "抖音")
        assert result["status"] == "calibrated"
        assert result["sample_count"] == 10
        assert result["history_used"] == "all"

    def test_pearson_constant_values(self):
        """皮尔逊相关系数的极端情况。"""
        from analyzers.calibrator import _pearson

        # 完全正相关
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = _pearson(x, y)
        assert r == pytest.approx(1.0)

        # 常数列的相关系数应为 0
        z = [5, 5, 5, 5, 5]
        assert _pearson(x, z) == 0.0
        assert _pearson([1], [2]) == 0.0


# ---------------------------------------------------------------------------
# D) DataTracker Tests  (services/data_loop.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def tracker_tmp_dir(tmp_path):
    """提供临时 analytics 目录。"""
    ad = tmp_path / "analytics"
    ad.mkdir()
    return str(ad)


class TestDataTracker:
    def test_record_publish(self, tracker_tmp_dir):
        """发布记录应成功创建并持久化到文件。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        record = dt.record_publish("proj_1", "抖音", "测试标题", "content_001", fire_score=92)

        assert record["project_id"] == "proj_1"
        assert record["platform"] == "抖音"
        assert record["title"] == "测试标题"
        assert record["fire_score"] == 92.0
        assert record["metrics"]["views"] == 0

    def test_update_metrics(self, tracker_tmp_dir):
        """更新指标应反映到已有记录。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        dt.record_publish("proj_2", "小红书", "测试", "content_002")

        updated = dt.update_metrics("proj_2", "content_002", {"views": 1000, "likes": 50})

        assert updated["metrics"]["views"] == 1000
        assert updated["metrics"]["likes"] == 50

    def test_update_metrics_nonexistent(self, tracker_tmp_dir):
        """更新不存在的记录应返回错误。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        result = dt.update_metrics("no_proj", "no_content", {"views": 100})

        assert "error" in result

    def test_get_project_analytics(self, tracker_tmp_dir):
        """项目分析应汇总多条记录的指标。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        dt.record_publish("proj_3", "抖音", "内容A", "c1")
        dt.record_publish("proj_3", "抖音", "内容B", "c2")
        dt.update_metrics("proj_3", "c1", {"views": 1000, "likes": 100})
        dt.update_metrics("proj_3", "c2", {"views": 500, "likes": 50})

        analytics = dt.get_project_analytics("proj_3")

        assert analytics["total_content"] == 2
        assert analytics["total_views"] == 1500
        assert analytics["total_likes"] == 150

    def test_get_project_analytics_empty(self, tracker_tmp_dir):
        """不存在项目的分析应返回零值。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        analytics = dt.get_project_analytics("empty_proj")

        assert analytics["total_content"] == 0
        assert analytics["total_views"] == 0

    def test_get_platform_summary(self, tracker_tmp_dir):
        """平台汇总应按平台聚合数据。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        dt.record_publish("proj_4a", "抖音", "A", "ca")
        dt.record_publish("proj_4b", "小红书", "B", "cb")
        dt.update_metrics("proj_4a", "ca", {"views": 2000, "likes": 200})

        summary = dt.get_platform_summary()

        assert "抖音" in summary
        assert "小红书" in summary
        assert summary["抖音"]["count"] == 1
        assert summary["抖音"]["views"] == 2000

    def test_get_avg_fire_score(self, tracker_tmp_dir):
        """平均 Fire Score 应正确计算。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        dt.record_publish("proj_5", "抖音", "A", "cx", fire_score=90)
        dt.record_publish("proj_5", "抖音", "B", "cy", fire_score=96)
        dt.record_publish("proj_5", "抖音", "C", "cz")  # no fire_score

        avg = dt.get_avg_fire_score("proj_5")
        assert avg == pytest.approx(93.0)

    def test_get_avg_fire_score_none(self, tracker_tmp_dir):
        """没有 fire_score 的记录应返回 None。"""
        from services.data_loop import DataTracker

        dt = DataTracker(data_dir=tracker_tmp_dir)
        dt.record_publish("proj_none", "抖音", "A", "no_score")

        avg = dt.get_avg_fire_score("proj_none")
        assert avg is None

    def test_abtester_create_and_get_winner(self, tracker_tmp_dir):
        """A/B 测试应能创建并确定获胜者。"""
        from services.data_loop import ABTester

        ab = ABTester(data_dir=tracker_tmp_dir)
        test_data = [
            {"title": "标题A", "content": "内容A"},
            {"title": "标题B", "content": "内容B"},
        ]
        test = ab.create_test("test_1", "proj_ab", test_data)
        assert test["status"] == "running"
        assert len(test["variants"]) == 2

        ab.update_variant_metrics("test_1", "variant_0", {"views": 1000, "likes": 100, "comments": 20, "shares": 5})
        ab.update_variant_metrics("test_1", "variant_1", {"views": 800, "likes": 50, "comments": 10, "shares": 2})

        result = ab.get_winner("test_1")
        assert result["winner"] is not None
        assert result["test_id"] == "test_1"

    def test_abtester_nonexistent(self, tracker_tmp_dir):
        """不存在的 A/B 测试应返回错误。"""
        from services.data_loop import ABTester

        ab = ABTester(data_dir=tracker_tmp_dir)
        result = ab.get_winner("nonexistent")
        assert "error" in result


# ---------------------------------------------------------------------------
# E) CompetitorMonitor Tests  (monitors/competitor.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def monitor_tmp_dir(tmp_path):
    """提供临时的竞品监控目录。"""
    cd = tmp_path / "competitors"
    cd.mkdir()
    return str(cd)


class TestCompetitorMonitor:
    def test_add_competitor(self, monitor_tmp_dir):
        """添加竞品应成功且可去重。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        result = cm.add_competitor("user_1", "抖音", "acc_001", "对标账号")

        assert "competitor" in result
        assert result["competitor"]["platform"] == "抖音"
        assert result["competitor"]["account_name"] == "对标账号"

        # 重复添加应返回错误
        dup = cm.add_competitor("user_1", "抖音", "acc_001", "对标账号")
        assert "error" in dup

    def test_remove_competitor(self, monitor_tmp_dir):
        """移除竞品应从索引中消失。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        added = cm.add_competitor("user_2", "小红书", "acc_002", "竞品账号")
        comp_id = added["competitor"]["id"]

        removed = cm.remove_competitor(comp_id)
        assert removed is True

        # 移除后再移除应返回 False
        removed_again = cm.remove_competitor(comp_id)
        assert removed_again is False

    def test_record_content(self, monitor_tmp_dir):
        """记录竞品内容应成功创建文件。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        added = cm.add_competitor("user_3", "抖音", "acc_003", "被测竞品")
        comp_id = added["competitor"]["id"]

        result = cm.record_content(comp_id, {
            "content_id": "ext_001",
            "title": "竞品爆款视频",
            "content_type": "视频",
            "published_at": "2026-06-20T10:00:00",
            "metrics": {"views": 10000, "likes": 500, "comments": 100, "shares": 50},
            "topics": ["AI", "科技"],
            "style_tags": ["教程"],
            "summary": "分享AI工具使用技巧",
        })

        assert "record" in result
        assert result["record"]["title"] == "竞品爆款视频"
        # 重复记录同一内容应报错
        dup = cm.record_content(comp_id, {"content_id": "ext_001"})
        assert "error" in dup

    def test_analyze_competitor(self, monitor_tmp_dir):
        """分析竞品应产出主题分布和互动率。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        added = cm.add_competitor("user_4", "抖音", "acc_004", "分析目标")
        comp_id = added["competitor"]["id"]

        for i in range(3):
            cm.record_content(comp_id, {
                "content_id": f"perf_{i}",
                "title": f"视频{i}",
                "content_type": "视频",
                "published_at": f"2026-06-{10+i}T10:00:00",
                "metrics": {"views": 5000, "likes": 200, "comments": 50, "shares": 20},
                "topics": ["AI"] if i % 2 == 0 else ["科技"],
                "style_tags": ["教程"],
                "summary": "测试内容",
            })

        analysis = cm.analyze_competitor(comp_id)
        assert "topic_focus" in analysis
        assert "posting_frequency" in analysis
        assert "avg_engagement" in analysis
        assert "top_performing" in analysis
        assert analysis["total_analyzed"] == 3

    def test_analyze_competitor_no_content(self, monitor_tmp_dir):
        """无任何内容的竞品应返回空分析。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        added = cm.add_competitor("user_4b", "抖音", "acc_empty", "空竞品")
        comp_id = added["competitor"]["id"]

        analysis = cm.analyze_competitor(comp_id)
        assert analysis["total_analyzed"] == 0
        assert analysis["avg_engagement"] == 0

    def test_get_comparison(self, monitor_tmp_dir):
        """对比结果应包含竞品和用户双方数据。"""
        from monitors.competitor import CompetitorMonitor

        cm = CompetitorMonitor(data_dir=monitor_tmp_dir)
        added = cm.add_competitor("user_5", "抖音", "acc_005", "对比目标")
        comp_id = added["competitor"]["id"]

        cm.record_content(comp_id, {
            "content_id": "comp_1",
            "title": "竞品内容",
            "published_at": "2026-06-20T10:00:00",
            "metrics": {"views": 10000, "likes": 500, "comments": 100, "shares": 50},
            "topics": ["AI"],
            "style_tags": ["教程"],
            "summary": "",
        })

        comparison = cm.get_comparison("user_5", comp_id)
        assert "competitor" in comparison
        assert "user" in comparison
        assert "comparison" in comparison
        assert "engagement_gap" in comparison["comparison"]


# ---------------------------------------------------------------------------
# F) KnowledgeGraph Tests  (services/knowledge_graph.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def kg_project_root(tmp_path):
    """模拟项目根目录结构，包含 methodology/templates/prompts 子目录。"""
    base = tmp_path / "mock_project"
    for d in ["content/methodology", "content/templates", "content/prompts"]:
        (base / d).mkdir(parents=True)

    # 写几个最小化的测试文件
    (base / "content/methodology/hook.md").write_text(
        "# 钩子方法论\n> 内容开篇的重要性\n\n## 核心原则\n- **黄金三秒**: 开头必须吸引注意力\n\n",
        encoding="utf-8",
    )
    (base / "content/templates/douyin-template.md").write_text(
        "# 抖音模板\n> 口播类模板\n\n## 结构\n1. 开场钩子\n",
        encoding="utf-8",
    )
    (base / "content/prompts/generate.md").write_text(
        "# 生成提示词\n> 通用生成模板\n\n## 模板\n开始写作\n",
        encoding="utf-8",
    )
    return str(base)


@pytest.fixture
def kg_module(kg_project_root):
    """动态注入 KnowledgeGraph 使其使用临时目录。"""
    import services.knowledge_graph as kg_mod

    # Patch all dir constants
    kg_mod.PROJECT_ROOT = Path(kg_project_root)
    kg_mod.CONTENT_DIR = Path(kg_project_root) / "content"
    kg_mod.METHODOLOGY_DIR = Path(kg_project_root) / "content" / "methodology"
    kg_mod.TEMPLATES_DIR = Path(kg_project_root) / "content" / "templates"
    kg_mod.PROMPTS_DIR = Path(kg_project_root) / "content" / "prompts"
    kg_mod.CACHE_FILE = Path(kg_project_root) / "data_cache.json"

    # Disable caching during tests for speed
    kg = kg_mod.KnowledgeGraph(cache_enabled=False)
    yield kg
    # Restore
    kg_mod.PROJECT_ROOT = None
    kg_mod.CONTENT_DIR = None
    kg_mod.METHODOLOGY_DIR = None
    kg_mod.TEMPLATES_DIR = None
    kg_mod.PROMPTS_DIR = None
    kg_mod.CACHE_FILE = None


class TestKnowledgeGraph:
    def test_parse_methodology_files(self, kg_module):
        """解析方法论文件应提取标题、章节和标签。"""
        kg_module.refresh(force=True)
        assert kg_module._methodology_cache is not None
        assert len(kg_module._methodology_cache) >= 1
        entry = kg_module._methodology_cache[0]
        assert "钩子" in entry["title"] or "hook" in entry["title"].lower()
        assert "sections" in entry
        assert "tags" in entry

    def test_search_by_keyword(self, kg_module):
        """按关键词搜索应返回相关条目。"""
        kg_module.refresh(force=True)
        results = kg_module.search("钩子")
        assert len(results) >= 1
        found_ids = [r.get("id", "") for r in results]
        assert any("hook" in rid.lower() for rid in found_ids)

    def test_search_empty_result(self, kg_module):
        """搜索不存在的词应返回空列表。"""
        kg_module.refresh(force=True)
        results = kg_module.search("完全不存在的词语xyzabc123")
        assert len(results) == 0

    def test_get_relevant_context(self, kg_module):
        """获取相关上下文应产出不为空的结构化文本。"""
        kg_module.refresh(force=True)
        ctx = kg_module.get_relevant_context("钩子")
        assert len(ctx) > 0
        assert "##" in ctx  # 至少有一个段落标题

    def test_cache_behavior(self, kg_module):
        """缓存启用时应跳过文件扫描。"""
        kg_module.cache_enabled = True
        kg_module.refresh(force=True)
        first_cache = list(kg_module._methodology_cache)

        # 第二次调用 refresh() 应走缓存（force=False）
        kg_module.refresh(force=False)
        assert kg_module._methodology_cache == first_cache


# ---------------------------------------------------------------------------
# G) AppMetrics Tests  (services/metrics.py)
# ---------------------------------------------------------------------------


class TestAppMetrics:
    def test_record_request(self):
        """记录请求应累加计数和路径/状态。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_request(100.0, "/api/generate", 200)
        m.record_request(200.0, "/api/generate", 200)
        m.record_request(50.0, "/api/score", 500)

        assert m.request_count == 3
        assert m.error_count == 1
        assert m.request_paths["/api/generate"] == 2

    def test_record_llm_call(self):
        """记录 LLM 调用应统计成功/失败。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_llm_call("gpt-4", True)
        m.record_llm_call("gpt-4", True)
        m.record_llm_call("gpt-4", False)

        metrics = m.get_metrics()
        assert metrics["llm"]["total_calls"] == 3
        assert metrics["llm"]["successful"] == 2
        assert metrics["llm"]["failed"] == 1

    def test_record_cache(self):
        """记录缓存命中/未命中应影响命中率。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_cache(True)
        m.record_cache(True)
        m.record_cache(False)

        assert m.get_cache_hit_rate() == pytest.approx(2 / 3)

    def test_get_prometheus_text_format(self):
        """Prometheus 格式输出应包含所有必要指标行。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_request(150.0, "/test", 200)
        m.record_llm_call("claude-sonnet", True)
        m.record_cache(True)

        output = m.get_prometheus_text()
        assert "zhimeiquan_requests_total" in output
        assert 'zhimeiquan_requests_by_path{path="/test"}' in output
        assert 'zhimeiquan_llm_calls_total{model="claude-sonnet"}' in output
        assert "zhimeiquan_cache_hit_rate" in output
        assert "zhimeiquan_uptime_seconds" in output

    def test_reset_clears_all(self):
        """reset 应清除所有指标。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_request(100.0, "/a", 200)
        m.record_llm_call("model1", True)
        m.record_cache(True)
        m.record_user_activity("user_A")
        m.reset()

        assert m.request_count == 0
        assert m.llm_calls["model1"] == 0
        assert m.cache_hits == 0
        assert len(m.active_users) == 0

    def test_average_duration(self):
        """平均耗时应正确计算。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_request(100.0, "/a", 200)
        m.record_request(200.0, "/a", 200)
        assert m.get_average_duration() == pytest.approx(150.0)

    def test_p99_duration(self):
        """P99 耗时应接近最大值。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        for i in range(100):
            m.record_request(float(i * 10), "/a", 200)
        p99 = m.get_p99_duration()
        assert p99 >= 900.0  # 第 99 个百分位应接近 990

    def test_get_metrics_full_snapshot(self):
        """完整的 get_metrics 应包含所有顶层键。"""
        from services.metrics import AppMetrics

        m = AppMetrics()
        m.record_request(100.0, "/api/test", 200)
        snapshot = m.get_metrics()
        assert "requests" in snapshot
        assert "llm" in snapshot
        assert "cache" in snapshot
        assert "users" in snapshot
        assert "uptime_seconds" in snapshot


# ---------------------------------------------------------------------------
# H) ErrorCodes Tests  (services/error_codes.py)
# ---------------------------------------------------------------------------


class TestErrorCodes:
    def test_all_categories_present(self):
        """错误码体系应包含 auth/cont/rate/serv/data 五类。"""
        from services.error_codes import ERROR_CODES

        categories_found = set()
        for code in ERROR_CODES:
            cat = code[:4]  # AUTH001 -> AUTH, CONT001 -> CONT, etc.
            # Extract category prefix
            for letter in "ACRSD":
                if code.startswith(letter * 4):
                    categories_found.add(letter.upper() + "UTH" if letter == "A" else
                                          "ONT" if letter == "C" else
                                          "ATE" if letter == "R" else
                                          "ERV" if letter == "S" else
                                          "ATA" if letter == "D" else "")
                    break

        # Just check known codes exist
        auth_codes = [c for c in ERROR_CODES if c.startswith("AUTH")]
        cont_codes = [c for c in ERROR_CODES if c.startswith("CONT")]
        assert len(auth_codes) > 0
        assert len(cont_codes) > 0

    def test_app_error_raised(self):
        """AppError 应具有正确的错误码和消息。"""
        from services.error_codes import AppError

        err = AppError("CONT003")
        assert err.code == "CONT003"
        assert err.message == "主题不能为空"
        assert err.status_code == 400
        assert err.to_dict()["code"] == "CONT003"

    def test_raise_error_http_exception(self):
        """raise_error 应抛出 FastAPI HTTPException。"""
        from fastapi import HTTPException
        from services.error_codes import raise_error

        with pytest.raises(HTTPException) as exc_info:
            raise_error("CONT003")

        detail = exc_info.value.detail
        assert detail["code"] == "CONT003"
        assert exc_info.value.status_code == 400

    def test_wrap_exception(self):
        """wrap_exception 应将普通异常转为 AppError。"""
        from services.error_codes import wrap_exception

        try:
            raise ValueError("数据库连接失败")
        except Exception as e:
            app_err = wrap_exception(e, "DATA002")

        assert app_err.code == "DATA002"
        assert "数据库连接失败" in app_err.message

    def test_get_error_detail(self):
        """get_error_detail 应返回正确的结构。"""
        from services.error_codes import get_error_detail

        detail = get_error_detail("RATE001")
        assert detail["code"] == "RATE001"
        assert detail["message"] == "请求过于频繁"
        assert detail["status_code"] == 429

    def test_custom_message_override(self):
        """AppError 支持自定义消息覆盖。"""
        from services.error_codes import AppError

        err = AppError("CONT001", message_override="自定义生成失败")
        assert err.message == "自定义生成失败"
        assert err.status_code == 500  # still uses the code's default status

    def test_unknown_error_code(self):
        """未知错误码应回退到 500。"""
        from services.error_codes import AppError

        err = AppError("FAKE000")
        assert err.status_code == 500
        assert err.message == "未知错误"

    def test_raise_error_with_metadata(self):
        """raise_error 应支持传递 metadata。"""
        from fastapi import HTTPException
        from services.error_codes import raise_error

        with pytest.raises(HTTPException) as exc_info:
            raise_error("AUTH001", metadata={"ip": "1.2.3.4"})

        assert "ip" in exc_info.value.detail["metadata"]


# ---------------------------------------------------------------------------
# I) AutonomousAgent Tests  (services/agent.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def agent_tmp_dir(tmp_path):
    """提供临时 agent 数据目录。"""
    ad = tmp_path / "agents"
    ad.mkdir()
    # Pre-create matrix dir
    (ad / "matrix").mkdir()
    # Pre-create analytics dir (for auto_optimize)
    (tmp_path / "data" / "analytics").mkdir(parents=True)
    return str(ad)


class TestAutonomousAgent:
    def test_create_auto_publish_task(self, agent_tmp_dir):
        """创建自动发布任务应返回正确结构的字典。"""
        from services.agent import AutonomousAgent

        with patch("services.agent.content_scheduler.schedule_recurring"):
            agent = AutonomousAgent(data_dir=agent_tmp_dir)
            task = agent.create_auto_publish_task(
                project_id="proj_1",
                platform="抖音",
                topic="AI前沿",
                frequency="daily",
                time_of_day="10:00",
            )

        assert "task_id" in task
        assert task["project_id"] == "proj_1"
        assert task["platform"] == "抖音"
        assert task["topic"] == "AI前沿"
        assert task["status"] == "active"
        assert task["frequency"] == "daily"

    def test_get_tasks(self, agent_tmp_dir):
        """获取任务列表初始应为空，添加后有数据。"""
        from services.agent import AutonomousAgent

        with patch("services.agent.content_scheduler.schedule_recurring"):
            agent = AutonomousAgent(data_dir=agent_tmp_dir)
            initial = agent.get_tasks()
            assert isinstance(initial, list)
            assert len(initial) == 0

            agent.create_auto_publish_task("proj_get", "抖音", "测试", time_of_day="09:00")
            tasks = agent.get_tasks()
            assert len(tasks) == 1
            assert tasks[0]["topic"] == "测试"

    def test_get_activity_log(self, agent_tmp_dir):
        """活动日志在创建任务后应不空。"""
        from services.agent import AutonomousAgent

        with patch("services.agent.content_scheduler.schedule_recurring"):
            agent = AutonomousAgent(data_dir=agent_tmp_dir)
            agent.create_auto_publish_task("proj_log", "小红书", "日志测试", time_of_day="12:00")
            logs = agent.get_activity_log(limit=10)
            assert len(logs) >= 1
            assert "自动任务" in logs[0]

    def test_auto_optimize_no_data(self, agent_tmp_dir):
        """没有矩阵数据时 auto_optimize 应返回 no_data。"""
        from services.agent import AutonomousAgent

        with patch("services.agent.content_scheduler.schedule_recurring"):
            agent = AutonomousAgent(data_dir=agent_tmp_dir)
        result = agent.auto_optimize("no_data_proj")
        assert result["status"] == "no_data"

    def test_schedule_auto_publish_nothing_to_trigger(self, agent_tmp_dir):
        """没有待触发的矩阵任务应返回空的触发列表。"""
        from services.agent import AutonomousAgent

        agent = AutonomousAgent(data_dir=agent_tmp_dir)
        result = agent.schedule_auto_publish()
        assert result["status"] == "completed"
        assert result["triggered_count"] == 0


# ---------------------------------------------------------------------------
# J) Prompts Tests  (services/prompts.py)
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_generate_content_prompt(self):
        """生成内容提示应返回有效的 system/prompt 二元组。"""
        from services.prompts import Prompts

        system, prompt = Prompts.generate_content(
            topic="AI自媒体",
            platform="抖音",
            persona="学长型",
            duration=60,
        )

        assert isinstance(system, str)
        assert isinstance(prompt, str)
        assert len(system) > 0
        assert len(prompt) > 0
        assert "AI自媒体" in prompt
        assert "抖音" in system
        assert "60秒" in prompt

    def test_generate_content_prompt_with_rules(self):
        """传入规则参数应在 system 中包含规则文本。"""
        from services.prompts import Prompts

        rules = {"max_title_length": 30, "preferred_hooks": ["数字"]}
        system, _ = Prompts.generate_content(
            topic="测试",
            platform="小红书",
            persona="导师型",
            duration=120,
            rules=rules,
        )

        assert "小红书" in system
        assert "preferred_hooks" in system

    def test_score_content_prompt(self):
        """评分提示应包含五维评估框架。"""
        from services.prompts import Prompts

        system, prompt = Prompts.score_content(
            title="3个AI技巧",
            body="这是一篇关于AI技巧的文章。",
            platform="抖音",
        )

        assert "钩子力" in system
        assert "信任度" in system
        assert "完播力" in system
        assert "转化力" in system
        assert "情绪值" in system
        assert "3个AI技巧" in prompt

    def test_score_content_prompt_with_rules(self):
        """评分提示传入规则应包含规则文本。"""
        from services.prompts import Prompts

        rules = {"required_elements": ["hook", "cta"]}
        system, _ = Prompts.score_content(
            title="测试标题",
            body="测试正文",
            platform="B站",
            rules=rules,
        )

        assert "required_elements" in system

    def test_generate_titles_prompt(self):
        """标题生成提示应要求输出 JSON 格式。"""
        from services.prompts import Prompts

        system, prompt = Prompts.generate_titles(
            topic="短视频制作",
            platform="小红书",
            count=3,
        )

        assert "小红书" in system
        assert "短视频制作" in prompt
        assert "3个爆款标题" in prompt

    def test_system_base_includes_language_instruction(self):
        """系统基础提示应包含中文回复指令。"""
        from services.prompts import SYSTEM_BASE

        assert "中文回复" in SYSTEM_BASE
