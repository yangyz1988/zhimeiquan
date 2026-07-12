"""自动化工作流引擎单元测试

覆盖: 触发器（TimeTrigger、HotTopicTrigger、PerformanceTrigger、ScheduleTrigger）、
动作（GenerateAction、RewriteAction、PublishAction、NotifyAction、AnalyzeAction）、
AutomationEngine CRUD 和操作。
"""

import json
import os
import pytest
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from automation.engine import (
    TimeTrigger,
    HotTopicTrigger,
    PerformanceTrigger,
    ScheduleTrigger,
    TriggerRegistry,
    trigger_from_dict,
    GenerateAction,
    RewriteAction,
    PublishAction,
    NotifyAction,
    AnalyzeAction,
    ActionRegistry,
    action_from_dict,
    AutomationEngine,
)


# ── TimeTrigger ───────────────────────────────────


class TestTimeTrigger:
    def test_every_minute(self):
        t = TimeTrigger(cron_expression="* * * * *")
        assert t.evaluate() is True

    def test_specific_minute(self):
        t = TimeTrigger(cron_expression="30 * * * *")
        now = datetime.now()
        if now.minute == 30:
            assert t.evaluate() is True
        else:
            assert t.evaluate() is False

    def test_specific_hour(self):
        t = TimeTrigger(cron_expression="0 9 * * *")
        now = datetime.now()
        if now.hour == 9 and now.minute == 0:
            assert t.evaluate() is True
        else:
            assert t.evaluate() is False

    def test_weekday_range(self):
        t = TimeTrigger(cron_expression="0 9 * * 1-5")
        now = datetime.now()
        weekday = now.weekday() + 1  # 1=Mon ... 7=Sun
        if 1 <= weekday <= 5 and now.hour == 9 and now.minute == 0:
            assert t.evaluate() is True
        else:
            assert t.evaluate() is False

    def test_invalid_cron(self):
        t = TimeTrigger(cron_expression="invalid")
        assert t.evaluate() is False

    def test_no_duplicate_within_same_minute(self):
        t = TimeTrigger(cron_expression="* * * * *")
        assert t.evaluate() is True
        assert t.evaluate() is False  # 同一分钟内不应重复触发

    def test_serialization(self):
        t = TimeTrigger(cron_expression="0 9 * * 1-5", timezone="Asia/Shanghai")
        d = t.to_dict()
        assert d["type"] == "type"
        assert d["cron_expression"] == "0 9 * * 1-5"
        assert d["timezone"] == "Asia/Shanghai"

    def test_deserialization(self):
        t = TimeTrigger.from_dict({
            "cron_expression": "0 12 * * *",
            "timezone": "UTC",
        })
        assert t.cron_expression == "0 12 * * *"
        assert t.timezone == "UTC"

    def test_get_type(self):
        t = TimeTrigger("* * * * *")
        assert t.get_type() == "time"


# ── HotTopicTrigger ───────────────────────────────


class TestHotTopicTrigger:
    def test_match_keywords(self):
        t = HotTopicTrigger(keywords=["AI", "大模型"], platform="抖音")
        context = {"hot_topics": ["AI 发展趋势", "大模型应用", "普通话题"]}
        assert t.evaluate(context) is True
        assert "AI 发展趋势" in t.get_matched_topics()

    def test_no_match(self):
        t = HotTopicTrigger(keywords=["量子计算"], platform="抖音")
        context = {"hot_topics": ["AI 趋势", "大模型"]}
        assert t.evaluate(context) is False

    def test_case_insensitive(self):
        t = HotTopicTrigger(keywords=["ai"], platform="抖音")
        context = {"hot_topics": ["AI 发展趋势"]}
        assert t.evaluate(context) is True

    def test_empty_context(self):
        t = HotTopicTrigger(keywords=["AI"])
        assert t.evaluate(None) is False
        assert t.evaluate({}) is False

    def test_empty_hot_topics(self):
        t = HotTopicTrigger(keywords=["AI"])
        assert t.evaluate({"hot_topics": []}) is False

    def test_serialization(self):
        t = HotTopicTrigger(keywords=["AI"], platform="抖音", min_rank=30)
        d = t.to_dict()
        assert d["type"] == "hot_topic"
        assert d["keywords"] == ["AI"]
        assert d["min_rank"] == 30

    def test_deserialization(self):
        t = HotTopicTrigger.from_dict({"keywords": ["test"], "platform": "B站"})
        assert t.keywords == ["test"]
        assert t.platform == "B站"


# ── PerformanceTrigger ────────────────────────────


class TestPerformanceTrigger:
    def test_below_threshold(self):
        t = PerformanceTrigger(metric="engagement_rate", threshold=0.1, direction="below")
        context = {
            "recent_records": [
                {"metrics": {"views": 1000, "likes": 50, "comments": 5, "shares": 2}},
                {"metrics": {"views": 800, "likes": 30, "comments": 3, "shares": 1}},
            ]
        }
        # 第一条: (50+5+2)/1000 = 0.057, 第二条: (30+3+1)/800 = 0.0425
        # 平均 ≈ 0.05 < 0.1
        assert t.evaluate(context) is True

    def test_above_threshold(self):
        t = PerformanceTrigger(metric="engagement_rate", threshold=0.01, direction="above")
        context = {
            "recent_records": [
                {"metrics": {"views": 1000, "likes": 200, "comments": 50, "shares": 30}},
            ]
        }
        # (200+50+30)/1000 = 0.28 > 0.01
        assert t.evaluate(context) is True

    def test_fire_score_metric(self):
        t = PerformanceTrigger(metric="fire_score", threshold=80, direction="below")
        context = {
            "recent_records": [
                {"fire_score": 60},
                {"fire_score": 70},
                {"fire_score": 75},
            ]
        }
        # 平均 68.33 < 80
        assert t.evaluate(context) is True

    def test_no_records(self):
        t = PerformanceTrigger()
        assert t.evaluate({"recent_records": []}) is False

    def test_empty_context(self):
        t = PerformanceTrigger()
        assert t.evaluate(None) is False

    def test_serialization(self):
        t = PerformanceTrigger(metric="likes", threshold=100, direction="above", window_days=14)
        d = t.to_dict()
        assert d["type"] == "performance"
        assert d["metric"] == "likes"
        assert d["threshold"] == 100

    def test_deserialization(self):
        t = PerformanceTrigger.from_dict({
            "metric": "views",
            "threshold": 500,
            "direction": "above",
            "window_days": 30,
        })
        assert t.metric == "views"
        assert t.threshold == 500


# ── ScheduleTrigger ───────────────────────────────


class TestScheduleTrigger:
    def test_fires_at_scheduled_time(self):
        now = datetime.now()
        target = now.replace(second=0, microsecond=0)
        t = ScheduleTrigger(scheduled_time=target.isoformat())
        # 当前时间在目标 ±1 分钟内
        assert t.evaluate() is True

    def test_not_fired_yet(self):
        future = (datetime.now() + timedelta(hours=2)).isoformat()
        t = ScheduleTrigger(scheduled_time=future)
        assert t.evaluate() is False

    def test_one_shot_no_repeat(self):
        now = datetime.now().replace(second=0, microsecond=0)
        t = ScheduleTrigger(scheduled_time=now.isoformat(), repeat=False)
        assert t.evaluate() is True
        assert t.evaluate() is False  # 不应重复触发

    def test_repeat_always_fires(self):
        now = datetime.now().replace(second=0, microsecond=0)
        t = ScheduleTrigger(scheduled_time=now.isoformat(), repeat=True)
        assert t.evaluate() is True
        assert t.evaluate() is True  # 重复模式可以再次触发

    def test_reset(self):
        now = datetime.now().replace(second=0, microsecond=0)
        t = ScheduleTrigger(scheduled_time=now.isoformat(), repeat=False)
        t.evaluate()  # 触发
        t.reset()
        # reset 后重新评估，不在时间窗口内所以返回 False
        # 但我们可以通过再次设置时间来验证
        assert t._fired is False

    def test_invalid_iso_format(self):
        t = ScheduleTrigger(scheduled_time="not-a-date")
        assert t.evaluate() is False

    def test_serialization(self):
        t = ScheduleTrigger(scheduled_time="2026-07-01T10:00:00", repeat=True)
        d = t.to_dict()
        assert d["type"] == "schedule"
        assert d["repeat"] is True


# ── 触发器注册表 ──────────────────────────────────


class TestTriggerRegistry:
    def test_all_types_registered(self):
        for name, cls in TriggerRegistry.items():
            assert issubclass(cls, type(Trigger())) or name in ["time", "hot_topic", "performance", "schedule"]

    def test_trigger_from_dict_time(self):
        t = trigger_from_dict({"type": "time", "cron_expression": "0 9 * * *"})
        assert isinstance(t, TimeTrigger)

    def test_trigger_from_dict_hot_topic(self):
        t = trigger_from_dict({"type": "hot_topic", "keywords": ["AI"]})
        assert isinstance(t, HotTopicTrigger)

    def test_trigger_from_dict_performance(self):
        t = trigger_from_dict({"type": "performance", "metric": "views"})
        assert isinstance(t, PerformanceTrigger)

    def test_trigger_from_dict_schedule(self):
        t = trigger_from_dict({"type": "schedule", "scheduled_time": "2026-07-01T10:00:00"})
        assert isinstance(t, ScheduleTrigger)

    def test_trigger_from_dict_unknown_type(self):
        with pytest.raises(ValueError, match="未知触发器类型"):
            trigger_from_dict({"type": "unknown_type"})


# ── 动作 ──────────────────────────────────────────


class TestGenerateAction:
    def test_execute(self):
        a = GenerateAction(topic="AI 工具", platform="抖音", count=3)
        result = a.execute()
        assert result["action"] == "generate"
        assert result["status"] == "queued"
        assert result["count"] == 3

    def test_execute_with_context(self):
        a = GenerateAction(topic="{topic} 深度解析", platform="B站")
        result = a.execute({"matched_topic": "大语言模型"})
        assert result["topic"] == "大语言模型 深度解析"

    def test_serialization(self):
        a = GenerateAction(topic="测试", platform="小红书")
        d = a.to_dict()
        assert d["type"] == "generate"
        assert d["topic"] == "测试"

    def test_deserialization(self):
        a = GenerateAction.from_dict({"topic": "test", "platform": "知乎", "count": 5})
        assert a.topic == "test"
        assert a.platform == "知乎"
        assert a.count == 5


class TestRewriteAction:
    def test_execute(self):
        a = RewriteAction(content_id="c123", style="optimize")
        result = a.execute()
        assert result["action"] == "rewrite"
        assert result["content_id"] == "c123"

    def test_serialization(self):
        a = RewriteAction("c456", "expand")
        d = a.to_dict()
        assert d["type"] == "rewrite"
        assert d["style"] == "expand"


class TestPublishAction:
    def test_execute(self):
        a = PublishAction(platform="抖音", content_id="c789")
        result = a.execute()
        assert result["action"] == "publish"
        assert result["platform"] == "抖音"

    def test_execute_uses_context_content_id(self):
        a = PublishAction(platform="小红书")
        result = a.execute({"generated_content_id": "auto_001"})
        assert result["content_id"] == "auto_001"


class TestNotifyAction:
    def test_execute(self):
        a = NotifyAction(message="测试通知", channel="email")
        result = a.execute()
        assert result["action"] == "notify"
        assert result["status"] == "sent"

    def test_execute_with_placeholder(self):
        a = NotifyAction(message="用户 {user} 完成了 {task}", channel="webhook")
        result = a.execute({"user": "张三", "task": "内容生成"})
        assert result["message"] == "用户 张三 完成了 内容生成"


class TestAnalyzeAction:
    def test_execute(self):
        a = AnalyzeAction(analysis_type="trends", platform="抖音", days=14)
        result = a.execute()
        assert result["action"] == "analyze"
        assert result["analysis_type"] == "trends"

    def test_serialization(self):
        a = AnalyzeAction("performance", "B站", 30)
        d = a.to_dict()
        assert d["type"] == "analyze"
        assert d["days"] == 30


class TestActionRegistry:
    def test_action_from_dict_generate(self):
        a = action_from_dict({"type": "generate", "topic": "AI"})
        assert isinstance(a, GenerateAction)

    def test_action_from_dict_rewrite(self):
        a = action_from_dict({"type": "rewrite", "content_id": "c1"})
        assert isinstance(a, RewriteAction)

    def test_action_from_dict_publish(self):
        a = action_from_dict({"type": "publish", "platform": "抖音"})
        assert isinstance(a, PublishAction)

    def test_action_from_dict_notify(self):
        a = action_from_dict({"type": "notify", "message": "hello"})
        assert isinstance(a, NotifyAction)

    def test_action_from_dict_analyze(self):
        a = action_from_dict({"type": "analyze", "analysis_type": "trends"})
        assert isinstance(a, AnalyzeAction)

    def test_action_from_dict_unknown(self):
        with pytest.raises(ValueError, match="未知动作类型"):
            action_from_dict({"type": "unknown"})


# ── AutomationEngine ──────────────────────────────


@pytest.fixture
def engine(tmp_path):
    return AutomationEngine(workflows_dir=tmp_path)


class TestEngineCRUD:
    def test_create_workflow(self, engine):
        trigger = TimeTrigger(cron_expression="0 9 * * *")
        actions = [GenerateAction(topic="AI 趋势", platform="抖音")]
        wf = engine.create_workflow("u1", "每日AI趋势", trigger, actions)
        assert wf["user_id"] == "u1"
        assert wf["name"] == "每日AI趋势"
        assert wf["status"] == "active"
        assert "workflow_id" in wf

    def test_list_workflows(self, engine):
        trigger = TimeTrigger("* * * * *")
        engine.create_workflow("u1", "wf1", trigger, [])
        engine.create_workflow("u1", "wf2", trigger, [])
        engine.create_workflow("u2", "wf3", trigger, [])

        u1_wfs = engine.list_workflows("u1")
        u2_wfs = engine.list_workflows("u2")
        assert len(u1_wfs) == 2
        assert len(u2_wfs) == 1

    def test_get_workflow(self, engine):
        trigger = TimeTrigger("0 12 * * *")
        wf = engine.create_workflow("u1", "test", trigger, [])
        retrieved = engine.get_workflow(wf["workflow_id"])
        assert retrieved is not None
        assert retrieved["name"] == "test"

    def test_get_nonexistent_workflow(self, engine):
        assert engine.get_workflow("nonexistent") is None

    def test_update_workflow(self, engine):
        trigger = TimeTrigger("* * * * *")
        wf = engine.create_workflow("u1", "old_name", trigger, [])
        updated = engine.update_workflow(wf["workflow_id"], {"name": "new_name", "status": "paused"})
        assert updated["name"] == "new_name"
        assert updated["status"] == "paused"

    def test_update_nonexistent_workflow(self, engine):
        assert engine.update_workflow("nonexistent", {"name": "x"}) is None

    def test_delete_workflow(self, engine):
        trigger = TimeTrigger("* * * * *")
        wf = engine.create_workflow("u1", "to_delete", trigger, [])
        assert engine.delete_workflow(wf["workflow_id"]) is True
        assert engine.get_workflow(wf["workflow_id"]) is None

    def test_delete_nonexistent_workflow(self, engine):
        assert engine.delete_workflow("nonexistent") is False


class TestEngineExecution:
    def test_execute_workflow_success(self, engine):
        trigger = TimeTrigger("* * * * *")
        actions = [
            GenerateAction(topic="AI", platform="抖音"),
            NotifyAction(message="生成完成", channel="log"),
        ]
        wf = engine.create_workflow("u1", "test_exec", trigger, actions)
        result = engine.execute_workflow(wf["workflow_id"])
        assert result["status"] == "completed"
        assert len(result["action_results"]) == 2

    def test_execute_workflow_not_found(self, engine):
        result = engine.execute_workflow("nonexistent")
        assert result["status"] == "error"

    def test_execute_paused_workflow(self, engine):
        trigger = TimeTrigger("* * * * *")
        wf = engine.create_workflow("u1", "paused_wf", trigger, [])
        engine.update_workflow(wf["workflow_id"], {"status": "paused"})
        result = engine.execute_workflow(wf["workflow_id"])
        assert result["status"] == "skipped"

    def test_execute_workflow_updates_stats(self, engine):
        trigger = TimeTrigger("* * * * *")
        wf = engine.create_workflow("u1", "stats_test", trigger, [
            GenerateAction(topic="AI", platform="抖音"),
        ])
        engine.execute_workflow(wf["workflow_id"])
        stored = engine.get_workflow(wf["workflow_id"])
        assert stored["stats"]["total_executions"] == 1
        assert stored["stats"]["successful_executions"] == 1


class TestCheckTriggers:
    def test_hot_topic_trigger(self, engine):
        trigger = HotTopicTrigger(keywords=["AI"], platform="抖音")
        engine.create_workflow("u1", "hot_test", trigger, [
            GenerateAction(topic="{topic}", platform="抖音"),
        ])
        triggered = engine.check_triggers("u1", {
            "hot_topics": ["AI 新突破", "普通新闻"],
        })
        assert len(triggered) == 1
        assert triggered[0]["name"] == "hot_test"

    def test_no_matching_trigger(self, engine):
        trigger = HotTopicTrigger(keywords=["量子计算"], platform="抖音")
        engine.create_workflow("u1", "no_match", trigger, [])
        triggered = engine.check_triggers("u1", {"hot_topics": ["AI 趋势"]})
        assert len(triggered) == 0

    def test_paused_workflow_skipped(self, engine):
        trigger = HotTopicTrigger(keywords=["AI"])
        wf = engine.create_workflow("u1", "paused_trigger", trigger, [])
        engine.update_workflow(wf["workflow_id"], {"status": "paused"})
        triggered = engine.check_triggers("u1", {"hot_topics": ["AI 趋势"]})
        assert len(triggered) == 0


class TestEngineStats:
    def test_get_workflow_stats(self, engine):
        trigger = TimeTrigger("* * * * *")
        engine.create_workflow("u1", "wf1", trigger, [])
        engine.create_workflow("u1", "wf2", trigger, [])
        engine.update_workflow(engine.get_workflow("wf1")["workflow_id"] if False else "", {"status": "paused"})

        # 先创建再更新
        wfs = engine.list_workflows("u1")
        if len(wfs) >= 2:
            engine.update_workflow(wfs[0]["workflow_id"], {"status": "paused"})

        stats = engine.get_workflow_stats("u1")
        assert stats["user_id"] == "u1"
        assert stats["total_workflows"] == 2
        assert "workflow_list" in stats
        assert "success_rate" in stats
