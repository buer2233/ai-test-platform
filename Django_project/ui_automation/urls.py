"""
UI 自动化测试模块 - URL 路由配置

定义所有 UI 自动化相关的 REST API 端点路由。
所有端点统一挂载在 /api/v1/ui-automation/ 前缀下。

端点一览:
    /api/v1/ui-automation/projects/       - 测试项目 CRUD
    /api/v1/ui-automation/test-cases/     - 测试用例 CRUD + 运行
    /api/v1/ui-automation/executions/     - 执行记录管理 + 运行/取消
    /api/v1/ui-automation/reports/        - 测试报告查看（只读）
    /api/v1/ui-automation/screenshots/    - 截图查看（只读）
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

# 使用 SimpleRouter 避免注册格式后缀转换器，防止与 api_automation 模块冲突
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
