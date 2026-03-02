"""
api_automation/urls.py

API自动化测试模块的 URL 路由配置。

路由结构:
    /api/v1/api-automation/             -- 主路由（通过 DefaultRouter 自动注册）
    /api-token-auth/                    -- Token 认证端点
    /api/v1/api-automation/auth/user/   -- 当前用户信息
    /api/v1/api-automation/test-execute/  -- HTTP 执行器相关端点
    /api/v1/api-automation/test-cases/<id>/assertions/   -- 断言配置嵌套路由
    /api/v1/api-automation/test-cases/<id>/extractions/  -- 数据提取配置嵌套路由
    /api/v1/internal/cleanup/           -- 内部运维物理删除接口
"""
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .http_executor import (
    cancel_execution,
    execute_batch_requests,
    execute_http_request,
    get_execution_history,
)
from .views import (
    ApiCollectionViewSet,
    ApiDataDriverViewSet,
    ApiHttpExecutionRecordViewSet,
    ApiProjectViewSet,
    ApiTestCaseAssertionViewSet,
    ApiTestCaseExtractionViewSet,
    ApiTestCaseViewSet,
    ApiTestEnvironmentViewSet,
    ApiTestExecutionViewSet,
    ApiTestReportViewSet,
    ApiTestResultViewSet,
    CurrentUserView,
    DashboardViewSet,
    UserViewSet,
)
from .views_recycle_bin import (
    RecycleBinViewSet,
    internal_cleanup_view,
)

# ---------------------------------------------------------------------------
# 主路由器：自动为各 ViewSet 生成 RESTful URL 模式
# ---------------------------------------------------------------------------
router = DefaultRouter()
router.register(r'projects', ApiProjectViewSet, basename='api-projects')
router.register(r'collections', ApiCollectionViewSet, basename='api-collections')
router.register(r'test-cases', ApiTestCaseViewSet, basename='api-test-cases')
router.register(r'environments', ApiTestEnvironmentViewSet, basename='api-environments')
router.register(r'executions', ApiTestExecutionViewSet, basename='api-executions')
router.register(r'test-results', ApiTestResultViewSet, basename='api-test-results')
router.register(r'reports', ApiTestReportViewSet, basename='api-reports')
router.register(r'data-drivers', ApiDataDriverViewSet, basename='api-data-drivers')
router.register(r'http-execution-records', ApiHttpExecutionRecordViewSet, basename='http-execution-records')
router.register(r'dashboard', DashboardViewSet, basename='api-dashboard')
router.register(r'users', UserViewSet, basename='api-users')
router.register(r'recycle-bin', RecycleBinViewSet, basename='recycle-bin')

# ---------------------------------------------------------------------------
# URL 配置
# ---------------------------------------------------------------------------
urlpatterns = [
    # 主路由（包含所有通过 router 注册的 ViewSet 端点）
    path('api/v1/api-automation/', include(router.urls)),

    # 认证相关
    path('api-token-auth/', csrf_exempt(obtain_auth_token), name='api-token-auth'),
    path('api/v1/api-automation/auth/user/', csrf_exempt(CurrentUserView.as_view()), name='current-user'),

    # HTTP 执行器（手动/批量执行、历史查询、取消执行）
    path('api/v1/api-automation/test-execute/',
         csrf_exempt(execute_http_request), name='http-execute'),
    path('api/v1/api-automation/test-execute/batch/',
         csrf_exempt(execute_batch_requests), name='http-execute-batch'),
    path('api/v1/api-automation/test-execute/history/',
         csrf_exempt(get_execution_history), name='http-execute-history'),
    path('api/v1/api-automation/test-execute/<str:execution_id>/cancel/',
         csrf_exempt(cancel_execution), name='http-execute-cancel'),

    # 测试用例断言配置（嵌套路由：通过 test_case_id 关联）
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/',
         ApiTestCaseAssertionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/<int:pk>/',
         ApiTestCaseAssertionViewSet.as_view({
             'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
         })),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/batch_update/',
         csrf_exempt(ApiTestCaseAssertionViewSet.as_view({'post': 'batch_update'}))),

    # 测试用例数据提取配置（嵌套路由：通过 test_case_id 关联）
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/',
         ApiTestCaseExtractionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/<int:pk>/',
         ApiTestCaseExtractionViewSet.as_view({
             'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
         })),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/batch_update/',
         csrf_exempt(ApiTestCaseExtractionViewSet.as_view({'post': 'batch_update'}))),

    # 内部运维物理删除接口
    path('api/v1/internal/cleanup/permanent-delete/',
         csrf_exempt(internal_cleanup_view), name='internal-permanent-delete'),
]