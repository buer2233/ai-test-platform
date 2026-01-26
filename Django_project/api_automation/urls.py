"""
api_automation/urls.py

接口自动化测试模块的URL配置
"""
from django.urls import path, include
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from rest_framework import views as drf_views

from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    ApiProjectViewSet, ApiCollectionViewSet, ApiTestCaseViewSet,
    ApiTestEnvironmentViewSet, ApiTestExecutionViewSet,
    ApiTestResultViewSet, ApiTestReportViewSet, ApiDataDriverViewSet,
    ApiTestCaseAssertionViewSet, ApiTestCaseExtractionViewSet,
    ApiHttpExecutionRecordViewSet,
    DashboardViewSet,
    UserViewSet,
    CurrentUserView
)
from .views_recycle_bin import (
    RecycleBinViewSet,
    internal_cleanup_view
)
from .http_executor import (
    execute_http_request,
    execute_batch_requests,
    get_execution_history,
    cancel_execution
)

# 创建路由器
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

# 创建嵌套路由器（用于断言和数据提取）
nested_router = DefaultRouter()

# URL配置
urlpatterns = [
    path('api/v1/api-automation/', include(router.urls)),

    # 认证相关API
    path('api-token-auth/', csrf_exempt(obtain_auth_token), name='api-token-auth'),
    path('api/v1/api-automation/auth/user/', csrf_exempt(CurrentUserView.as_view()), name='current-user'),

    # HTTP执行器API - 添加CSRF豁免
    path('api/v1/api-automation/test-execute/', csrf_exempt(execute_http_request), name='http-execute'),
    path('api/v1/api-automation/test-execute/batch/', csrf_exempt(execute_batch_requests), name='http-execute-batch'),
    path('api/v1/api-automation/test-execute/history/', csrf_exempt(get_execution_history), name='http-execute-history'),
    path('api/v1/api-automation/test-execute/<str:execution_id>/cancel/', csrf_exempt(cancel_execution), name='http-execute-cancel'),

    # 测试用例断言配置API - 嵌套路由
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/',
         ApiTestCaseAssertionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/<int:pk>/',
         ApiTestCaseAssertionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/assertions/batch_update/',
         csrf_exempt(ApiTestCaseAssertionViewSet.as_view({'post': 'batch_update'}))),

    # 测试用例数据提取配置API - 嵌套路由
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/',
         ApiTestCaseExtractionViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/<int:pk>/',
         ApiTestCaseExtractionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('api/v1/api-automation/test-cases/<int:test_case_id>/extractions/batch_update/',
         csrf_exempt(ApiTestCaseExtractionViewSet.as_view({'post': 'batch_update'}))),

    # 内部物理删除接口 - 添加CSRF豁免
    path('api/v1/internal/cleanup/permanent-delete/', csrf_exempt(internal_cleanup_view), name='internal-permanent-delete'),
]