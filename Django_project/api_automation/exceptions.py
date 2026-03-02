"""
api_automation/exceptions.py

API自动化测试模块的自定义异常体系。

异常层级结构:
    APIAutomationException          -- 模块基础异常（HTTP 400）
    ├── ValidationError             -- 数据验证失败（HTTP 400）
    ├── NotFoundError               -- 资源不存在（HTTP 404）
    ├── PermissionDeniedError       -- 权限不足（HTTP 403）
    ├── ExecutionError              -- 测试执行失败（HTTP 500）
    └── EnvironmentConnectionError  -- 环境连接失败（HTTP 400）

所有异常均继承自 DRF 的 APIException，可被全局异常处理中间件统一捕获。
"""
from rest_framework.exceptions import APIException


class APIAutomationException(APIException):
    """
    API自动化模块基础异常。

    作为模块内所有自定义异常的基类，便于在全局异常处理器中
    统一识别和处理来自本模块的异常。
    """

    status_code = 400
    default_detail = 'API 自动化模块错误'
    default_code = 'API_AUTOMATION_ERROR'


class ValidationError(APIAutomationException):
    """数据验证异常，当请求数据不符合业务规则时抛出。"""

    status_code = 400
    default_detail = '数据验证失败'
    default_code = 'VALIDATION_ERROR'


class NotFoundError(APIAutomationException):
    """资源不存在异常，当请求的数据库记录不存在时抛出。"""

    status_code = 404
    default_detail = '请求的资源不存在'
    default_code = 'NOT_FOUND'


class PermissionDeniedError(APIAutomationException):
    """权限拒绝异常，当用户无权执行指定操作时抛出。"""

    status_code = 403
    default_detail = '没有权限执行此操作'
    default_code = 'PERMISSION_DENIED'


class ExecutionError(APIAutomationException):
    """测试执行异常，当测试用例执行过程中出现不可恢复错误时抛出。"""

    status_code = 500
    default_detail = '测试执行失败'
    default_code = 'EXECUTION_ERROR'


class EnvironmentConnectionError(APIAutomationException):
    """环境连接异常，当无法连接到指定测试环境时抛出。"""

    status_code = 400
    default_detail = '无法连接到测试环境'
    default_code = 'ENV_CONNECTION_ERROR'
