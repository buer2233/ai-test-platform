"""
测试执行编排服务

协调 UI 测试的完整执行流程，包括:
1. 加载和验证执行记录状态
2. 初始化并运行 BrowserUse Agent
3. 收集执行步骤和截图
4. 更新执行记录状态
5. 生成测试报告

此服务通过直接调用 BrowserUseService 执行测试（区别于 CLI 方式），
适用于在 Django 进程内直接运行的场景。
"""

import asyncio
import json
from typing import Callable, Dict, Optional

from django.db import transaction
from django.utils import timezone

from ..models import UiTestExecution, UiTestReport
from .browser_use_service import BrowserUseService


class TestExecutorService:
    """
    测试执行编排服务类。

    协调测试执行的完整流程:
        1. 加载执行记录并验证状态
        2. 初始化 BrowserUse Agent
        3. 执行测试任务
        4. 收集结果并更新执行记录
        5. 生成测试报告

    Attributes:
        execution_id: 执行记录 ID
        execution: 加载后的 UiTestExecution 实例
        execution_steps: 收集的执行步骤列表
        screenshot_data: 收集的截图数据列表
    """

    def __init__(self, execution_id: int, progress_callback: Optional[Callable] = None):
        """
        初始化测试执行服务。

        Args:
            execution_id: 数据库中的执行记录 ID
            progress_callback: 进度回调函数，签名: (dict) -> None
        """
        self.execution_id = execution_id
        self.progress_callback = progress_callback
        self.execution = None
        self.browser_use_service = None
        self.execution_steps = []
        self.screenshot_data = []

    def _emit_progress(self, message: str, data: Optional[Dict] = None) -> None:
        """通过回调函数发送进度更新。"""
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
        """BrowserUse 步骤回调: 记录步骤并通知进度。"""
        self.execution_steps.append({
            **step,
            'timestamp': timezone.now().isoformat(),
        })
        self._emit_progress(
            f"执行步骤: {step.get('action', 'unknown')}",
            {'step': step}
        )

    async def _on_screenshot(self, screenshot_data: str, description: str) -> None:
        """截图回调: 收集截图数据并通知进度。"""
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
        从数据库加载执行记录。

        Raises:
            ValueError: 指定 ID 的执行记录不存在
        """
        try:
            execution = UiTestExecution.objects.get(id=self.execution_id)
            self.execution = execution
            return execution
        except UiTestExecution.DoesNotExist:
            raise ValueError(f"Execution {self.execution_id} not found")

    def _update_execution_status(self, status: str, **kwargs) -> None:
        """更新执行记录的状态及其他字段。"""
        if self.execution:
            for key, value in kwargs.items():
                setattr(self.execution, key, value)
            self.execution.status = status
            self.execution.save()

    def _create_test_report(self, result: Dict) -> UiTestReport:
        """根据执行结果创建测试报告记录。"""
        total_steps = len(self.execution_steps)
        completed_steps = sum(1 for s in self.execution_steps if s.get('success', True))
        failed_steps = total_steps - completed_steps

        return UiTestReport.objects.create(
            execution=self.execution,
            agent_history=json.dumps(self.execution_steps, ensure_ascii=False),
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            screenshot_paths=json.dumps(
                [s['description'] for s in self.screenshot_data],
                ensure_ascii=False
            ),
            summary=self._generate_summary(result),
        )

    def _generate_summary(self, result: Dict) -> str:
        """根据执行结果生成简洁的摘要文本。"""
        steps_count = len(self.execution_steps)
        screenshots_count = len(self.screenshot_data)

        if result.get('success'):
            return f"测试执行成功。共执行 {steps_count} 个步骤，捕获 {screenshots_count} 张截图。"

        error = result.get('error', '未知错误')
        return f"测试执行失败: {error}。共执行 {steps_count} 个步骤。"

    def _save_screenshots(self) -> None:
        """保存截图到数据库（当前为占位实现，实际需处理文件上传）。"""

    @transaction.atomic
    def execute(self) -> Dict[str, any]:
        """
        执行测试用例（同步，事务保护）。

        完整流程: 加载记录 -> 校验状态 -> 初始化 Agent -> 执行 -> 更新结果 -> 生成报告。

        Returns:
            执行结果字典，包含 success、status、duration、report_id 等字段
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
        异步执行测试用例（在线程池中运行同步 execute 方法）。

        Returns:
            执行结果字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute)

    def cancel(self) -> bool:
        """
        取消正在执行的测试。

        更新执行记录状态为 cancelled 并清理 BrowserUse 资源。

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
    同步执行测试用例的便捷函数。

    创建 TestExecutorService 实例并立即执行，参数含义同构造函数。
    """
    executor = TestExecutorService(execution_id, progress_callback)
    return executor.execute()


async def execute_test_case_async(
    execution_id: int,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, any]:
    """
    异步执行测试用例的便捷函数。

    创建 TestExecutorService 实例并异步执行，参数含义同构造函数。
    """
    executor = TestExecutorService(execution_id, progress_callback)
    return await executor.execute_async()
