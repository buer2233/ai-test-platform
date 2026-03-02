"""
api_automation/swagger_config.py

Swagger/OpenAPI 文档配置。

定义 API 文档的元信息（标题、版本、描述）、标签分组、安全认证方案，
以及分层 URL 结构映射（供文档生成器参考）。

使用方式:
    - schema_view: 用于渲染 Swagger UI 和 ReDoc 页面
    - SWAGGER_SETTINGS: Django settings 中的 Swagger 相关配置
    - tags: API 接口的分组标签定义
"""
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions


# =============================================================================
# API 标签定义（按功能模块分组）
# =============================================================================

tags = [
    {
        'name': 'Project Management',
        'description': '项目管理相关接口，包括项目的创建、查询、更新、删除等操作',
    },
    {
        'name': 'Collection Management',
        'description': '集合管理相关接口，包括API集合的创建、管理、导入导出等操作',
    },
    {
        'name': 'Test Cases',
        'description': '测试用例相关接口，包括用例的创建、编辑、执行、克隆等操作',
    },
    {
        'name': 'Environment Configuration',
        'description': '环境配置相关接口，包括测试环境的创建、管理、变量配置等',
    },
    {
        'name': 'Test Execution',
        'description': '测试执行相关接口，包括执行计划的创建、管理、执行状态监控等',
    },
    {
        'name': 'Test Reports',
        'description': '测试报告相关接口，包括报告的查询、导出、统计分析等',
    },
    {
        'name': 'Data Drivers',
        'description': '数据驱动测试相关接口，包括数据源的配置、预览、管理等',
    },
    {
        'name': 'HTTP Executor',
        'description': 'HTTP执行器相关接口，包括直接执行HTTP请求、批量执行等',
    },
    {
        'name': 'UI Automation',
        'description': 'UI自动化测试模块 - 基于browser_use的AI驱动UI测试，支持自然语言描述测试场景',
    },
    {
        'name': 'UI Test Projects',
        'description': 'UI测试项目管理接口，包括项目的创建、查询、更新、删除、统计等操作',
    },
    {
        'name': 'UI Test Cases',
        'description': 'UI测试用例管理接口，支持自然语言描述的测试用例创建和管理',
    },
    {
        'name': 'UI Test Executions',
        'description': 'UI测试执行接口，包括执行记录的创建、运行、取消、状态监控等',
    },
    {
        'name': 'UI Test Reports',
        'description': 'UI测试报告接口，包括HTML报告的生成、查看、截图展示等',
    },
    {
        'name': 'Authentication',
        'description': '用户认证相关接口，包括登录、登出、token刷新等操作',
    },
]


# =============================================================================
# Schema 信息
# =============================================================================

schema_info = openapi.Info(
    title='API自动化测试平台',
    default_version='v1',
    description='''
        # 主要功能
        这是一个功能完善的API自动化测试平台，提供以下核心功能：

        ## 项目管理
        项目创建、编辑、删除、成员管理、统计和概览

        ## 集合管理
        API集合的创建和管理、导入导出、版本控制

        ## 测试用例
        RESTful API测试用例设计、多种请求方法、断言配置、变量提取

        ## 环境配置
        多环境配置管理、全局变量和环境变量、连接测试

        ## 测试执行
        单个/批量执行、实时状态监控、并发控制

        ## 测试报告
        详细报告生成、多维度统计、图表可视化

        ## 数据驱动测试
        多种数据源支持（JSON、CSV、Excel、Database）

        ## HTTP执行器
        直接HTTP请求测试工具、变量替换、请求历史

        ## UI自动化测试
        基于browser_use的AI驱动UI测试、自然语言描述测试场景

        ## 认证系统
        Token认证、用户权限管理
        ''',
    terms_of_service='https://github.com/yourorg/api-automation/blob/main/Terms.md',
    contact=openapi.Contact(
        email='support@api-automation.com',
        name='API自动化测试平台技术支持',
        url='https://github.com/yourorg/api-automation'
    ),
    license=openapi.License(
        name='Apache License 2.0',
        url='https://www.apache.org/licenses/LICENSE-2.0.html'
    ),
    version='1.0.0',
)


# =============================================================================
# Schema View（用于渲染 Swagger UI / ReDoc）
# =============================================================================

schema_view = get_schema_view(
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[r'^api/v1/api-automation/'],
)

urlpatterns = [
    path('swagger/', schema_view, name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


# =============================================================================
# Swagger 配置字典（供 Django settings 引用）
# =============================================================================

SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': '格式: Bearer <token>',
        },
    },
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# =============================================================================
# 分层 URL 结构映射（文档参考用）
# =============================================================================

LAYERED_URLS = {
    'api/v1/api-automation/': {
        'projects/': {
            'list/': '项目列表',
            'create/': '创建项目',
            'detail/': '项目详情',
            'update/': '更新项目',
            'delete/': '删除项目',
            'clone/': '克隆项目',
            'stats/': '项目统计',
        },
        'collections/': {
            'list/': '集合列表',
            'create/': '创建集合',
            'detail/': '集合详情',
            'update/': '更新集合',
            'delete/': '删除集合',
            'import/': '导入集合',
            'export/': '导出集合',
        },
        'test-cases/': {
            'list/': '测试用例列表',
            'create/': '创建测试用例',
            'detail/': '测试用例详情',
            'update/': '更新测试用例',
            'delete/': '删除测试用例',
            'clone/': '克隆测试用例',
            'run/': '执行测试用例',
            'batch-run/': '批量执行',
        },
        'environments/': {
            'list/': '环境列表',
            'create/': '创建环境',
            'detail/': '环境详情',
            'update/': '更新环境',
            'delete/': '删除环境',
            'test-connection/': '测试连接',
            'set-default/': '设为默认',
        },
        'executions/': {
            'list/': '执行列表',
            'create/': '创建执行',
            'detail/': '执行详情',
            'cancel/': '取消执行',
            'results/': '执行结果',
            'report/': '生成报告',
        },
        'reports/': {
            'list/': '报告列表',
            'detail/': '报告详情',
            'export/': '导出报告',
            'statistics/': '统计信息',
        },
        'data-drivers/': {
            'list/': '数据源列表',
            'create/': '创建数据源',
            'detail/': '数据源详情',
            'update/': '更新数据源',
            'delete/': '删除数据源',
            'preview/': '预览数据',
        },
        'http-executor/': {
            'execute/': '执行请求',
            'batch/': '批量执行',
            'history/': '执行历史',
            'cancel/': '取消执行',
        },
        'auth/': {
            'login/': '用户登录',
            'logout/': '用户登出',
            'refresh/': '刷新Token',
            'register/': '用户注册',
            'user/': '用户信息',
        }
    },
    'api/v1/ui-automation/': {
        'projects/': {
            'list/': 'UI项目列表',
            'create/': '创建UI项目',
            'detail/': 'UI项目详情',
            'test_cases/': '项目下的测试用例',
            'executions/': '项目下的执行记录',
            'statistics/': '项目统计信息',
        },
        'test-cases/': {
            'list/': 'UI用例列表',
            'create/': '创建UI用例',
            'detail/': 'UI用例详情',
            'executions/': '用例执行历史',
            'execute/': '执行用例',
        },
        'executions/': {
            'list/': '执行记录列表',
            'detail/': '执行详情',
            'run/': '运行测试',
            'cancel/': '取消执行',
            'report/': '获取测试报告',
            'screenshots/': '获取执行截图',
        },
        'reports/': {
            'list/': '测试报告列表',
            'detail/': '报告详情',
        },
        'screenshots/': {
            'list/': '截图列表',
            'detail/': '截图详情',
        },
    }
}


def get_layered_schema_view():
    """返回使用 schema_info 配置的分层 Schema View。"""
    return get_schema_view(
        schema_info,
        public=True,
        permission_classes=[permissions.AllowAny],
        patterns=[],
    )


def get_custom_swagger_settings():
    """返回包含额外自定义配置的 Swagger 设置副本。"""
    settings = SWAGGER_SETTINGS.copy()
    settings.update({
        'DEFAULT_GENERATOR_CLASS': 'drf_yasg.generators.OpenAPISchemaGenerator',
        'SECURITY_DEFINITIONS': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': '格式: Bearer <token>',
                'bearerFormat': 'JWT',
            }
        },
    })
    return settings