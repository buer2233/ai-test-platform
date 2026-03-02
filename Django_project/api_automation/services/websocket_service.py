"""
WebSocket广播服务

负责在测试执行过程中，通过Django Channels将实时状态更新
推送到前端客户端。支持以下类型的广播：
- 执行状态变更（开始、完成、失败、取消）
- 单条测试用例结果
- 执行进度百分比
- 执行日志
- 断言结果
- 变量提取结果
- 错误信息
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WebSocketBroadcastService:
    """
    WebSocket广播服务

    所有广播方法都是「尽力而为」——如果Django Channels未配置或
    发送失败，仅记录错误日志而不影响主流程。每个广播方法内部
    延迟导入channels相关模块，避免在channels未安装时导致导入错误。
    """

    def __init__(self):
        self.enabled = True  # 全局开关，可在运行时禁用广播

    def _send_to_group(
        self,
        execution_id: int,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        通用的组消息发送方法

        将消息发送到执行ID对应的channel group。
        所有广播方法的底层实现。

        Args:
            execution_id: 执行ID（决定channel group名称）
            event_type: 事件类型（如 execution.update, test.result）
            data: 事件数据字典
        """
        if not self.enabled:
            return

        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            group_name = f'execution_{execution_id}'

            # 统一添加时间戳
            data['timestamp'] = datetime.now().isoformat()

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': event_type,
                    'data': data
                }
            )

            logger.debug(
                f"Broadcasted {event_type} for execution {execution_id}"
            )

        except Exception as e:
            logger.error(f"Error broadcasting {event_type}: {str(e)}")

    def broadcast_execution_status(
        self,
        execution_id: int,
        status: str,
        message: Optional[str] = None
    ):
        """
        广播执行状态变更

        Args:
            execution_id: 执行ID
            status: 状态码 (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
            message: 可选的状态描述消息
        """
        self._send_to_group(execution_id, 'execution.update', {
            'execution_id': execution_id,
            'status': status,
            'message': message or self._get_status_message(status),
        })

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
        广播单个测试用例的执行结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            result: 结果状态 (PASSED, FAILED, SKIPPED)
            response_time: 响应时间（毫秒）
            status_code: HTTP状态码
            error_message: 错误消息
        """
        self._send_to_group(execution_id, 'test.result', {
            'execution_id': execution_id,
            'test_case_id': test_case_id,
            'test_case_name': test_case_name,
            'result': result,
            'response_time': response_time,
            'status_code': status_code,
            'error_message': error_message,
        })

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
            current: 当前已执行的用例数
            total: 总用例数
            passed_count: 已通过数量
            failed_count: 已失败数量
        """
        percentage = int((current / total) * 100) if total > 0 else 0

        self._send_to_group(execution_id, 'execution.progress', {
            'execution_id': execution_id,
            'current': current,
            'total': total,
            'percentage': percentage,
            'passed_count': passed_count,
            'failed_count': failed_count,
        })

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
            message: 日志消息内容
            test_case_name: 关联的测试用例名称（可选）
        """
        self._send_to_group(execution_id, 'execution.log', {
            'execution_id': execution_id,
            'level': level,
            'message': message,
            'test_case_name': test_case_name,
        })

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
        广播单条断言的执行结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            assertion_type: 断言类型
            assertion_operator: 比较操作符
            expected_value: 期望值
            actual_value: 实际值
            passed: 是否通过
            error_message: 错误消息
        """
        self._send_to_group(execution_id, 'assertion.result', {
            'execution_id': execution_id,
            'test_case_id': test_case_id,
            'test_case_name': test_case_name,
            'assertion_type': assertion_type,
            'assertion_operator': assertion_operator,
            'expected_value': str(expected_value),
            'actual_value': str(actual_value),
            'passed': passed,
            'error_message': error_message,
        })

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
            variable_name: 提取的变量名
            variable_value: 提取到的值
            extract_type: 提取方式
        """
        self._send_to_group(execution_id, 'variable.extracted', {
            'execution_id': execution_id,
            'test_case_id': test_case_id,
            'test_case_name': test_case_name,
            'variable_name': variable_name,
            'variable_value': str(variable_value),
            'extract_type': extract_type,
        })

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
            error_type: 错误类型分类
            error_message: 错误详细消息
            test_case_name: 关联的测试用例名称（可选）
        """
        self._send_to_group(execution_id, 'execution.error', {
            'execution_id': execution_id,
            'error_type': error_type,
            'error_message': error_message,
            'test_case_name': test_case_name,
        })

    def _get_status_message(self, status: str) -> str:
        """
        将执行状态码转换为用户友好的中文消息

        Args:
            status: 状态码

        Returns:
            对应的中文描述消息
        """
        status_messages = {
            'PENDING': '测试准备中...',
            'RUNNING': '测试执行中...',
            'COMPLETED': '测试执行完成',
            'FAILED': '测试执行失败',
            'CANCELLED': '测试已取消',
        }
        return status_messages.get(status, f'状态变更为: {status}')


# 全局单例实例，供其他模块直接导入使用
websocket_service = WebSocketBroadcastService()
