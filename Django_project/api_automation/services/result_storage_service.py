"""
result_storage_service.py

数据分级存储服务，根据HTTP状态码决定存储详细程度。

存储策略：
- HTTP 2xx (200-299): 仅存储摘要信息（节省空间）
- HTTP 非2xx: 存储完整请求/响应（方便排查）
- 错误情况: 存储完整错误信息
"""
import logging
from typing import Dict, Any, Optional
from api_automation.models import ApiTestResult

logger = logging.getLogger(__name__)


class ResultStorageService:
    """
    数据分级存储服务
    """

    @staticmethod
    def save_result(
        test_result: ApiTestResult,
        http_response: Optional[Any] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        assertion_results: Optional[list] = None,
        error_info: Optional[Dict[str, Any]] = None,
    ):
        """
        根据HTTP状态码分级存储测试结果

        Args:
            test_result: ApiTestResult实例
            http_response: HTTP响应对象（包含status_code, headers, body等）
            request_data: 请求数据（url, method, headers, body等）
            response_data: 响应数据（status_code, headers, body等）
            assertion_results: 断言结果列表
            error_info: 错误信息字典
        """
        try:
            # 获取HTTP状态码
            status_code = None
            if http_response:
                status_code = getattr(http_response, 'status_code', None)
            elif response_data:
                status_code = response_data.get('status_code')
            elif test_result.response_status:
                status_code = test_result.response_status

            # 判断是否为成功状态码 (2xx)
            is_success = status_code and 200 <= status_code < 300

            if is_success:
                # HTTP 200: 仅存储摘要信息
                ResultStorageService._save_summary_only(
                    test_result,
                    request_data,
                    response_data,
                    assertion_results
                )
            else:
                # HTTP 非200: 存储完整信息
                ResultStorageService._save_full_details(
                    test_result,
                    request_data,
                    response_data,
                    assertion_results,
                    error_info
                )

            logger.debug(f"Saved result for {test_result.test_case.name} (status={status_code}, success={is_success})")

        except Exception as e:
            logger.error(f"Error saving result: {e}")
            # 出错时也保存完整信息
            ResultStorageService._save_full_details(
                test_result,
                request_data,
                response_data,
                assertion_results,
                error_info or {'error': str(e)}
            )

    @staticmethod
    def _save_summary_only(
        test_result: ApiTestResult,
        request_data: Optional[Dict[str, Any]],
        response_data: Optional[Dict[str, Any]],
        assertion_results: Optional[list],
    ):
        """
        仅保存摘要信息（HTTP 200情况）

        Args:
            test_result: ApiTestResult实例
            request_data: 请求数据
            response_data: 响应数据
            assertion_results: 断言结果
        """
        # 保存请求摘要
        if request_data:
            test_result.request_summary = {
                'method': request_data.get('method'),
                'url': request_data.get('url'),
                # 仅保存关键请求头
                'headers': ResultStorageService._extract_key_headers(
                    request_data.get('headers', {})
                ),
                'content_type': request_data.get('headers', {}).get('Content-Type'),
            }

        # 保存响应摘要
        if response_data:
            test_result.response_summary = {
                'status_code': response_data.get('status_code'),
                'response_time': response_data.get('response_time'),
                'content_length': response_data.get('content_length', 0),
                'content_type': response_data.get('headers', {}).get('Content-Type'),
            }

        # 清空完整数据字段（确保不会占用空间）
        test_result.request_full = {}
        test_result.response_full = {}
        test_result.error_info = {}

        # 保存断言结果
        if assertion_results:
            test_result.assertion_results = assertion_results

    @staticmethod
    def _save_full_details(
        test_result: ApiTestResult,
        request_data: Optional[Dict[str, Any]],
        response_data: Optional[Dict[str, Any]],
        assertion_results: Optional[list],
        error_info: Optional[Dict[str, Any]],
    ):
        """
        保存完整详细信息（HTTP 非200情况）

        Args:
            test_result: ApiTestResult实例
            request_data: 请求数据
            response_data: 响应数据
            assertion_results: 断言结果
            error_info: 错误信息
        """
        # 保存完整请求信息
        if request_data:
            test_result.request_full = {
                'method': request_data.get('method'),
                'url': request_data.get('url'),
                'base_url': request_data.get('base_url'),
                'path': request_data.get('path'),
                'headers': request_data.get('headers', {}),
                'params': request_data.get('params', {}),
                'body': request_data.get('body', {}),
            }

        # 保存完整响应信息
        if response_data:
            test_result.response_full = {
                'status_code': response_data.get('status_code'),
                'status_text': response_data.get('status_text'),
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {}),
                'body': response_data.get('body', {}),
                'content_length': response_data.get('content_length', 0),
            }

        # 保存错误信息
        if error_info:
            test_result.error_info = error_info

        # 如果有断言结果，保存
        if assertion_results:
            test_result.assertion_results = assertion_results

    @staticmethod
    def _extract_key_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        提取关键请求头

        Args:
            headers: 完整请求头

        Returns:
            关键请求头
        """
        key_headers = [
            'Content-Type',
            'Authorization',
            'Accept',
            'User-Agent',
            'X-Requested-With',
        ]

        result = {}
        for key in key_headers:
            # 不区分大小写查找
            for header_key, header_value in headers.items():
                if header_key.lower() == key.lower():
                    result[key] = header_value
                    break

        return result

    @staticmethod
    def get_display_data(test_result: ApiTestResult) -> Dict[str, Any]:
        """
        获取用于前端展示的数据（根据存储情况返回）

        Args:
            test_result: ApiTestResult实例

        Returns:
            展示数据字典
        """
        status_code = test_result.response_status

        # 判断是否有完整数据
        has_full_data = bool(test_result.request_full or test_result.response_full)
        has_summary_data = bool(test_result.request_summary or test_result.response_summary)

        if has_full_data:
            # 返回完整数据
            return {
                'storage_level': 'full',
                'request': test_result.request_full or {
                    'method': test_result.request_method,
                    'url': test_result.request_url,
                    'headers': test_result.request_headers,
                    'body': test_result.request_body,
                },
                'response': test_result.response_full or {
                    'status_code': status_code,
                    'headers': test_result.response_headers,
                    'body': test_result.response_body,
                },
                'error_info': test_result.error_info,
                'message': '状态码非200，显示完整信息',
            }
        elif has_summary_data:
            # 返回摘要数据
            return {
                'storage_level': 'summary',
                'request': test_result.request_summary,
                'response': test_result.response_summary,
                'error_info': {},
                'message': '状态码200，仅显示摘要信息',
            }
        else:
            # 返回兼容数据（旧数据）
            return {
                'storage_level': 'legacy',
                'request': {
                    'method': test_result.request_method,
                    'url': test_result.request_url,
                    'headers': test_result.request_headers,
                    'body': test_result.request_body,
                },
                'response': {
                    'status_code': status_code,
                    'headers': test_result.response_headers,
                    'body': test_result.response_body,
                },
                'error_info': {},
                'message': '历史数据（兼容格式）',
            }

    @staticmethod
    def calculate_storage_size(test_result: ApiTestResult) -> Dict[str, int]:
        """
        计算存储大小（估算）

        Args:
            test_result: ApiTestResult实例

        Returns:
            存储大小信息（字节）
        """
        import sys

        def get_size(obj):
            """估算对象大小"""
            return len(str(obj).encode('utf-8')) if obj else 0

        return {
            'request_summary': get_size(test_result.request_summary),
            'response_summary': get_size(test_result.response_summary),
            'request_full': get_size(test_result.request_full),
            'response_full': get_size(test_result.response_full),
            'error_info': get_size(test_result.error_info),
            'assertion_results': get_size(test_result.assertion_results),
            'total': (
                get_size(test_result.request_summary) +
                get_size(test_result.response_summary) +
                get_size(test_result.request_full) +
                get_size(test_result.response_full) +
                get_size(test_result.error_info) +
                get_size(test_result.assertion_results)
            ),
        }
