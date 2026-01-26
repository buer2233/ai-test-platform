"""
api_automation/exceptions.py

自定义异常类，用于 API 自动化模块
"""
from rest_framework.exceptions import APIException


class APIAutomationException(APIException):
    """API 自动化模块基础异常类"""
    status_code = 400
    default_detail = 'API 自动化模块错误'
    default_code = 'API_AUTOMATION_ERROR'


class ValidationError(APIAutomationException):
    """数据验证错误"""
    status_code = 400
    default_detail = '数据验证失败'
    default_code = 'VALIDATION_ERROR'


class NotFoundError(APIAutomationException):
    """资源不存在错误"""
    status_code = 404
    default_detail = '请求的资源不存在'
    default_code = 'NOT_FOUND'


class PermissionDeniedError(APIAutomationException):
    """权限拒绝错误"""
    status_code = 403
    default_detail = '没有权限执行此操作'
    default_code = 'PERMISSION_DENIED'


class ExecutionError(APIAutomationException):
    """测试执行错误"""
    status_code = 500
    default_detail = '测试执行失败'
    default_code = 'EXECUTION_ERROR'


class EnvironmentConnectionError(APIAutomationException):
    """环境连接错误"""
    status_code = 400
    default_detail = '无法连接到测试环境'
    default_code = 'ENV_CONNECTION_ERROR'
