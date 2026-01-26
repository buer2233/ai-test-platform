"""
自定义认证和权限配置
用于API视图的CSRF豁免
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from functools import wraps
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def api_auth_exempt(view_func):
    """
    装饰器：为API视图提供认证豁免和CSRF豁免
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 应用CSRF豁免
        view_func = csrf_exempt(view_func)

        # 如果请求需要认证，检查Token
        if getattr(view_func, 'require_auth', True):
            auth = TokenAuthentication()
            try:
                auth_result = auth.authenticate(request)
                if auth_result is not None:
                    request.user, request.auth = auth_result
                else:
                    return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
            except Exception:
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


class APITokenMixin:
    """
    Mixin类：为ViewSet提供Token认证
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]