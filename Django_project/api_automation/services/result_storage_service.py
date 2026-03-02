"""
数据分级存储服务

根据HTTP响应状态码决定测试结果的存储详细程度，平衡存储空间和排查需求：
- HTTP 2xx（成功）: 仅存储摘要信息（方法、URL、状态码、耗时），节省空间
- HTTP 非2xx（失败）: 存储完整请求/响应详情，方便问题排查
- 异常情况: 存储完整错误信息

同时提供前端展示数据获取和存储大小估算功能。
"""

import logging
from typing import Any, Dict, Optional

from api_automation.models import ApiTestResult

logger = logging.getLogger(__name__)

# 在摘要模式下保留的关键请求头列表
KEY_HEADERS = [
    'Content-Type',
    'Authorization',
    'Accept',
    'User-Agent',
    'X-Requested-With',
]


class ResultStorageService:
    """
    数据分级存储服务

    所有方法均为静态方法，无需实例化即可使用。
    通过 save_result 入口方法自动判断存储级别。
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
        根据HTTP状态码自动选择存储级别并保存测试结果

        判断逻辑：HTTP 2xx -> 摘要存储；其他 -> 完整存储。

        Args:
            test_result: ApiTestResult模型实例（需先创建再传入）
            http_response: HTTP响应对象（用于获取status_code）
            request_data: 请求数据字典（url, method, headers, body等）
            response_data: 响应数据字典（status_code, headers, body等）
            assertion_results: 断言结果列表
            error_info: 错误信息字典
        """
        try:
            # 从多个来源尝试获取HTTP状态码
            status_code = None
            if http_response:
                status_code = getattr(http_response, 'status_code', None)
            elif response_data:
                status_code = response_data.get('status_code')
            elif test_result.response_status:
                status_code = test_result.response_status

            is_success = status_code and 200 <= status_code < 300

            if is_success:
                ResultStorageService._save_summary_only(
                    test_result, request_data, response_data, assertion_results
                )
            else:
                ResultStorageService._save_full_details(
                    test_result, request_data, response_data,
                    assertion_results, error_info
                )

            logger.debug(
                f"Saved result for {test_result.test_case.name} "
                f"(status={status_code}, success={is_success})"
            )

        except Exception as e:
            logger.error(f"Error saving result: {e}")
            # 保存失败时仍尝试存储完整信息
            ResultStorageService._save_full_details(
                test_result, request_data, response_data,
                assertion_results, error_info or {'error': str(e)}
            )

    @staticmethod
    def _save_summary_only(
        test_result: ApiTestResult,
        request_data: Optional[Dict[str, Any]],
        response_data: Optional[Dict[str, Any]],
        assertion_results: Optional[list],
    ):
        """
        摘要存储模式（HTTP 2xx成功场景）

        仅保留请求方法、URL、关键请求头、状态码、耗时等核心字段，
        清空完整数据字段以节省存储空间。

        Args:
            test_result: ApiTestResult实例
            request_data: 请求数据
            response_data: 响应数据
            assertion_results: 断言结果
        """
        if request_data:
            test_result.request_summary = {
                'method': request_data.get('method'),
                'url': request_data.get('url'),
                'headers': ResultStorageService._extract_key_headers(
                    request_data.get('headers', {})
                ),
                'content_type': request_data.get('headers', {}).get('Content-Type'),
            }

        if response_data:
            test_result.response_summary = {
                'status_code': response_data.get('status_code'),
                'response_time': response_data.get('response_time'),
                'content_length': response_data.get('content_length', 0),
                'content_type': response_data.get('headers', {}).get('Content-Type'),
            }

        # 清空完整数据字段，确保不占用多余空间
        test_result.request_full = {}
        test_result.response_full = {}
        test_result.error_info = {}

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
        完整存储模式（HTTP非2xx或异常场景）

        保留完整的请求和响应信息，包括请求头、请求体、响应头、
        响应体等，方便问题排查和回溯。

        Args:
            test_result: ApiTestResult实例
            request_data: 请求数据
            response_data: 响应数据
            assertion_results: 断言结果
            error_info: 错误信息
        """
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

        if response_data:
            test_result.response_full = {
                'status_code': response_data.get('status_code'),
                'status_text': response_data.get('status_text'),
                'response_time': response_data.get('response_time'),
                'headers': response_data.get('headers', {}),
                'body': response_data.get('body', {}),
                'content_length': response_data.get('content_length', 0),
            }

        if error_info:
            test_result.error_info = error_info

        if assertion_results:
            test_result.assertion_results = assertion_results

    @staticmethod
    def _extract_key_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        从完整请求头中提取关键字段

        在摘要模式下，只保留对排查有价值的核心请求头（如Content-Type、
        Authorization等），忽略其他次要头信息。使用不区分大小写的匹配。

        Args:
            headers: 完整的请求头字典

        Returns:
            仅包含关键字段的请求头字典
        """
        result = {}
        for key_name in KEY_HEADERS:
            for header_key, header_value in headers.items():
                if header_key.lower() == key_name.lower():
                    result[key_name] = header_value
                    break
        return result

    @staticmethod
    def get_display_data(test_result: ApiTestResult) -> Dict[str, Any]:
        """
        获取用于前端展示的测试结果数据

        根据存储级别自动选择数据来源：
        - full: 有完整数据，返回完整请求/响应信息
        - summary: 仅有摘要，返回摘要信息
        - legacy: 无分级存储数据，从旧格式字段读取（向后兼容）

        Args:
            test_result: ApiTestResult实例

        Returns:
            包含 storage_level、request、response、error_info 的展示数据
        """
        has_full_data = bool(
            test_result.request_full or test_result.response_full
        )
        has_summary_data = bool(
            test_result.request_summary or test_result.response_summary
        )

        if has_full_data:
            return {
                'storage_level': 'full',
                'request': test_result.request_full or {
                    'method': test_result.request_method,
                    'url': test_result.request_url,
                    'headers': test_result.request_headers,
                    'body': test_result.request_body,
                },
                'response': test_result.response_full or {
                    'status_code': test_result.response_status,
                    'headers': test_result.response_headers,
                    'body': test_result.response_body,
                },
                'error_info': test_result.error_info,
                'message': '状态码非200，显示完整信息',
            }

        if has_summary_data:
            return {
                'storage_level': 'summary',
                'request': test_result.request_summary,
                'response': test_result.response_summary,
                'error_info': {},
                'message': '状态码200，仅显示摘要信息',
            }

        # 旧数据兼容模式
        return {
            'storage_level': 'legacy',
            'request': {
                'method': test_result.request_method,
                'url': test_result.request_url,
                'headers': test_result.request_headers,
                'body': test_result.request_body,
            },
            'response': {
                'status_code': test_result.response_status,
                'headers': test_result.response_headers,
                'body': test_result.response_body,
            },
            'error_info': {},
            'message': '历史数据（兼容格式）',
        }

    @staticmethod
    def calculate_storage_size(test_result: ApiTestResult) -> Dict[str, int]:
        """
        估算测试结果的存储占用大小

        通过将各字段转为UTF-8字符串来粗略估算字节数。

        Args:
            test_result: ApiTestResult实例

        Returns:
            各字段的估算大小（字节）及总计
        """
        def get_size(obj):
            """估算单个对象序列化后的UTF-8字节数"""
            return len(str(obj).encode('utf-8')) if obj else 0

        sizes = {
            'request_summary': get_size(test_result.request_summary),
            'response_summary': get_size(test_result.response_summary),
            'request_full': get_size(test_result.request_full),
            'response_full': get_size(test_result.response_full),
            'error_info': get_size(test_result.error_info),
            'assertion_results': get_size(test_result.assertion_results),
        }
        sizes['total'] = sum(sizes.values())

        return sizes
