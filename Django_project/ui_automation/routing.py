"""
UI 自动化测试模块 - WebSocket 路由配置

定义 WebSocket 端点，用于实时推送测试执行进度。

路由:
    ws/ui-automation/<execution_id>/ - 订阅指定执行记录的实时进度
"""

from django.urls import re_path

from .websocket_service import UiAutomationConsumer

websocket_urlpatterns = [
    # 按执行记录 ID 建立 WebSocket 连接，推送该执行的实时进度
    re_path(r'^ws/ui-automation/(?P<execution_id>\d+)/$', UiAutomationConsumer.as_asgi()),
]
