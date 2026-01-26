"""
WebSocket服务
负责在测试执行过程中广播实时更新
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketBroadcastService:
    """
    WebSocket广播服务
    用于向所有连接的客户端广播测试执行状态更新
    """

    def __init__(self):
        self.enabled = True

    def broadcast_execution_status(
        self,
        execution_id: int,
        status: str,
        message: Optional[str] = None
    ):
        """
        广播执行状态更新

        Args:
            execution_id: 执行ID
            status: 状态 (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
            message: 可选的消息
        """
        if not self.enabled:
            return

        try:
            from .consumers import broadcast_execution_status
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'status': status,
                'message': message or self._get_status_message(status),
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'execution.update',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted status {status} for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting execution status: {str(e)}")

    def broadcast_test_result(
        self,
        execution_id: int,
        test_case_id: int,
        test_case_name: str,
        result: str,
        response_time: Optional[int] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        广播单个测试用例结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            result: 结果 (PASSED, FAILED, SKIPPED)
            response_time: 响应时间(毫秒)
            status_code: HTTP状态码
            error_message: 错误消息
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'test_case_id': test_case_id,
                'test_case_name': test_case_name,
                'result': result,
                'response_time': response_time,
                'status_code': status_code,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'test.result',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted test result {result} for test case {test_case_name} (execution {execution_id})")

        except Exception as e:
            logger.error(f"Error broadcasting test result: {str(e)}")

    def broadcast_execution_progress(
        self,
        execution_id: int,
        current: int,
        total: int,
        passed_count: int = 0,
        failed_count: int = 0
    ):
        """
        广播执行进度

        Args:
            execution_id: 执行ID
            current: 当前执行的索引
            total: 总数
            passed_count: 通过数量
            failed_count: 失败数量
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            percentage = int((current / total) * 100) if total > 0 else 0

            data = {
                'execution_id': execution_id,
                'current': current,
                'total': total,
                'percentage': percentage,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'execution.progress',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted progress {current}/{total} ({percentage}%) for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting execution progress: {str(e)}")

    def broadcast_execution_log(
        self,
        execution_id: int,
        level: str,
        message: str,
        test_case_name: Optional[str] = None
    ):
        """
        广播执行日志

        Args:
            execution_id: 执行ID
            level: 日志级别 (INFO, WARNING, ERROR, DEBUG)
            message: 日志消息
            test_case_name: 关联的测试用例名称(可选)
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'level': level,
                'message': message,
                'test_case_name': test_case_name,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'execution.log',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted log [{level}] for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting execution log: {str(e)}")

    def broadcast_assertion_result(
        self,
        execution_id: int,
        test_case_id: int,
        test_case_name: str,
        assertion_type: str,
        assertion_operator: str,
        expected_value: Any,
        actual_value: Any,
        passed: bool,
        error_message: Optional[str] = None
    ):
        """
        广播断言结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            assertion_type: 断言类型
            assertion_operator: 断言操作符
            expected_value: 期望值
            actual_value: 实际值
            passed: 是否通过
            error_message: 错误消息
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'test_case_id': test_case_id,
                'test_case_name': test_case_name,
                'assertion_type': assertion_type,
                'assertion_operator': assertion_operator,
                'expected_value': str(expected_value),
                'actual_value': str(actual_value),
                'passed': passed,
                'error_message': error_message,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'assertion.result',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted assertion result ({'passed' if passed else 'failed'}) for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting assertion result: {str(e)}")

    def broadcast_variable_extracted(
        self,
        execution_id: int,
        test_case_id: int,
        test_case_name: str,
        variable_name: str,
        variable_value: Any,
        extract_type: str
    ):
        """
        广播变量提取结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            variable_name: 变量名
            variable_value: 变量值
            extract_type: 提取类型
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'test_case_id': test_case_id,
                'test_case_name': test_case_name,
                'variable_name': variable_name,
                'variable_value': str(variable_value),
                'extract_type': extract_type,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'variable.extracted',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted variable extracted {variable_name} for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting variable extracted: {str(e)}")

    def broadcast_error(
        self,
        execution_id: int,
        error_type: str,
        error_message: str,
        test_case_name: Optional[str] = None
    ):
        """
        广播错误信息

        Args:
            execution_id: 执行ID
            error_type: 错误类型
            error_message: 错误消息
            test_case_name: 关联的测试用例名称(可选)
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            data = {
                'execution_id': execution_id,
                'error_type': error_type,
                'error_message': error_message,
                'test_case_name': test_case_name,
                'timestamp': datetime.now().isoformat()
            }

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'execution.error',
                    'data': data
                }
            )

            logger.debug(f"Broadcasted error [{error_type}] for execution {execution_id}")

        except Exception as e:
            logger.error(f"Error broadcasting error: {str(e)}")

    def _get_status_message(self, status: str) -> str:
        """获取状态消息"""
        messages = {
            'PENDING': '测试准备中...',
            'RUNNING': '测试执行中...',
            'COMPLETED': '测试执行完成',
            'FAILED': '测试执行失败',
            'CANCELLED': '测试已取消',
        }
        return messages.get(status, f'状态变更为: {status}')

    def broadcast_execution_update(self, execution_id: int, data: Dict[str, Any]):
        """
        广播执行更新（兼容方法）

        这是 broadcast_execution_status 的别名，用于向后兼容
        """
        status = data.get('status', 'PENDING')
        message = data.get('message')
        return self.broadcast_execution_status(execution_id, status, message)


# 全局单例实例
websocket_service = WebSocketBroadcastService()
