"""
ASGI 配置 - 支持 HTTP 和 WebSocket 双协议

使用 Django Channels 的 ProtocolTypeRouter 实现协议分发：
- HTTP 请求：由标准 Django ASGI 应用处理
- WebSocket 请求：由 Channels URLRouter 分发到各模块的 Consumer

各模块的 WebSocket 路由在各自的 routing.py 中定义。
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import api_automation.routing
import ui_automation.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 初始化 Django ASGI 应用（必须在导入路由之后调用）
django_asgi_app = get_asgi_application()

# 合并所有模块的 WebSocket 路由
websocket_urlpatterns = (
    api_automation.routing.websocket_urlpatterns
    + ui_automation.routing.websocket_urlpatterns
)

# ASGI 协议分发器
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
