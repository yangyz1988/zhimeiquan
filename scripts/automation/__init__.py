"""自动化引擎包"""

from .engine import (
    AutomationEngine,
    Trigger, TimeTrigger, HotTopicTrigger, PerformanceTrigger, ScheduleTrigger,
    TriggerRegistry, trigger_from_dict,
    Action, GenerateAction, RewriteAction, PublishAction, NotifyAction, AnalyzeAction,
    ActionRegistry, action_from_dict,
    automation_engine,
)
