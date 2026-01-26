"""
WebSocket 服务模块

提供实时测试执行进度推送功能。
"""

import json
import django
from typing import Dict, Set
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class WebSocketProgressService:
    """
    WebSocket 进度推送服务

    通过 Django Channels 实现测试执行进度的实时推送。
    """

    # Channel layer 名称
    UI_AUTOMATION_GROUP = "ui_automation_progress"

    @classmethod
    def broadcast_progress(cls, execution_id: int, message: str, data: Dict = None) -> None:
        """
        广播进度更新到所有订阅的客户端

        Args:
            execution_id: 执行记录ID
            message: 进度消息
            data: 附加数据
        """
        channel_layer = get_channel_layer()

        payload = {
            'type': 'ui_automation.progress',
            'execution_id': execution_id,
            'message': message,
            'data': data or {},
        }

        # 发送到组
        async_to_sync(channel_layer.group_send)(
            cls.UI_AUTOMATION_GROUP,
            {
                'type': 'broadcast_progress',
                'payload': payload,
            }
        )

    @classmethod
    def broadcast_status_change(cls, execution_id: int, status: str, extra_data: Dict = None) -> None:
        """
        广播状态变更

        Args:
            execution_id: 执行记录ID
            status: 新状态
            extra_data: 额外数据（错误信息、完成时间等）
        """
        channel_layer = get_channel_layer()

        payload = {
            'type': 'ui_automation.status_change',
            'execution_id': execution_id,
            'status': status,
            'timestamp': django.utils.timezone.now().isoformat(),
        }

        if extra_data:
            payload.update(extra_data)

        async_to_sync(channel_layer.group_send)(
            cls.UI_AUTOMATION_GROUP,
            {
                'type': 'broadcast_status',
                'payload': payload,
            }
        )

    @classmethod
    def broadcast_error(cls, execution_id: int, error_message: str, error_details: Dict = None) -> None:
        """
        广播错误信息

        Args:
            execution_id: 执行记录ID
            error_message: 错误消息
            error_details: 错误详情
        """
        channel_layer = get_channel_layer()

        payload = {
            'type': 'ui_automation.error',
            'execution_id': execution_id,
            'error': error_message,
            'timestamp': django.utils.timezone.now().isoformat(),
        }

        if error_details:
            payload['details'] = error_details

        async_to_sync(channel_layer.group_send)(
            cls.UI_AUTOMATION_GROUP,
            {
                'type': 'broadcast_error',
                'payload': payload,
            }
        )

    @classmethod
    def broadcast_screenshot(cls, execution_id: int, screenshot_data: str) -> None:
        """
        广播新截图

        Args:
            execution_id: 执行记录ID
            screenshot_data: 截图数据
        """
        channel_layer = get_channel_layer()

        payload = {
            'type': 'ui_automation.screenshot',
            'execution_id': execution_id,
            'screenshot': screenshot_data,
        }

        async_to_sync(channel_layer.group_send)(
            cls.UI_AUTOMATION_GROUP,
            {
                'type': 'broadcast_screenshot',
                'payload': payload,
            }
        )


class UiAutomationConsumer(AsyncWebsocketConsumer):
    """
    UI 自动化测试的 WebSocket 消费者

    处理客户端连接和消息接收。
    """

    # 跟踪活跃订阅
    active_executions: Dict[str, Set[str]] = {}

    async def connect(self) -> None:
        """处理连接"""
        # 获取执行ID
        execution_id = self.scope['url_route']['kwargs'].get('execution_id')

        if execution_id:
            self.execution_id = str(execution_id)

            # 加入组
            await self.channel_layer.group_add(
                WebSocketProgressService.UI_AUTOMATION_GROUP,
                self.channel_name
            )

            # 跟踪订阅
            if self.execution_id not in self.active_executions:
                self.active_executions[self.execution_id] = set()
            self.active_executions[self.execution_id].add(self.channel_name)

            # 接受连接
            await self.accept()

            # 发送欢迎消息
            await self.send_json({
                'type': 'connected',
                'execution_id': self.execution_id,
                'message': '已连接到测试执行进度更新',
            })
        else:
            await self.close()

    async def disconnect(self, close_code: int) -> None:
        """处理断开连接"""
        # 离开组
        await self.channel_layer.group_discard(
            WebSocketProgressService.UI_AUTOMATION_GROUP,
            self.channel_name
        )

        # 移除订阅跟踪
        if hasattr(self, 'execution_id') and self.execution_id in self.active_executions:
            self.active_executions[self.execution_id].discard(self.channel_name)
            if not self.active_executions[self.execution_id]:
                del self.active_executions[self.execution_id]

    async def receive_json(self, content: Dict) -> None:
        """
        接收 JSON 消息

        Args:
            content: 消息内容
        """
        message_type = content.get('type')

        if message_type == 'ping':
            # 心跳响应
            await self.send_json({'type': 'pong'})
        elif message_type == 'subscribe':
            # 订阅特定执行
            execution_id = content.get('execution_id')
            if execution_id:
                self.execution_id = str(execution_id)

    async def send_json(self, content: Dict) -> None:
        """
        发送 JSON 消息

        Args:
            content: 消息内容
        """
        await self.send(text_data=json.dumps(content, ensure_ascii=False))

    # Channel 处理方法

    async def broadcast_progress(self, event: Dict) -> None:
        """
        处理进度广播

        Args:
            event: 事件数据
        """
        payload = event['payload']

        # 只发送给相关执行的订阅者
        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_status(self, event: Dict) -> None:
        """
        处理状态广播

        Args:
            event: 事件数据
        """
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_screenshot(self, event: Dict) -> None:
        """
        处理截图广播

        Args:
            event: 事件数据
        """
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_error(self, event: Dict) -> None:
        """
        处理错误广播

        Args:
            event: 事件数据
        """
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)


def create_progress_callback(execution_id: int):
    """
    创建进度回调函数

    Args:
        execution_id: 执行记录ID

    Returns:
        进度回调函数
    """
    def callback(progress_data: Dict) -> None:
        """内部回调函数"""
        WebSocketProgressService.broadcast_progress(
            execution_id=execution_id,
            message=progress_data.get('message', ''),
            data=progress_data.get('data', {}),
        )

    return callback


def create_screenshot_callback(execution_id: int):
    """
    创建截图回调函数

    Args:
        execution_id: 执行记录ID

    Returns:
        截图回调函数
    """
    async def async_callback(screenshot_data: str, description: str) -> None:
        """异步回调函数"""
        WebSocketProgressService.broadcast_screenshot(
            execution_id=execution_id,
            screenshot_data={
                'data': screenshot_data,
                'description': description,
            }
        )

    def callback(screenshot_data: str, description: str) -> None:
        """同步回调函数"""
        asyncio.create_task(async_callback(screenshot_data, description))

    return callback
