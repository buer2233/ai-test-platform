"""
UI自动化测试模块 URL 配置

定义所有 UI 自动化相关的 API 端点路由。
"""

from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import (
    UiTestProjectViewSet,
    UiTestCaseViewSet,
    UiTestExecutionViewSet,
    UiTestReportViewSet,
    UiScreenshotViewSet,
)

# 创建SimpleRouter（不注册格式后缀转换器，避免与api_automation冲突）
router = SimpleRouter()
router.register(r'projects', UiTestProjectViewSet, basename='ui-projects')
router.register(r'test-cases', UiTestCaseViewSet, basename='ui-test-cases')
router.register(r'executions', UiTestExecutionViewSet, basename='ui-executions')
router.register(r'reports', UiTestReportViewSet, basename='ui-reports')
router.register(r'screenshots', UiScreenshotViewSet, basename='ui-screenshots')

app_name = 'ui_automation'

urlpatterns = [
    path('api/v1/ui-automation/', include(router.urls)),
]
