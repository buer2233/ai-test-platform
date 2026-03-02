"""
HTTP执行器 - API视图层

提供直接执行HTTP请求的REST API端点，不依赖于测试用例。
支持单次执行、批量执行、执行历史保存和查询。

端点列表：
- POST /execute/      - 执行单个HTTP请求
- POST /batch/        - 批量执行多个HTTP请求
- GET  /history/      - 获取执行历史记录
- POST /cancel/{id}/  - 取消正在执行的请求
"""

import json
import logging
import time

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from api_automation.models import ApiTestExecution, ApiTestResult
from api_automation.services.assertion_engine import AssertionEngine
from api_automation.services.http_executor import HttpExecutor

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='POST',
    tags=['HTTP Executor'],
    operation_description='直接执行HTTP请求',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'method': openapi.Schema(
                type=openapi.TYPE_STRING, description='HTTP方法'
            ),
            'url': openapi.Schema(
                type=openapi.TYPE_STRING, description='请求URL'
            ),
            'headers': openapi.Schema(
                type=openapi.TYPE_OBJECT, description='请求头'
            ),
            'params': openapi.Schema(
                type=openapi.TYPE_OBJECT, description='查询参数'
            ),
            'body': openapi.Schema(
                type=openapi.TYPE_OBJECT, description='请求体'
            ),
            'variables': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                description='变量列表'
            ),
            'tests': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                description='断言测试'
            ),
        }
    )
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_http_request(request: Request):
    """
    直接执行HTTP请求

    接受请求参数，创建HTTP执行器发送请求，执行断言，
    可选保存执行历史。返回完整的响应数据和断言结果。
    """
    try:
        data = request.data
        method = data.get('method', 'GET')
        url = data.get('url', '')
        headers = data.get('headers', {})
        params = data.get('params', {})
        body = data.get('body')
        variables = data.get('variables', {})
        settings = data.get('settings', {})
        tests = data.get('tests', [])

        # 创建执行器并发送请求
        timeout = settings.get('timeout', 30)
        verify_ssl = settings.get('verify_ssl', True)
        executor = HttpExecutor(timeout=timeout, verify_ssl=verify_ssl)

        start_time = time.time()
        response = executor.execute_request(
            method=method, url=url, headers=headers,
            params=params, body=body, global_variables=variables
        )
        execution_time = time.time() - start_time

        # 构建响应数据
        response_data = {
            'status_code': response.status_code,
            'headers': response.headers,
            'body': response.body,
            'response_time': response.response_time,
            'body_size': response.body_size,
            'execution_time': round(execution_time * 1000),
        }

        if response.error:
            response_data['error'] = response.error

        # 解析Set-Cookie响应头
        cookies = _parse_cookies(response.headers)
        if cookies:
            response_data['cookies'] = cookies

        # 执行断言测试
        assertion_results = []
        if tests and response.error is None:
            assertion_engine = AssertionEngine()
            assertion_results = assertion_engine.run_assertions(response, tests)

        response_data['assertion_results'] = assertion_results

        # 断言统计
        passed_count = sum(1 for r in assertion_results if r.passed)
        response_data['assertion_summary'] = {
            'total': len(assertion_results),
            'passed': passed_count,
            'failed': len(assertion_results) - passed_count,
        }

        # 可选保存执行历史
        if data.get('save_history', False):
            record_id = save_execution_history(request.user, {
                'request': {
                    'method': method, 'url': url, 'base_url': '',
                    'headers': headers, 'params': params, 'body': body
                },
                'response': response_data
            })
            if record_id:
                response_data['execution_record_id'] = record_id

        return Response({
            'code': 200, 'message': 'success', 'data': response_data
        })

    except Exception as e:
        return Response(
            {'code': 500, 'message': f'请求执行失败: {str(e)}', 'data': None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _parse_cookies(headers: dict) -> dict:
    """
    从响应头中解析Set-Cookie字段

    Args:
        headers: 响应头字典

    Returns:
        解析后的 {cookie名: cookie值} 字典，无Cookie时返回空字典
    """
    if 'set-cookie' not in headers:
        return {}

    cookies = {}
    cookie_header = headers['set-cookie']

    # Set-Cookie可能是列表（多个Cookie）或单个字符串
    cookie_items = cookie_header if isinstance(cookie_header, list) else [cookie_header]

    for cookie in cookie_items:
        name_value_part = cookie.split(';')[0]
        if '=' in name_value_part:
            key, value = name_value_part.split('=', 1)
            cookies[key] = value

    return cookies


@swagger_auto_schema(
    method='POST',
    tags=['HTTP Executor'],
    operation_description='批量执行HTTP请求'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_batch_requests(request: Request):
    """
    批量执行HTTP请求

    接受请求数组，逐条执行并返回汇总结果。
    单条请求失败不影响后续请求的执行。
    """
    try:
        requests_data = request.data.get('requests', [])
        results = []

        for i, req_data in enumerate(requests_data):
            try:
                result = execute_single_request(req_data)
                results.append({'index': i, 'success': True, 'data': result})
            except Exception as e:
                results.append({'index': i, 'success': False, 'error': str(e)})

        success_count = sum(1 for r in results if r['success'])

        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'total': len(requests_data),
                'success_count': success_count,
                'failed_count': len(requests_data) - success_count,
                'results': results
            }
        })

    except Exception as e:
        return Response(
            {'code': 500, 'message': f'批量执行失败: {str(e)}', 'data': None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def execute_single_request(request_data: dict) -> dict:
    """
    执行单个HTTP请求的内部函数

    由 execute_batch_requests 调用，封装请求参数解析和执行逻辑。

    Args:
        request_data: 请求配置字典

    Returns:
        响应数据字典
    """
    method = request_data.get('method', 'GET')
    url = request_data.get('url', '')
    headers = request_data.get('headers', {})
    params = request_data.get('params', {})
    body = request_data.get('body')
    variables = request_data.get('variables', {})
    settings = request_data.get('settings', {})

    executor = HttpExecutor(
        timeout=settings.get('timeout', 30),
        verify_ssl=settings.get('verify_ssl', True)
    )

    response = executor.execute_request(
        method=method, url=url, headers=headers,
        params=params, body=body, global_variables=variables
    )

    return {
        'status_code': response.status_code,
        'headers': response.headers,
        'body': response.body,
        'response_time': response.response_time,
        'body_size': response.body_size,
        'error': response.error
    }


def save_execution_history(user, execution_data: dict):
    """
    保存HTTP请求执行历史到 ApiHttpExecutionRecord 模型

    将请求和响应数据持久化存储，包含请求方法、URL、请求头、
    请求体、响应状态、响应体、断言结果等完整信息。

    Args:
        user: 执行用户对象
        execution_data: 包含 request 和 response 子字典的执行数据

    Returns:
        保存成功返回记录ID，失败返回None
    """
    try:
        from urllib.parse import urljoin

        from django.utils import timezone

        from api_automation.models import ApiHttpExecutionRecord

        request_data = execution_data.get('request', {})
        response_data = execution_data.get('response', execution_data)

        # 构建完整URL
        method = request_data.get('method', 'GET')
        url = request_data.get('url', '')
        base_url = request_data.get('base_url', '')
        if base_url:
            full_url = urljoin(base_url.rstrip('/') + '/', url.lstrip('/'))
        else:
            full_url = url

        # 估算请求大小
        headers = request_data.get('headers', {})
        params = request_data.get('params', {})
        body = request_data.get('body')
        request_size = (
            len(method or '')
            + len(full_url or '')
            + len(json.dumps(headers))
            + (len(json.dumps(params)) if params else 0)
            + (len(json.dumps(body)) if body else 0)
        )

        # 根据响应状态确定执行状态
        status_code = response_data.get('status_code', 0)
        error = response_data.get('error')
        status_record, error_type, error_message = _determine_execution_status(
            status_code, error
        )

        # 如果有断言失败，覆盖状态为FAILED
        assertion_results_data = response_data.get('assertion_results', [])
        assertions_passed = response_data.get(
            'assertion_summary', {}
        ).get('passed', 0)
        assertions_failed = response_data.get(
            'assertion_summary', {}
        ).get('failed', 0)

        if assertion_results_data and assertions_failed > 0:
            status_record = 'FAILED'
            error_message = '断言失败'

        # 处理响应体（区分JSON和文本）
        response_body_raw = response_data.get('body', {})
        if isinstance(response_body_raw, (dict, list)):
            response_body = response_body_raw
            response_body_text = None
        else:
            response_body = {}
            response_body_text = response_body_raw

        execution_record = ApiHttpExecutionRecord.objects.create(
            project=None,
            test_case=None,
            environment=None,
            execution=None,
            execution_source='API',
            request_method=method,
            request_url=full_url,
            request_base_url=base_url,
            request_path=url,
            request_headers=headers,
            request_params=params,
            request_body=body,
            request_size=request_size,
            request_time=timezone.now(),
            response_time=timezone.now(),
            duration=(
                response_data.get('response_time', 0)
                or response_data.get('execution_time', 0)
            ),
            response_status=status_code,
            response_status_text='',
            response_headers=response_data.get('headers', {}),
            response_body=response_body,
            response_body_text=response_body_text,
            response_size=response_data.get('body_size', 0),
            response_encoding='utf-8',
            status=status_record,
            error_type=error_type,
            error_message=error_message,
            stack_trace=None,
            assertion_results=assertion_results_data,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            executed_by=user
        )

        return execution_record.id

    except Exception as e:
        import traceback
        logger.error(f"Failed to save execution history: {e}")
        logger.debug(traceback.format_exc())
        return None


def _determine_execution_status(status_code: int, error: str = None) -> tuple:
    """
    根据HTTP状态码和错误信息确定执行状态

    Args:
        status_code: HTTP响应状态码
        error: 请求错误信息

    Returns:
        (status_record, error_type, error_message) 三元组
    """
    if error:
        return 'ERROR', 'RequestError', error

    if 200 <= status_code < 400:
        return 'SUCCESS', None, None

    return 'FAILED', 'HTTPError', f'HTTP {status_code}'


@swagger_auto_schema(
    method='GET',
    tags=['HTTP Executor'],
    operation_description='获取HTTP执行历史记录'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_execution_history(request: Request):
    """
    获取执行历史

    TODO: 实现从 ApiHttpExecutionRecord 查询历史记录
    """
    try:
        return Response({
            'code': 200,
            'message': 'success',
            'data': {'count': 0, 'results': []}
        })

    except Exception as e:
        return Response(
            {'code': 500, 'message': f'获取历史记录失败: {str(e)}', 'data': None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='POST',
    tags=['HTTP Executor'],
    operation_description='取消正在执行的HTTP请求'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_execution(request: Request, execution_id: str):
    """
    取消正在执行的请求

    TODO: 实现请求取消逻辑
    """
    try:
        return Response({
            'code': 200, 'message': 'execution cancelled', 'data': None
        })

    except Exception as e:
        return Response(
            {'code': 500, 'message': f'取消执行失败: {str(e)}', 'data': None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )