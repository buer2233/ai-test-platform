"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken import views as drf_authtoken_views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 创建 Swagger/OpenAPI 模式
schema_view = get_schema_view(
    openapi.Info(
        title="API自动化测试平台",
        default_version='v1',
        description="""
        # API自动化测试平台

        这是一个功能完善的API自动化测试平台，提供以下核心功能：

        ## 🏗️ 项目管理
        - 项目创建、编辑、删除
        - 项目成员管理
        - 项目统计和概览

        ## 📚 集合管理
        - API集合的创建和管理
        - 集合的导入导出
        - 集合版本控制

        ## 🧪 测试用例
        - RESTful API测试用例设计
        - 多种请求方法支持
        - 断言配置
        - 变量提取和使用

        ## ⚙️ 环境配置
        - 多环境配置管理
        - 全局变量和环境变量
        - 请求头预设

        ## 🚀 测试执行
        - 单个用例执行
        - 批量测试执行
        - 实时执行状态监控

        ## 📊 测试报告
        - 详细的测试报告生成
        - 多维度数据统计
        - 报告导出功能

        ## 🔐 认证系统
        - JWT Token认证
        - 用户权限管理
        - 操作日志记录
        """,
        terms_of_service="https://github.com/yourorg/api-automation/blob/main/Terms.md",
        contact=openapi.Contact(email="support@api-automation.com", name="API自动化测试平台技术支持"),
        license=openapi.License(name="Apache License 2.0", url="https://www.apache.org/licenses/LICENSE-2.0.html"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger UI 文档
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # OpenAPI JSON 格式
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    path('admin/', admin.site.urls),
    # API 接口自动化测试模块
    path('', include('api_automation.urls')),
    # UI 自动化测试模块
    path('', include('ui_automation.urls')),
    # DRF 认证相关
    path('api-auth/', include('rest_framework.urls')),
    # Token 认证 - 支持两种路径以兼容不同前端配置
    # 使用csrf_exempt豁免CSRF检查，因为这些是API端点
    path('api-token-auth/', csrf_exempt(drf_authtoken_views.obtain_auth_token)),
    path('api/api-token-auth/', csrf_exempt(drf_authtoken_views.obtain_auth_token)),
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
