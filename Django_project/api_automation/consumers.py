"""
WebSocket消费者
负责实时推送测试执行状态
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class ExecutionStatusConsumer(AsyncWebsocketConsumer):
    """
    测试执行状态WebSocket消费者

    支持的消息类型:
    - status: 执行状态更新 (pending/running/completed/failed/cancelled)
    - test_result: 单个测试用例结果
    - log: 执行日志
    - variable_extracted: 变量提取通知
    - assertion_result: 断言结果
    - progress: 执行进度
    - error: 错误信息
    """

    async def connect(self):
        """处理WebSocket连接"""
        # 获取执行ID
        self.execution_id = self.scope['url_route']['kwargs'].get('execution_id')
        self.execution_group_name = f'execution_{self.execution_id}'

        # 验证用户身份 (可选, 根据需求决定是否需要认证)
        user = self.scope.get('user')
        if user is None or not user.is_authenticated:
            # 如果需要认证，拒绝连接
            # await self.close()
            # return
            pass

        try:
            # 验证执行ID是否有效
            execution_exists = await self.check_execution_exists(self.execution_id)
            if not execution_exists:
                logger.warning(f"Execution {self.execution_id} does not exist")
                await self.close(code=4004, reason='Execution not found')
                return

            # 加入执行组
            await self.channel_layer.group_add(
                self.execution_group_name,
                self.channel_name
            )

            # 接受连接
            await self.accept()

            logger.info(f"WebSocket connected for execution {self.execution_id}")

            # 发送连接成功消息
            await self.send(text_data=json.dumps({
                'type': 'connected',
                'execution_id': self.execution_id,
                'message': 'WebSocket连接成功'
            }))

        except Exception as e:
            logger.error(f"Error connecting WebSocket: {str(e)}")
            await self.close(code=4000, reason=str(e))

    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        try:
            # 离开执行组
            await self.channel_layer.group_discard(
                self.execution_group_name,
                self.channel_name
            )

            logger.info(f"WebSocket disconnected for execution {self.execution_id} (code: {close_code})")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")

    async def receive(self, text_data):
        """接收来自客户端的消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            logger.debug(f"Received message: {message_type} from execution {self.execution_id}")

            # 处理客户端消息
            if message_type == 'ping':
                # 心跳检测
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))

            elif message_type == 'subscribe':
                # 订阅特定事件类型
                event_types = data.get('event_types', [])
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'event_types': event_types
                }))

            elif message_type == 'cancel':
                # 取消执行请求 (转发到执行服务)
                user = self.scope.get('user')
                await self.channel_layer.group_send(
                    self.execution_group_name,
                    {
                        'type': 'cancel_execution',
                        'execution_id': self.execution_id,
                        'user': str(user) if user else 'anonymous'
                    }
                )

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")

    async def execution_update(self, event):
        """发送执行状态更新"""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'data': event.get('data')
        }))

    async def test_result(self, event):
        """发送测试结果"""
        await self.send(text_data=json.dumps({
            'type': 'test_result',
            'data': event.get('data')
        }))

    async def execution_log(self, event):
        """发送执行日志"""
        await self.send(text_data=json.dumps({
            'type': 'log',
            'data': event.get('data')
        }))

    async def variable_extracted(self, event):
        """发送变量提取通知"""
        await self.send(text_data=json.dumps({
            'type': 'variable_extracted',
            'data': event.get('data')
        }))

    async def assertion_result(self, event):
        """发送断言结果"""
        await self.send(text_data=json.dumps({
            'type': 'assertion_result',
            'data': event.get('data')
        }))

    async def execution_progress(self, event):
        """发送执行进度"""
        await self.send(text_data=json.dumps({
            'type': 'progress',
            'data': event.get('data')
        }))

    async def execution_error(self, event):
        """发送错误信息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'data': event.get('data')
        }))

    @database_sync_to_async
    def check_execution_exists(self, execution_id):
        """检查执行记录是否存在"""
        try:
            from api_automation.models import ApiTestExecution
            return ApiTestExecution.objects.filter(
                id=execution_id,
                is_deleted=False
            ).exists()
        except Exception as e:
            logger.error(f"Error checking execution exists: {str(e)}")
            return False


# 辅助函数: 用于从执行服务发送WebSocket消息
async def broadcast_execution_update(execution_id, update_type, data):
    """
    广播执行更新到所有订阅的客户端

    Args:
        execution_id: 执行ID
        update_type: 更新类型 (status, test_result, log, etc.)
        data: 更新数据
    """
    try:
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        group_name = f'execution_{execution_id}'

        # 根据更新类型选择处理方法
        type_mapping = {
            'status': 'execution.update',
            'test_result': 'test.result',
            'log': 'execution.log',
            'variable_extracted': 'variable.extracted',
            'assertion_result': 'assertion.result',
            'progress': 'execution.progress',
            'error': 'execution.error',
        }

        message_type = type_mapping.get(update_type, 'execution.update')

        await channel_layer.group_send(
            group_name,
            {
                'type': message_type,
                'data': data
            }
        )

        logger.debug(f"Broadcasted {update_type} for execution {execution_id}")

    except Exception as e:
        logger.error(f"Error broadcasting execution update: {str(e)}")


# 同步版本的辅助函数 (用于在同步上下文中调用)
def broadcast_execution_status(execution_id, status_data):
    """
    同步函数: 广播执行状态更新

    Args:
        execution_id: 执行ID
        status_data: 状态数据字典
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'execution.update',
                'data': status_data
            }
        )

    except Exception as e:
        logger.error(f"Error broadcasting execution status: {str(e)}")


def broadcast_test_result(execution_id, result_data):
    """
    同步函数: 广播测试结果

    Args:
        execution_id: 执行ID
        result_data: 测试结果数据字典
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'test.result',
                'data': result_data
            }
        )

    except Exception as e:
        logger.error(f"Error broadcasting test result: {str(e)}")


def broadcast_execution_log(execution_id, log_data):
    """
    同步函数: 广播执行日志

    Args:
        execution_id: 执行ID
        log_data: 日志数据字典
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'execution.log',
                'data': log_data
            }
        )

    except Exception as e:
        logger.error(f"Error broadcasting execution log: {str(e)}")


def broadcast_execution_progress(execution_id, progress_data):
    """
    同步函数: 广播执行进度

    Args:
        execution_id: 执行ID
        progress_data: 进度数据字典
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        group_name = f'execution_{execution_id}'

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'execution.progress',
                'data': progress_data
            }
        )

    except Exception as e:
        logger.error(f"Error broadcasting execution progress: {str(e)}")
