"""
测试执行服务模块

处理UI测试的执行逻辑，协调 BrowserUse、数据库和报告生成。
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional, Callable
from django.utils import timezone
from django.db import transaction

from ..models import UiTestExecution, UiTestReport, UiScreenshot
from .browser_use_service import BrowserUseService


class TestExecutorService:
    """
    测试执行服务类

    协调测试执行的完整流程：
    1. 初始化执行记录
    2. 启动 BrowserUse Agent
    3. 收集执行结果
    4. 生成测试报告
    """

    def __init__(self, execution_id: int, progress_callback: Optional[Callable] = None):
        """
        初始化测试执行服务

        Args:
            execution_id: 执行记录ID
            progress_callback: 进度回调函数
        """
        self.execution_id = execution_id
        self.progress_callback = progress_callback
        self.execution = None
        self.browser_use_service = None
        self.execution_steps = []
        self.screenshot_data = []

    def _emit_progress(self, message: str, data: Optional[Dict] = None) -> None:
        """
        发送进度更新

        Args:
            message: 进度消息
            data: 附加数据
        """
        if self.progress_callback:
            try:
                self.progress_callback({
                    'execution_id': self.execution_id,
                    'message': message,
                    'data': data or {},
                    'timestamp': timezone.now().isoformat(),
                })
            except Exception as e:
                print(f"Progress callback error: {e}")

    def _on_browser_step(self, step: Dict) -> None:
        """
        BrowserUse 步骤回调

        Args:
            step: 步骤信息
        """
        self.execution_steps.append({
            **step,
            'timestamp': timezone.now().isoformat(),
        })

        self._emit_progress(
            f"执行步骤: {step.get('action', 'unknown')}",
            {'step': step}
        )

    async def _on_screenshot(self, screenshot_data: str, description: str) -> None:
        """
        截图回调

        Args:
            screenshot_data: 截图数据（base64）
            description: 截图描述
        """
        self.screenshot_data.append({
            'data': screenshot_data,
            'description': description,
            'timestamp': timezone.now().isoformat(),
        })

        self._emit_progress(
            f"截图: {description}",
            {'screenshot_count': len(self.screenshot_data)}
        )

    def _load_execution(self) -> UiTestExecution:
        """
        加载执行记录

        Returns:
            UiTestExecution 实例

        Raises:
            ValueError: 如果执行记录不存在
        """
        try:
            execution = UiTestExecution.objects.get(id=self.execution_id)
            self.execution = execution
            return execution
        except UiTestExecution.DoesNotExist:
            raise ValueError(f"Execution {self.execution_id} not found")

    def _update_execution_status(self, status: str, **kwargs) -> None:
        """
        更新执行状态

        Args:
            status: 新状态
            **kwargs: 其他更新字段
        """
        if self.execution:
            for key, value in kwargs.items():
                setattr(self.execution, key, value)
            self.execution.status = status
            self.execution.save()

    def _create_test_report(self, result: Dict) -> UiTestReport:
        """
        创建测试报告

        Args:
            result: 执行结果字典

        Returns:
            UiTestReport 实例
        """
        # 统计步骤
        total_steps = len(self.execution_steps)
        completed_steps = sum(1 for s in self.execution_steps if s.get('success', True))
        failed_steps = total_steps - completed_steps

        # 创建报告
        report = UiTestReport.objects.create(
            execution=self.execution,
            agent_history=json.dumps(self.execution_steps, ensure_ascii=False),
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            screenshot_paths=json.dumps([s['description'] for s in self.screenshot_data], ensure_ascii=False),
            summary=self._generate_summary(result),
        )

        return report

    def _generate_summary(self, result: Dict) -> str:
        """
        生成执行摘要

        Args:
            result: 执行结果字典

        Returns:
            摘要文本
        """
        if result.get('success'):
            return f"测试执行成功。共执行 {len(self.execution_steps)} 个步骤，捕获 {len(self.screenshot_data)} 张截图。"
        else:
            error = result.get('error', '未知错误')
            return f"测试执行失败: {error}。共执行 {len(self.execution_steps)} 个步骤。"

    def _save_screenshots(self) -> None:
        """保存截图到数据库"""
        # 注意：实际保存图片文件需要处理文件上传
        # 这里暂时只记录截图信息
        pass

    @transaction.atomic
    def execute(self) -> Dict[str, any]:
        """
        执行测试用例

        Returns:
            执行结果字典
        """
        try:
            # 加载执行记录
            execution = self._load_execution()

            # 检查状态
            if execution.status != 'pending':
                return {
                    'success': False,
                    'error': f'Execution is not in pending status (current: {execution.status})',
                }

            # 更新状态为执行中
            self._update_execution_status(
                'running',
                started_at=timezone.now()
            )

            self._emit_progress("测试执行开始")

            # 获取测试任务
            test_case = execution.test_case
            task = test_case.natural_language_task

            # 创建 BrowserUse 服务
            self.browser_use_service = BrowserUseService(
                task=task,
                browser_mode=execution.browser_mode,
                screenshot_callback=self._on_screenshot,
                step_callback=self._on_browser_step,
            )

            self._emit_progress("BrowserUse Agent 初始化完成")

            # 执行测试
            result = self.browser_use_service.run_sync()

            # 更新执行记录
            completed_at = timezone.now()
            duration_seconds = int((completed_at - execution.started_at).total_seconds())

            status = 'passed' if result.get('success') else 'failed'

            self._update_execution_status(
                status,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                final_result=json.dumps(result.get('result', {}), ensure_ascii=False) if result.get('success') else None,
                error_message=result.get('error', '') if not result.get('success') else None,
            )

            # 创建测试报告
            report = self._create_test_report(result)

            # 保存截图
            self._save_screenshots()

            self._emit_progress(
                f"测试执行{'成功' if result.get('success') else '失败'}",
                {
                    'status': status,
                    'duration': duration_seconds,
                    'steps': len(self.execution_steps),
                    'screenshots': len(self.screenshot_data),
                }
            )

            return {
                'success': result.get('success', False),
                'execution_id': self.execution_id,
                'status': status,
                'duration': duration_seconds,
                'steps': len(self.execution_steps),
                'screenshots': len(self.screenshot_data),
                'report_id': report.id,
            }

        except Exception as e:
            # 更新为错误状态
            self._update_execution_status(
                'error',
                completed_at=timezone.now(),
                error_message=str(e),
            )

            self._emit_progress(f"测试执行出错: {str(e)}")

            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
                'status': 'error',
            }

    async def execute_async(self) -> Dict[str, any]:
        """
        异步执行测试用例

        Returns:
            执行结果字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute)

    def cancel(self) -> bool:
        """
        取消执行

        Returns:
            是否成功取消
        """
        try:
            if self.execution and self.execution.status == 'running':
                self._update_execution_status('cancelled')
                self._emit_progress("测试执行已取消")

                # 清理 BrowserUse 资源
                if self.browser_use_service:
                    asyncio.create_task(self.browser_use_service.cleanup())

                return True
            return False
        except Exception as e:
            print(f"Cancel error: {e}")
            return False


def execute_test_case(
    execution_id: int,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, any]:
    """
    执行测试用例的便捷函数

    Args:
        execution_id: 执行记录ID
        progress_callback: 进度回调函数

    Returns:
        执行结果字典
    """
    executor = TestExecutorService(execution_id, progress_callback)
    return executor.execute()


async def execute_test_case_async(
    execution_id: int,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, any]:
    """
    异步执行测试用例的便捷函数

    Args:
        execution_id: 执行记录ID
        progress_callback: 进度回调函数

    Returns:
        执行结果字典
    """
    executor = TestExecutorService(execution_id, progress_callback)
    return await executor.execute_async()
