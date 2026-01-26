"""
api_automation/middleware/exception_handler.py

全局异常处理中间件
"""
import logging
import traceback
from datetime import datetime
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from django.http import Http404
from api_automation.exceptions import APIAutomationException

logger = logging.getLogger(__name__)


class GlobalExceptionHandler:
    """全局异常处理中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """处理异常"""
        # 构建标准错误响应
        error_response = {
            'code': 500,
            'message': '服务器内部错误',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        if isinstance(exception, APIAutomationException):
            # 自定义 API 异常
            error_response['code'] = exception.status_code
            error_response['message'] = str(exception.detail)
            error_response['details'] = getattr(exception, 'details', {})

        elif isinstance(exception, DRFValidationError):
            # DRF 验证错误
            error_response['code'] = 400
            error_response['message'] = '数据验证失败'
            error_response['details'] = exception.detail

        elif isinstance(exception, (PermissionDenied, PermissionDenied)):
            # 权限错误
            error_response['code'] = 403
            error_response['message'] = '没有权限执行此操作'

        elif isinstance(exception, (Http404, Http404)):
            # 404 错误
            error_response['code'] = 404
            error_response['message'] = '请求的资源不存在'

        elif isinstance(exception, APIException):
            # DRF API 异常
            error_response['code'] = exception.status_code
            error_response['message'] = str(exception.detail)

        else:
            # 未知异常 - 记录日志
            logger.error(
                f"Unhandled exception: {type(exception).__name__}: {str(exception)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            # 生产环境不暴露详细错误信息
            error_response['message'] = '服务器内部错误'

        return JsonResponse(error_response, status=error_response['code'])
