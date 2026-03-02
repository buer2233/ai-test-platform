"""
Django 项目配置文件

本项目为 AI 自动化测试平台，包含以下模块：
- api_automation: API 接口自动化测试
- ui_automation: UI 自动化测试（基于 browser-use）

基于 Django 3.2 + Django REST Framework + Channels(WebSocket)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ============================================================
# 基础路径配置
# ============================================================

# 项目根目录（Django_project/）
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 browser-use 的 .env 文件（包含 OPENAI_API_KEY 等 LLM 配置）
BROWSER_USE_DIR = BASE_DIR / 'ui_automation' / 'browser-use-0.11.2'
load_dotenv(BROWSER_USE_DIR / '.env')

# 确保日志目录存在
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ============================================================
# 安全配置
# ============================================================

# TODO: 生产环境必须替换为安全的密钥，并从环境变量读取
SECRET_KEY = 'django-insecure-l3r4(#7z&ijd8mb#lx^53vv52z26!++zg%5e&*47%0j%+#tn0e'

DEBUG = True

# 允许访问的主机名（同时用于 HTTP 和 WebSocket）
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ============================================================
# 应用注册
# ============================================================

INSTALLED_APPS = [
    # Django 内置应用
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 第三方库
    'rest_framework',               # REST API 框架
    'rest_framework.authtoken',     # Token 认证
    'django_filters',               # 查询过滤器
    'drf_yasg',                     # Swagger/OpenAPI 文档
    'corsheaders',                  # 跨域请求支持
    'channels',                     # WebSocket 支持
    # 项目业务模块
    'api_automation',               # API 接口自动化测试
    'ui_automation',                # UI 自动化测试
]

# ============================================================
# 中间件配置
# ============================================================

MIDDLEWARE = [
    # CORS 必须放在最前面，确保预检请求正确响应
    'corsheaders.middleware.CorsMiddleware',
    # Django 安全相关中间件
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 自定义：对 /api/ 路径豁免 CSRF 检查（使用 Token 认证代替）
    'config.settings.DisableCSRFMiddleware',
    # 自定义：全局异常处理（放在最后，捕获所有未处理的异常）
    'api_automation.middleware.exception_handler.GlobalExceptionHandler',
]

# ============================================================
# URL 与模板配置
# ============================================================

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================================
# 服务器应用配置
# ============================================================

# 传统 WSGI（用于普通 HTTP 请求）
WSGI_APPLICATION = 'config.wsgi.application'

# ASGI（用于 HTTP + WebSocket，Channels 需要）
ASGI_APPLICATION = 'config.asgi.application'

# Channel Layer 配置（WebSocket 消息传输层）
# 开发环境使用内存通道，生产环境应切换为 Redis
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
    # 生产环境 Redis 配置示例：
    # 'default': {
    #     'BACKEND': 'channels_redis.core.RedisChannelLayer',
    #     'CONFIG': {
    #         'hosts': [(os.environ.get('REDIS_HOST', '127.0.0.1'), 6379)],
    #     },
    # },
}

# ============================================================
# 数据库配置
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ai_test_platform',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ============================================================
# 密码验证规则
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# 国际化与时区
# ============================================================

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ============================================================
# 静态文件
# ============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================
# 主键字段类型
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# Django REST Framework 配置
# ============================================================

REST_FRAMEWORK = {
    # 仅使用 Token 认证（不使用 Session 认证，避免 CSRF 问题）
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# ============================================================
# CORS 跨域配置
# ============================================================

# 允许携带认证信息的跨域请求来源
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3008',
    'http://127.0.0.1:3008',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

CORS_ALLOW_CREDENTIALS = True

# ============================================================
# CSRF 配置
# ============================================================

# 信任的 CSRF 来源（与 CORS 来源保持一致）
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:3008',
    'http://127.0.0.1:3008',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]

CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False


class DisableCSRFMiddleware:
    """对 /api/ 路径下的请求豁免 CSRF 检查。

    API 端点使用 Token 认证而非 Session 认证，
    因此不需要 CSRF 保护。该中间件通过设置
    Django 内部标记 _dont_enforce_csrf_checks 实现豁免。
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)


# ============================================================
# 日志配置
# ============================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_automation': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================================
# Swagger / OpenAPI 文档配置
# ============================================================

from api_automation.swagger_config import get_custom_swagger_settings  # noqa: E402

SWAGGER_SETTINGS = get_custom_swagger_settings()
