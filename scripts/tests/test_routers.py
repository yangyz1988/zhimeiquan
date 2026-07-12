# Router 模块单元测试
# 覆盖 18 个路由组的核心功能测试

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import json
import tempfile
import os


# ============ Health Router Tests ============
class TestHealthRouter:
    '''健康检查路由测试'''

    def test_health_returns_ok(self):
        '''健康检查应返回 ok 状态'''
        from routers.health import health
        import asyncio
        result = asyncio.run(health())
        assert result['status'] == 'ok'
        assert 'timestamp' in result
        assert 'version' in result

    def test_ready_checks_dependencies(self):
        '''就绪检查应检查依赖状态'''
        from routers.health import ready
        import asyncio
        result = asyncio.run(ready())
        assert 'status' in result
        assert 'checks' in result
        assert 'api' in result['checks']
        assert 'redis' in result['checks']
        assert 'deepseek' in result['checks']


# ============ A/B Test Router Tests ============
class TestABTestRouter:
    '''A/B 测试路由测试'''

    @pytest.fixture
    def temp_data_dir(self):
        '''临时数据目录'''
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_list_tests_empty(self, temp_data_dir):
        '''空列表测试'''
        from routers.ab_test import list_tests
        import routers.ab_test as ab_module
        original_dir = ab_module.tester.data_dir
        ab_module.tester.data_dir = temp_data_dir
        
        result = await list_tests()
        assert result['total'] == 0
        assert result['tests'] == []
        
        ab_module.tester.data_dir = original_dir

    @pytest.mark.asyncio
    async def test_create_ab_test(self, temp_data_dir):
        '''创建 A/B 测试'''
        from routers.ab_test import create_ab_test, CreateTestRequest
        import routers.ab_test as ab_module
        original_dir = ab_module.tester.data_dir
        ab_module.tester.data_dir = temp_data_dir
        
        req = CreateTestRequest(
            test_id='test_001',
            project_id='proj_001',
            variants=[
                {'id': 'A', 'content': 'variant A'},
                {'id': 'B', 'content': 'variant B'}
            ]
        )
        result = await create_ab_test(req)
        assert result['test_id'] == 'test_001'
        assert len(result['variants']) == 2
        
        ab_module.tester.data_dir = original_dir

    @pytest.mark.asyncio
    async def test_update_variant(self, temp_data_dir):
        '''更新变体数据'''
        from routers.ab_test import create_ab_test, update_variant, CreateTestRequest, UpdateVariantRequest
        import routers.ab_test as ab_module
        original_dir = ab_module.tester.data_dir
        ab_module.tester.data_dir = temp_data_dir
        
        req = CreateTestRequest(
            test_id='test_002',
            project_id='proj_001',
            variants=[{'id': 'A', 'content': 'variant A'}]
        )
        await create_ab_test(req)
        
        update_req = UpdateVariantRequest(variant_id='A', metrics={'views': 100, 'clicks': 10})
        result = await update_variant('test_002', update_req)
        assert 'variants' in result
        
        ab_module.tester.data_dir = original_dir


# ============ Calendar Router Tests ============
class TestCalendarRouter:
    '''内容调度路由测试'''

    @pytest.fixture
    def mock_scheduler(self):
        '''Mock scheduler service'''
        mock = MagicMock()
        mock.schedule_post.return_value = {'job_id': 'job_001', 'status': 'scheduled'}
        mock.schedule_recurring.return_value = {'job_id': 'job_002', 'status': 'recurring'}
        mock.get_calendar.return_value = {'days': []}
        mock.get_queue.return_value = {'jobs': []}
        mock.cancel_job.return_value = True
        return mock

    @pytest.mark.asyncio
    async def test_schedule_post(self, mock_scheduler):
        '''调度一次性发布'''
        from routers.calendar import ScheduleRequest, schedule_post
        import routers.calendar as cal_module
        original_scheduler = cal_module.content_scheduler
        cal_module.content_scheduler = mock_scheduler
        
        from datetime import datetime, timedelta
        req = ScheduleRequest(
            project_id='proj_001',
            content_id='content_001',
            platform='wechat',
            title='Test Title',
            content='Test Content',
            scheduled_at=datetime.now() + timedelta(hours=1)
        )
        result = await schedule_post(req)
        assert result['job_id'] == 'job_001'
        
        cal_module.content_scheduler = original_scheduler

    @pytest.mark.asyncio
    async def test_get_calendar(self, mock_scheduler):
        '''获取日历视图'''
        from routers.calendar import get_calendar
        import routers.calendar as cal_module
        original_scheduler = cal_module.content_scheduler
        cal_module.content_scheduler = mock_scheduler
        
        result = await get_calendar(2024, 1)
        assert 'days' in result
        
        cal_module.content_scheduler = original_scheduler

    @pytest.mark.asyncio
    async def test_cancel_job(self, mock_scheduler):
        '''取消调度任务'''
        from routers.calendar import cancel_job
        import routers.calendar as cal_module
        original_scheduler = cal_module.content_scheduler
        cal_module.content_scheduler = mock_scheduler
        
        result = await cancel_job('job_001')
        assert result['cancelled'] is True
        
        cal_module.content_scheduler = original_scheduler


# ============ Competitors Router Tests ============
class TestCompetitorsRouter:
    '''竞品监控路由测试'''

    @pytest.fixture
    def mock_monitor(self):
        '''Mock competitor monitor'''
        mock = MagicMock()
        mock.add_competitor.return_value = {'competitor_id': 'comp_001', 'status': 'added'}
        mock.remove_competitor.return_value = True
        mock.list_competitors.return_value = []
        mock.analyze_competitor.return_value = {'strategy': 'aggressive'}
        mock.get_comparison.return_value = {'gap': 0.15}
        return mock

    @pytest.mark.asyncio
    async def test_add_competitor(self, mock_monitor):
        '''添加竞品账号'''
        from routers.competitors import AddCompetitorRequest, add_competitor
        import routers.competitors as comp_module
        original_monitor = comp_module.monitor
        comp_module.monitor = mock_monitor
        
        req = AddCompetitorRequest(
            user_id='user_001',
            platform='douyin',
            account_id='account_001',
            account_name='Competitor Account'
        )
        result = await add_competitor(req)
        assert result['competitor_id'] == 'comp_001'
        
        comp_module.monitor = original_monitor

    @pytest.mark.asyncio
    async def test_list_competitors(self, mock_monitor):
        '''列出竞品'''
        from routers.competitors import list_competitors
        import routers.competitors as comp_module
        original_monitor = comp_module.monitor
        comp_module.monitor = mock_monitor
        
        result = await list_competitors('user_001')
        assert 'competitors' in result
        
        comp_module.monitor = original_monitor

    @pytest.mark.asyncio
    async def test_remove_competitor(self, mock_monitor):
        '''移除竞品'''
        from routers.competitors import remove_competitor
        import routers.competitors as comp_module
        original_monitor = comp_module.monitor
        comp_module.monitor = mock_monitor
        
        result = await remove_competitor('comp_001')
        assert result['success'] is True
        
        comp_module.monitor = original_monitor


# ============ Content Router Tests ============
class TestContentRouter:
    '''内容生成路由测试'''

    def test_generate_endpoint_structure(self):
        '''验证内容生成端点结构'''
        from routers.content import router
        routes = [r.path for r in router.routes]
        assert '/generate' in routes


# ============ Model Router Tests ============
class TestModelRouterAPI:
    '''模型路由 API 测试'''

    def test_profiles_endpoint_structure(self):
        '''验证模型档案端点结构'''
        from routers.model_router import router
        routes = [r.path for r in router.routes]
        assert '/profiles' in routes

    def test_recommend_endpoint_structure(self):
        '''验证推荐端点结构'''
        from routers.model_router import router
        routes = [r.path for r in router.routes]
        assert '/recommend' in routes

    def test_chat_endpoint_structure(self):
        '''验证聊天端点结构'''
        from routers.model_router import router
        routes = [r.path for r in router.routes]
        assert '/chat' in routes


# ============ Stream Router Tests ============
class TestStreamRouter:
    '''流式生成路由测试'''

    def test_stream_endpoint_exists(self):
        '''验证流式端点存在'''
        from routers.stream import router
        routes = [r.path for r in router.routes]
        assert '/generate' in routes


# ============ Team Router Tests ============
class TestTeamRouter:
    '''团队协作路由测试'''

    def test_team_endpoints_exist(self):
        '''验证团队端点存在'''
        from routers.team import router
        routes = [r.path for r in router.routes]
        assert any('team' in r for r in routes)


# ============ Fire Score Router Tests ============
class TestFireScoreRouter:
    '''Fire Score 路由测试'''

    def test_fire_score_endpoint_exists(self):
        '''验证 Fire Score 端点存在'''
        from routers.fire_score import router
        routes = [r.path for r in router.routes]
        assert len(routes) > 0


# ============ Analytics Router Tests ============
class TestAnalyticsRouter:
    '''分析洞察路由测试'''

    def test_analytics_endpoints_exist(self):
        '''验证分析端点存在'''
        from routers.analytics import router
        routes = [r.path for r in router.routes]
        assert any('overview' in r or 'analytics' in r for r in routes)


# ============ Insights Router Tests ============
class TestInsightsRouter:
    '''洞察路由测试'''

    def test_insights_endpoints_exist(self):
        '''验证洞察端点存在'''
        from routers.insights import router
        routes = [r.path for r in router.routes]
        assert any('trends' in r or 'predict' in r or 'posting-time' in r for r in routes)


# ============ Video Router Tests ============
class TestVideoRouter:
    '''视频生成路由测试'''

    def test_video_endpoint_exists(self):
        '''验证视频端点存在'''
        from routers.video import router
        routes = [r.path for r in router.routes]
        assert '/generate' in routes


# ============ Image Router Tests ============
class TestImageRouter:
    '''图像生成路由测试'''

    def test_image_endpoint_exists(self):
        '''验证图像端点存在'''
        from routers.image import router
        routes = [r.path for r in router.routes]
        assert '/generate' in routes


# ============ Templates Router Tests ============
class TestTemplatesRouter:
    '''模板路由测试'''

    def test_templates_endpoint_exists(self):
        '''验证模板端点存在'''
        from routers.templates import router
        routes = [r.path for r in router.routes]
        assert '/list' in routes


# ============ Agent Router Tests ============
class TestAgentRouter:
    '''智能体路由测试'''

    def test_agent_endpoint_exists(self):
        '''验证智能体端点存在'''
        from routers.agent import router
        routes = [r.path for r in router.routes]
        assert '/start' in routes


# ============ Rules Router Tests ============
class TestRulesRouter:
    '''平台规则路由测试'''

    def test_rules_endpoint_exists(self):
        '''验证规则端点存在'''
        from routers.rules import router
        routes = [r.path for r in router.routes]
        assert len(routes) > 0


# ============ Titles Router Tests ============
class TestTitlesRouter:
    '''标题生成路由测试'''

    def test_titles_endpoint_exists(self):
        '''验证标题端点存在'''
        from routers.titles import router
        routes = [r.path for r in router.routes]
        assert '/generate' in routes


# ============ Score Router Tests ============
class TestScoreRouter:
    '''内容评分路由测试'''

    def test_score_endpoint_exists(self):
        '''验证评分端点存在'''
        from routers.score import router
        routes = [r.path for r in router.routes]
        assert '/score' in routes
