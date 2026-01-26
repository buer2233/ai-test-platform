"""
WebSocket路由配置
定义WebSocket URL模式和对应的消费者
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 测试执行状态WebSocket
    # URL: ws://host/ws/execution/<execution_id>/
    re_path(
        r'^ws/execution/(?P<execution_id>\d+)/$',
        consumers.ExecutionStatusConsumer.as_asgi(),
        name='execution_status_ws'
    ),
]
