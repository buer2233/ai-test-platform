"""
AI 自动化测试平台 - 根 URL 配置

路由结构：
  /admin/                         - Django 后台管理
  /swagger/                       - Swagger UI 文档
  /redoc/                         - ReDoc 文档
  /api/v1/api-automation/...      - API 自动化测试模块（由 api_automation.urls 定义）
  /api/v1/ui-automation/...       - UI 自动化测试模块（由 ui_automation.urls 定义）
  /api-token-auth/                - Token 认证端点
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken import views as drf_authtoken_views

# ============================================================
# Swagger / OpenAPI 文档配置
# ============================================================

schema_view = get_schema_view(
    openapi.Info(
        title="AI 自动化测试平台 API",
        default_version='v1',
        description=(
            "AI 自动化测试平台 REST API 文档。\n\n"
            "包含项目管理、集合管理、测试用例、环境配置、"
            "测试执行、测试报告、UI 自动化等全部接口。"
        ),
        contact=openapi.Contact(
            email="support@api-automation.com",
            name="API 自动化测试平台技术支持",
        ),
        license=openapi.License(
            name="Apache License 2.0",
            url="https://www.apache.org/licenses/LICENSE-2.0.html",
        ),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# ============================================================
# URL 路由表
# ============================================================

urlpatterns = [
    # --- 文档端点 ---
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # --- Django 后台 ---
    path('admin/', admin.site.urls),

    # --- 业务模块（各模块内部定义具体路由前缀） ---
    path('', include('api_automation.urls')),
    path('', include('ui_automation.urls')),

    # --- 认证端点 ---
    path('api-auth/', include('rest_framework.urls')),
    # Token 认证：提供两个路径兼容不同前端配置
    path('api-token-auth/', csrf_exempt(drf_authtoken_views.obtain_auth_token)),
    path('api/api-token-auth/', csrf_exempt(drf_authtoken_views.obtain_auth_token)),
]

# 开发环境提供静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
