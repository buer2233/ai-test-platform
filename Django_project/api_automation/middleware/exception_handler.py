"""
api_automation/middleware/exception_handler.py

全局异常处理中间件。
捕获所有未被视图层处理的异常，将其转换为统一的 JSON 错误响应格式。

响应格式:
    {
        "code": <HTTP状态码>,
        "message": <用户可读的错误描述>,
        "details": <附加详情（仅部分异常包含）>,
        "timestamp": <ISO 8601 时间戳>
    }

异常处理优先级:
    1. APIAutomationException  -- 本模块自定义异常
    2. DRFValidationError      -- DRF 数据验证异常
    3. PermissionDenied         -- Django 权限拒绝
    4. Http404                  -- 资源不存在
    5. APIException             -- DRF 通用异常
    6. 其他未知异常             -- 记录日志，返回 500
"""
import logging
import traceback
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError as DRFValidationError

from api_automation.exceptions import APIAutomationException

logger = logging.getLogger(__name__)


class GlobalExceptionHandler:
    """
    全局异常处理中间件。

    作为 Django 中间件注册后，会自动拦截视图中未捕获的异常，
    生成统一格式的 JSON 错误响应返回给客户端。
    """

    def __init__(self, get_response):
        """初始化中间件，保存后续处理链。"""
        self.get_response = get_response

    def __call__(self, request):
        """正常请求的处理入口，直接传递给下一层中间件或视图。"""
        return self.get_response(request)

    def process_exception(self, request, exception):
        """
        异常处理钩子，将各类异常映射为标准化的 JSON 响应。

        参数:
            request: 当前 HTTP 请求对象
            exception: 视图中抛出的未捕获异常

        返回:
            JsonResponse: 包含错误码、消息和时间戳的标准响应
        """
        error_response = {
            'code': 500,
            'message': '服务器内部错误',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        if isinstance(exception, APIAutomationException):
            # 本模块自定义异常，直接使用异常中的状态码和消息
            error_response['code'] = exception.status_code
            error_response['message'] = str(exception.detail)
            error_response['details'] = getattr(exception, 'details', {})

        elif isinstance(exception, DRFValidationError):
            # DRF 数据验证异常，附带字段级错误详情
            error_response['code'] = 400
            error_response['message'] = '数据验证失败'
            error_response['details'] = exception.detail

        elif isinstance(exception, PermissionDenied):
            error_response['code'] = 403
            error_response['message'] = '没有权限执行此操作'

        elif isinstance(exception, Http404):
            error_response['code'] = 404
            error_response['message'] = '请求的资源不存在'

        elif isinstance(exception, APIException):
            # DRF 其他 API 异常（如认证失败、限流等）
            error_response['code'] = exception.status_code
            error_response['message'] = str(exception.detail)

        else:
            # 未知异常：记录完整堆栈，对客户端隐藏实现细节
            logger.error(
                "未处理的异常: %s: %s\n%s",
                type(exception).__name__,
                str(exception),
                traceback.format_exc()
            )

        return JsonResponse(error_response, status=error_response['code'])
