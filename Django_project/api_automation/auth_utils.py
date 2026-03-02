"""
api_automation/auth_utils.py

自定义认证和权限工具集。
提供用于 API 视图的 Token 认证装饰器和 Mixin 类，
简化视图中的认证配置。

主要组件:
    api_auth_exempt  -- 函数装饰器，对视图同时应用 CSRF 豁免和 Token 认证
    APITokenMixin    -- 类 Mixin，为 ViewSet 统一配置 Token 认证和权限校验
"""
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


def api_auth_exempt(view_func):
    """
    函数装饰器：为视图函数同时提供 CSRF 豁免和 Token 认证。

    工作流程:
        1. 对被装饰的视图函数应用 CSRF 豁免
        2. 若视图函数标记了 require_auth=True（默认），则尝试 Token 认证
        3. 认证失败时返回 401 JSON 响应
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        wrapped = csrf_exempt(view_func)

        # 检查视图是否需要 Token 认证（默认需要）
        if getattr(wrapped, 'require_auth', True):
            auth = TokenAuthentication()
            try:
                auth_result = auth.authenticate(request)
                if auth_result is not None:
                    request.user, request.auth = auth_result
                else:
                    return JsonResponse(
                        {'detail': 'Authentication credentials were not provided.'},
                        status=401
                    )
            except Exception:
                return JsonResponse(
                    {'detail': 'Authentication credentials were not provided.'},
                    status=401
                )

        return wrapped(request, *args, **kwargs)

    return _wrapped_view


class APITokenMixin:
    """
    ViewSet Mixin：统一配置 Token 认证和已登录权限校验。

    使用方式:
        class MyViewSet(APITokenMixin, viewsets.ModelViewSet):
            ...
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]