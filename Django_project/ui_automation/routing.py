"""
WebSocket 路由配置

定义 UI 自动化测试的 WebSocket 路由。
"""

from django.urls import re_path
from .websocket_service import UiAutomationConsumer

websocket_urlpatterns = [
    re_path(r'^ws/ui-automation/(?P<execution_id>\d+)/$', UiAutomationConsumer.as_asgi()),
]
