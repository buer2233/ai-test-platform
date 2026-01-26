"""
Swagger API文档配置
实现分层级的API文档展示
"""

from django.urls import path
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 定义主要的API标签（顶层分类）
tags = [
    # 项目管理模块
    {
        'name': 'Project Management',
        'description': '项目管理相关接口，包括项目的创建、查询、更新、删除等操作',
        'externalDocs': {
            'description': '更多项目操作',
            'url': 'http://127.0.0.1:3000/projects'
        }
    },

    # 集合管理模块
    {
        'name': 'Collection Management',
        'description': '集合管理相关接口，包括API集合的创建、管理、导入导出等操作',
        'externalDocs': {
            'description': '集合管理指南',
            'url': 'http://127.0.0.1:3000/collections'
        }
    },

    # 测试用例模块
    {
        'name': 'Test Cases',
        'description': '测试用例相关接口，包括用例的创建、编辑、执行、克隆等操作',
        'externalDocs': {
            'description': '测试用例指南',
            'url': 'http://127.0.0.1:3000/test-cases'
        }
    },

    # 环境配置模块
    {
        'name': 'Environment Configuration',
        'description': '环境配置相关接口，包括测试环境的创建、管理、变量配置等',
        'externalDocs': {
            'description': '环境配置指南',
            'url': 'http://127.0.0.1:3000/environments'
        }
    },

    # 测试执行模块
    {
        'name': 'Test Execution',
        'description': '测试执行相关接口，包括执行计划的创建、管理、执行状态监控等',
        'externalDocs': {
            'description': '执行管理指南',
            'url': 'http://127.0.0.1:3000/executions'
        }
    },

    # 测试报告模块
    {
        'name': 'Test Reports',
        'description': '测试报告相关接口，包括报告的查询、导出、统计分析等',
        'externalDocs': {
            'description': '报告分析指南',
            'url': 'http://127.0.0.1:3000/reports'
        }
    },

    # 数据驱动模块
    {
        'name': 'Data Drivers',
        'description': '数据驱动测试相关接口，包括数据源的配置、预览、管理等',
        'externalDocs': {
            'description': '数据驱动测试指南',
            'url': 'OpenAPI URL'
        }
    },

    # HTTP执行器模块
    {
        'name': 'HTTP Executor',
        'description': 'HTTP执行器相关接口，包括直接执行HTTP请求、批量执行等',
        'externalDocs': {
            'description': 'HTTP执行器工具',
            'url': 'http://127.0.1:3000/http-executor'
        }
    },

    # UI自动化测试模块
    {
        'name': 'UI Automation',
        'description': 'UI自动化测试模块 - 基于browser_use的AI驱动UI测试，支持自然语言描述测试场景',
        'externalDocs': {
            'description': 'UI自动化测试指南',
            'url': '/api/v1/ui-automation/'
        }
    },

    # UI自动化项目管理
    {
        'name': 'UI Test Projects',
        'description': 'UI测试项目管理接口，包括项目的创建、查询、更新、删除、统计等操作',
    },

    # UI自动化测试用例
    {
        'name': 'UI Test Cases',
        'description': 'UI测试用例管理接口，支持自然语言描述的测试用例创建和管理',
    },

    # UI自动化测试执行
    {
        'name': 'UI Test Executions',
        'description': 'UI测试执行接口，包括执行记录的创建、运行、取消、状态监控等',
    },

    # UI自动化测试报告
    {
        'name': 'UI Test Reports',
        'description': 'UI测试报告接口，包括HTML报告的生成、查看、截图展示等',
    },

    # 认证模块
    {
        'name': 'Authentication',
        'description': '用户认证相关接口，包括登录、登出、token刷新等操作',
        'externalDocs': {
            'description': '认证帮助文档',
            'url': 'OpenAPI URL'
        }
    },
]

# 创建分层的schema_info
schema_info = openapi.Info(
    title='API自动化测试平台',
    default_version='v1',
    description='''
        # 主要功能
        这是一个功能完善的API自动化测试平台，提供以下核心功能：

        ## 🏗️ 项目管理
        - 项目创建、编辑、删除
        - 项目成员管理
        - 项目统计和概览
        - 项目克隆和备份

        ## 📚 集合管理
        - API集合的创建和管理
        - 集合的导入导出
        - 集合版本控制
        - 集合间的依赖关系

        ## 🧪 测试用例
        - RESTful API测试用例设计
        - 多种请求方法支持（GET、POST、PUT、DELETE等）
        - 断言配置（11种断言类型）
        - 变量提取和使用
        - 测试用例版本管理
        - 批量操作和导入导出

        ## ⚙️ 环境配置
        - 多环境配置管理
        - 全局变量和环境变量
        - 请求头预设
        - SSL证书配置
        - 连接测试和验证

        ## 🚀 测试执行
        - 单个用例执行
        - 批量测试执行
        - 执行计划管理
        - 实时执行状态监控
        - 并发执行控制
        - 执行结果统计

        📊 **测试报告**
        - 详细的测试报告生成
        - 多维度数据统计
        - 图表可视化展示
        - 报告导出（PDF、Excel等格式）
        - 历史报告对比分析

        ## 📊 **数据驱动测试**
        - 多种数据源支持（JSON、CSV、Excel、Database）
        - 数据预览和验证
        - 变量映射配置
        - 动态数据加载

        ⚡ **HTTP执行器**
        - 直接HTTP请求测试工具
        - 支持所有HTTP方法
        - 多种请求格式（JSON、Form、File等）
        - 变量替换系统
        - 请求历史记录
        - 一键保存为测试用例
        - 响应结果分析

        ## 🤖 **UI自动化测试模块**
        - 基于browser_use的AI驱动UI测试
        - 自然语言描述测试场景
        - 自动解析并执行浏览器操作
        - 实时执行进度推送（WebSocket）
        - HTML格式测试报告生成
        - 截图记录和展示
        - 支持有头/无头浏览器模式

        ## 🔐 **认证系统**
        - JWT Token认证
        - 用户权限管理
        - 角色权限控制
        - 操作日志记录

        ## 🔧 **高级功能**
        - 自动化测试调度
        - 持续集成支持（CI/CD）
        - Webhook通知
        - 数据加密存储
        - 性能监控和优化

        ## 📚 **文档和帮助**
        - 完整的API文档
        - 使用指南和最佳实践
        - 常见问题解答
        - 视频教程和示例
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

# 创建分层级的Schema View
schema_view = get_schema_view(
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[r'^api/v1/api-automation/'],
)

# 自定义URL配置
urlpatterns = [
    path('swagger/', schema_view, name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# API文档页面配置
SWAGGER_SETTINGS = {
    'DEFAULT_FIELD_INSPECTORS': [
        'rest_framework.inspectors.InspectAPIView',
        'rest_framework.permissions.InspectPermissions',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_PARAMS': 'page',
    'PAGINATE_PARAM': 'page',
    # 分组显示设置
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'USE_SESSION_AUTH': False,
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': '格式: Bearer <token>',
        },
    },
}

# 分层URL配置示例
LAYERED_URLS = {
    # 第一层：API根路径
    'api/v1/api-automation/': {
        # 第二层：主要功能模块
        'projects/': {
            # 第三层：子功能
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
            'update/': '更新执行',
            'delete/': '删除执行',
            'run/': '开始执行',
            'cancel/': '取消执行',
            'results/': '执行结果',
            'report/': '生成报告',
        },
        'reports/': {
            'list/': '报告列表',
            'detail/': '报告详情',
            'export/': '导出报告',
            'statistics/': '统计信息',
            'compare/': '报告对比',
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
    # UI自动化测试模块
    'api/v1/ui-automation/': {
        'projects/': {
            'list/': 'UI项目列表',
            'create/': '创建UI项目',
            'detail/': 'UI项目详情',
            'update/': '更新UI项目',
            'delete/': '删除UI项目',
            'test_cases/': '项目下的测试用例',
            'executions/': '项目下的执行记录',
            'statistics/': '项目统计信息',
        },
        'test-cases/': {
            'list/': 'UI用例列表',
            'create/': '创建UI用例',
            'detail/': 'UI用例详情',
            'update/': '更新UI用例',
            'delete/': '删除UI用例',
            'executions/': '用例执行历史',
            'execute/': '执行用例',
        },
        'executions/': {
            'list/': '执行记录列表',
            'create/': '创建执行记录',
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
    """
    返回分层级的Schema View
    """
    from drf_yasg.renderers import SwaggerUIRenderer, ReDocRenderer

    return get_schema_view(
        schema_info,
        public=True,
        permission_classes=[permissions.AllowAny],
        patterns=[],  # 移除 patterns 参数以避免错误
    )

def get_custom_swagger_settings():
    """
    返回自定义的Swagger设置
    """
    settings = SWAGGER_SETTINGS.copy()
    settings.update({
        'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
        'DEFAULT_FIELD_INSPECTORS': [
            'rest_framework.inspectors.InspectAPIView',
            'rest_framework.inspectors.InspectPermissions',
            'rest_framework.inspectors.InspectAutoSchema',
        ],
        'DEFAULT_GENERATOR_CLASS': 'drf_yasg.generators.OpenAPISchemaGenerator',
        'DEFAULT_FILTER_BACKENDS': [
            'django_filters.rest_framework.DjangoFilterBackend',
        ],
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