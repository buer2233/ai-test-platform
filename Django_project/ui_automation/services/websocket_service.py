"""
WebSocket 服务模块

提供测试执行进度的实时推送功能，基于 Django Channels 实现。

核心组件:
    WebSocketProgressService - 服务端广播工具类（同步接口，内部转换为异步）
    UiAutomationConsumer     - WebSocket 消费者（处理连接、断开、消息过滤）
    create_progress_callback - 创建进度回调函数的工厂
    create_screenshot_callback - 创建截图回调函数的工厂

消息类型:
    ui_automation.progress      - 执行进度更新
    ui_automation.status_change - 执行状态变更（running/passed/failed/error）
    ui_automation.error         - 执行错误信息
    ui_automation.screenshot    - 新截图通知
"""

import asyncio
import json
from typing import Dict, Set

import django
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer


class WebSocketProgressService:
    """
    WebSocket 进度推送服务。

    通过 Django Channels 的 channel layer 实现同步代码向 WebSocket 客户端广播消息。
    所有方法均为类方法，无需实例化即可使用。

    使用方式:
        WebSocketProgressService.broadcast_progress(execution_id=1, message='开始执行')
    """

    # 所有 UI 自动化执行共用同一个 Channel Group
    UI_AUTOMATION_GROUP = "ui_automation_progress"

    @classmethod
    def broadcast_progress(cls, execution_id: int, message: str, data: Dict = None) -> None:
        """广播执行进度更新到所有订阅的客户端。"""
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
        """广播执行状态变更（如 running -> passed/failed/error）。"""
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
        """广播执行错误信息。"""
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
        """广播新截图通知。"""
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
    UI 自动化测试的 WebSocket 消费者。

    处理客户端连接、断开、消息接收和广播过滤。
    每个连接通过 URL 中的 execution_id 标识订阅的执行记录，
    只接收与自己订阅的 execution_id 匹配的消息。

    支持的客户端消息类型:
        ping      - 心跳检测，回复 pong
        subscribe - 切换订阅的 execution_id
    """

    # 类级别: 跟踪每个 execution_id 的活跃连接
    active_executions: Dict[str, Set[str]] = {}

    async def connect(self) -> None:
        """处理 WebSocket 连接请求。"""
        # 获取 URL 路由参数中的 execution_id
        execution_id = self.scope['url_route']['kwargs'].get('execution_id')

        if execution_id:
            self.execution_id = str(execution_id)

            # 加入共享的 Channel Group
            await self.channel_layer.group_add(
                WebSocketProgressService.UI_AUTOMATION_GROUP,
                self.channel_name
            )

            # 记录活跃连接
            if self.execution_id not in self.active_executions:
                self.active_executions[self.execution_id] = set()
            self.active_executions[self.execution_id].add(self.channel_name)

            await self.accept()

            # 发送连接成功确认
            await self.send_json({
                'type': 'connected',
                'execution_id': self.execution_id,
                'message': '已连接到测试执行进度更新',
            })
        else:
            await self.close()

    async def disconnect(self, close_code: int) -> None:
        """处理 WebSocket 断开连接，清理 Channel Group 和活跃连接记录。"""
        # 离开 Channel Group
        await self.channel_layer.group_discard(
            WebSocketProgressService.UI_AUTOMATION_GROUP,
            self.channel_name
        )

        # 清理活跃连接记录
        if hasattr(self, 'execution_id') and self.execution_id in self.active_executions:
            self.active_executions[self.execution_id].discard(self.channel_name)
            if not self.active_executions[self.execution_id]:
                del self.active_executions[self.execution_id]

    async def receive_json(self, content: Dict) -> None:
        """
        处理客户端发送的 JSON 消息。

        支持:
            ping      - 心跳检测，回复 pong
            subscribe - 动态切换订阅的 execution_id
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
        """发送 JSON 消息到客户端（自动序列化，保留中文字符）。"""
        await self.send(text_data=json.dumps(content, ensure_ascii=False))

    # ---- Channel Layer 事件处理器 ----
    # 以下方法由 Channel Layer 的 group_send 触发，负责过滤并转发消息

    async def broadcast_progress(self, event: Dict) -> None:
        """处理进度广播事件，仅转发匹配当前 execution_id 的消息。"""
        payload = event['payload']

        # 只发送给相关执行的订阅者
        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_status(self, event: Dict) -> None:
        """处理状态变更广播事件。"""
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_screenshot(self, event: Dict) -> None:
        """处理截图广播事件。"""
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)

    async def broadcast_error(self, event: Dict) -> None:
        """处理错误广播事件。"""
        payload = event['payload']

        if hasattr(self, 'execution_id') and str(payload.get('execution_id')) == self.execution_id:
            await self.send_json(payload)


def create_progress_callback(execution_id: int):
    """
    创建进度回调函数的工厂。

    返回一个可以直接传递给执行服务的回调函数，
    该函数会将进度数据通过 WebSocket 广播给订阅的客户端。

    Args:
        execution_id: 执行记录 ID
    """
    def callback(progress_data: Dict) -> None:
        """将进度数据广播到 WebSocket。"""
        WebSocketProgressService.broadcast_progress(
            execution_id=execution_id,
            message=progress_data.get('message', ''),
            data=progress_data.get('data', {}),
        )

    return callback


def create_screenshot_callback(execution_id: int):
    """
    创建截图回调函数的工厂。

    返回一个同步回调函数，内部通过 asyncio 任务将截图数据广播给客户端。

    Args:
        execution_id: 执行记录 ID
    """
    async def async_callback(screenshot_data: str, description: str) -> None:
        """异步广播截图数据。"""
        WebSocketProgressService.broadcast_screenshot(
            execution_id=execution_id,
            screenshot_data={
                'data': screenshot_data,
                'description': description,
            }
        )

    def callback(screenshot_data: str, description: str) -> None:
        """同步入口，创建异步任务执行广播。"""
        asyncio.create_task(async_callback(screenshot_data, description))

    return callback
