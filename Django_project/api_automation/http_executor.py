"""
HTTP执行器API视图
支持直接执行HTTP请求，不依赖于测试用例
"""

import json
import time
from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from api_automation.services.http_executor import HttpExecutor
from api_automation.services.assertion_engine import AssertionEngine
from api_automation.models import ApiTestExecution, ApiTestResult


@swagger_auto_schema(
    method='POST',
    tags=['HTTP Executor'],
    operation_description='直接执行HTTP请求',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'method': openapi.Schema(type=openapi.TYPE_STRING, description='HTTP方法'),
            'url': openapi.Schema(type=openapi.TYPE_STRING, description='请求URL'),
            'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
            'params': openapi.Schema(type=openapi.TYPE_OBJECT, description='查询参数'),
            'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体'),
            'variables': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description='变量列表'),
            'tests': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description='断言测试'),
        }
    )
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_http_request(request: Request):
    """
    直接执行HTTP请求
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

        # 创建HTTP执行器
        timeout = settings.get('timeout', 30)
        verify_ssl = settings.get('verify_ssl', True)
        executor = HttpExecutor(timeout=timeout, verify_ssl=verify_ssl)

        # 执行请求
        start_time = time.time()
        response = executor.execute_request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            body=body,
            global_variables=variables
        )
        execution_time = time.time() - start_time

        # 处理响应
        response_data = {
            'status_code': response.status_code,
            'headers': response.headers,
            'body': response.body,
            'response_time': response.response_time,
            'body_size': response.body_size,
            'execution_time': round(execution_time * 1000)  # 转换为毫秒
        }

        # 如果有错误，添加到响应中
        if response.error:
            response_data['error'] = response.error

        # 处理cookies
        if 'set-cookie' in response.headers:
            cookies = {}
            cookie_header = response.headers['set-cookie']
            if isinstance(cookie_header, list):
                for cookie in cookie_header:
                    parts = cookie.split(';')[0]
                    if '=' in parts:
                        key, value = parts.split('=', 1)
                        cookies[key] = value
            else:
                parts = cookie_header.split(';')[0]
                if '=' in parts:
                    key, value = parts.split('=', 1)
                    cookies[key] = value
            response_data['cookies'] = cookies

        # 执行断言测试
        assertion_results = []
        if tests and response.error is None:
            assertion_engine = AssertionEngine()
            assertion_results = assertion_engine.run_assertions(response, tests)

        response_data['assertion_results'] = assertion_results

        # 计算断言统计
        passed_count = sum(1 for r in assertion_results if r.passed)
        failed_count = len(assertion_results) - passed_count

        response_data['assertion_summary'] = {
            'total': len(assertion_results),
            'passed': passed_count,
            'failed': failed_count
        }

        # 记录执行历史（可选）
        if data.get('save_history', False):
            execution_record_id = save_execution_history(request.user, {
                'request': {
                    'method': method,
                    'url': url,
                    'base_url': '',
                    'headers': headers,
                    'params': params,
                    'body': body
                },
                'response': response_data
            })
            if execution_record_id:
                response_data['execution_record_id'] = execution_record_id

        return Response({
            'code': 200,
            'message': 'success',
            'data': response_data
        })

    except Exception as e:
        return Response({
            'code': 500,
            'message': f'请求执行失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    """
    try:
        requests_data = request.data.get('requests', [])
        results = []

        for i, req_data in enumerate(requests_data):
            try:
                result = execute_single_request(req_data)
                results.append({
                    'index': i,
                    'success': True,
                    'data': result
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })

        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'total': len(requests_data),
                'success_count': sum(1 for r in results if r['success']),
                'failed_count': sum(1 for r in results if not r['success']),
                'results': results
            }
        })

    except Exception as e:
        return Response({
            'code': 500,
            'message': f'批量执行失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def execute_single_request(request_data):
    """执行单个HTTP请求的内部函数"""
    method = request_data.get('method', 'GET')
    url = request_data.get('url', '')
    headers = request_data.get('headers', {})
    params = request_data.get('params', {})
    body = request_data.get('body')
    variables = request_data.get('variables', {})
    settings = request_data.get('settings', {})

    # 创建HTTP执行器
    timeout = settings.get('timeout', 30)
    verify_ssl = settings.get('verify_ssl', True)
    executor = HttpExecutor(timeout=timeout, verify_ssl=verify_ssl)

    # 执行请求
    response = executor.execute_request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        body=body,
        global_variables=variables
    )

    # 返回响应数据
    return {
        'status_code': response.status_code,
        'headers': response.headers,
        'body': response.body,
        'response_time': response.response_time,
        'body_size': response.body_size,
        'error': response.error
    }


def save_execution_history(user, execution_data):
    """保存执行历史到ApiHttpExecutionRecord模型"""
    try:
        from api_automation.models import ApiHttpExecutionRecord
        from urllib.parse import urljoin

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

        # 计算请求大小
        import json
        request_size = 0
        request_size += len(method or '')
        request_size += len(full_url or '')
        headers = request_data.get('headers', {})
        request_size += len(json.dumps(headers))
        params = request_data.get('params', {})
        if params:
            request_size += len(json.dumps(params))
        body = request_data.get('body')
        if body:
            request_size += len(json.dumps(body))

        # 确定执行状态
        status_code = response_data.get('status_code', 0)
        error = response_data.get('error')
        if error:
            status_record = 'ERROR'
            error_type = 'RequestError'
            error_message = error
        elif 200 <= status_code < 300:
            status_record = 'SUCCESS'
            error_type = None
            error_message = None
        elif 300 <= status_code < 400:
            status_record = 'SUCCESS'
            error_type = None
            error_message = None
        else:
            status_record = 'FAILED'
            error_type = 'HTTPError'
            error_message = f'HTTP {status_code}'

        # 处理断言结果
        assertion_results_data = response_data.get('assertion_results', [])
        assertions_passed = response_data.get('assertion_summary', {}).get('passed', 0)
        assertions_failed = response_data.get('assertion_summary', {}).get('failed', 0)

        # 如果有断言失败，更新状态
        if assertion_results_data and assertions_failed > 0:
            status_record = 'FAILED'
            error_message = '断言失败'

        # 创建执行记录（不关联test_case，因为是直接执行）
        execution_record = ApiHttpExecutionRecord.objects.create(
            project=None,  # 直接执行没有关联项目
            test_case=None,  # 直接执行没有关联测试用例
            environment=None,  # 直接执行没有关联环境
            execution=None,  # 直接执行不关联批次
            execution_source='API',  # API触发

            # 请求信息
            request_method=method,
            request_url=full_url,
            request_base_url=base_url,
            request_path=url,
            request_headers=headers,
            request_params=params,
            request_body=body,
            request_size=request_size,

            # 时间信息
            request_time=timezone.now(),
            response_time=timezone.now(),
            duration=response_data.get('response_time', 0) or response_data.get('execution_time', 0),

            # 响应信息
            response_status=status_code,
            response_status_text='',
            response_headers=response_data.get('headers', {}),
            response_body=response_data.get('body', {}) if isinstance(response_data.get('body'), (dict, list)) else {},
            response_body_text=response_data.get('body') if not isinstance(response_data.get('body'), (dict, list)) else None,
            response_size=response_data.get('body_size', 0),
            response_encoding='utf-8',

            # 状态信息
            status=status_record,
            error_type=error_type,
            error_message=error_message,
            stack_trace=None,

            # 断言结果
            assertion_results=assertion_results_data,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,

            # 执行者
            executed_by=user
        )

        return execution_record.id

    except Exception as e:
        import traceback
        print(f"Failed to save execution history: {e}")
        print(traceback.format_exc())
        return None


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
    """
    try:
        # 这里应该从数据库获取历史记录
        # 暂时返回空列表
        return Response({
            'code': 200,
            'message': 'success',
            'data': {
                'count': 0,
                'results': []
            }
        })

    except Exception as e:
        return Response({
            'code': 500,
            'message': f'获取历史记录失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    """
    try:
        # 这里应该实现取消逻辑
        return Response({
            'code': 200,
            'message': 'execution cancelled',
            'data': None
        })

    except Exception as e:
        return Response({
            'code': 500,
            'message': f'取消执行失败: {str(e)}',
            'data': None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)