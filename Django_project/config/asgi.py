"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import api_automation.routing
import ui_automation.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 初始化Django ASGI应用
django_asgi_app = get_asgi_application()

# 合并所有WebSocket路由
websocket_urlpatterns = []
websocket_urlpatterns.extend(api_automation.routing.websocket_urlpatterns)
websocket_urlpatterns.extend(ui_automation.routing.websocket_urlpatterns)

# 应用路由配置
application = ProtocolTypeRouter({
    # HTTP请求处理
    "http": django_asgi_app,

    # WebSocket请求处理
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
