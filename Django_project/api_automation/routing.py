"""
api_automation/routing.py

WebSocket 路由配置。
定义 WebSocket URL 模式和对应的消费者（Consumer），
用于测试执行过程中的实时状态推送。

路由说明:
    ws://host/ws/execution/<execution_id>/  -- 监听指定执行记录的实时状态更新
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r'^ws/execution/(?P<execution_id>\d+)/$',
        consumers.ExecutionStatusConsumer.as_asgi(),
        name='execution_status_ws'
    ),
]
