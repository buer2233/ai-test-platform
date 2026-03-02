"""
UI 自动化测试模块 - API 视图

提供 Django REST Framework 视图集，处理所有 UI 自动化相关的 API 请求。

视图集清单:
    UiTestProjectViewSet    - 测试项目 CRUD + 统计
    UiTestCaseViewSet       - 测试用例 CRUD + 运行 + 复制
    UiTestExecutionViewSet  - 执行记录管理 + 运行/取消 + 报告/截图查看
    UiTestReportViewSet     - 报告查看（只读）+ 文件下载 + 截图服务
    UiScreenshotViewSet     - 截图查看（只读）
"""

import json
import logging
import mimetypes
import os
import threading
import traceback
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path as PathLib

from django.conf import settings
from django.db.models import Q, Count
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import UiTestProject, UiTestCase, UiTestExecution, UiTestReport, UiScreenshot
from .serializers import (
    UiTestProjectSerializer,
    UiTestProjectDetailSerializer,
    UiTestCaseSerializer,
    UiTestCaseListSerializer,
    UiTestCaseDetailSerializer,
    UiTestExecutionSerializer,
    UiTestExecutionListSerializer,
    UiTestExecutionDetailSerializer,
    UiTestExecutionCreateSerializer,
    UiTestReportSerializer,
    UiScreenshotSerializer,
)
from .services import (
    execute_test_case_cli,
    create_progress_callback,
    generate_report,
    save_report,
)
from .services.websocket_service import WebSocketProgressService

logger = logging.getLogger(__name__)

# ============================================================================
# 后台测试执行辅助函数
# ============================================================================


def _resolve_report_absolute_path(report_path):
    """
    将报告路径转换为绝对路径。

    如果是相对路径，则基于 browser-use-0.11.2 目录进行解析。

    Args:
        report_path: 原始报告路径（可能是绝对路径或相对路径）

    Returns:
        绝对路径字符串
    """
    path_obj = PathLib(report_path)
    if not path_obj.is_absolute():
        base_dir = PathLib(__file__).parent / 'browser-use-0.11.2'
        path_obj = base_dir / report_path
    return str(path_obj.resolve())


def _determine_final_status(result):
    """
    根据 CLI 执行结果判断最终状态和状态消息。

    Args:
        result: CLI 执行返回的结果字典

    Returns:
        (final_status, status_message) 元组
    """
    if result.get('success') and result.get('is_successful'):
        return 'passed', '测试执行成功'
    if result.get('success'):
        # CLI 成功执行但测试未通过预期
        return 'failed', result.get('final_result', '测试未达到预期结果')
    # CLI 执行失败
    return 'error', result.get('error', '未知错误')


def _run_test_in_background(execution, task, browser_mode, progress_callback):
    """
    在后台线程中执行测试的核心逻辑。

    包含完整的测试执行流程:
    1. 广播执行开始通知
    2. 调用 CLI 执行服务运行测试
    3. 根据结果更新执行记录状态
    4. 创建或更新测试报告
    5. 广播状态变更和报告生成通知

    Args:
        execution: UiTestExecution 实例
        task: 自然语言测试任务文本
        browser_mode: 浏览器模式（headless/headed）
        progress_callback: 进度回调函数
    """
    try:
        # 第1步: 广播执行开始
        WebSocketProgressService.broadcast_progress(
            execution_id=execution.id,
            message='开始执行测试',
            data={'step': 'start', 'task': task[:100]}
        )

        # 第2步: 调用 CLI 执行服务
        result = execute_test_case_cli(
            execution_id=execution.id,
            task=task,
            browser_mode=browser_mode,
            model='gpt-4o-mini',
            max_steps=50,
            progress_callback=progress_callback,
        )

        # 第3步: 更新执行记录
        execution.refresh_from_db()
        completed_at = timezone.now()
        duration_seconds = (
            int((completed_at - execution.started_at).total_seconds())
            if execution.started_at else 0
        )
        final_status, status_message = _determine_final_status(result)

        execution.status = final_status
        execution.completed_at = completed_at
        execution.duration_seconds = duration_seconds

        if result.get('success'):
            execution.final_result = json.dumps({
                'report_path': result.get('report_path'),
                'final_result': result.get('final_result'),
                'is_successful': result.get('is_successful', False),
                'total_steps': result.get('total_steps', 0),
            }, ensure_ascii=False)
        else:
            execution.error_message = result.get('error', '未知错误')

        execution.save()

        # 第4步: 广播状态变更
        WebSocketProgressService.broadcast_status_change(
            execution_id=execution.id,
            status=final_status,
            extra_data={
                'message': status_message,
                'duration_seconds': duration_seconds,
                'report_path': result.get('report_path'),
            }
        )

        # 第5步: 创建或更新测试报告记录
        report_path = result.get('report_path')
        if report_path:
            absolute_path_str = _resolve_report_absolute_path(report_path)
            is_success = result.get('success', False)
            total_steps = result.get('total_steps', 0)

            # 检查是否已有关联报告
            existing_report = getattr(execution, 'report', None)

            if not existing_report:
                UiTestReport.objects.create(
                    execution=execution,
                    total_steps=total_steps,
                    completed_steps=total_steps if is_success else 0,
                    failed_steps=0 if is_success else total_steps,
                    agent_history='',
                    json_report_path=absolute_path_str,
                    summary=f"测试{'成功' if is_success and result.get('is_successful') else '失败'}",
                )
            else:
                existing_report.json_report_path = absolute_path_str
                existing_report.save()

            # 广播报告生成通知
            WebSocketProgressService.broadcast_progress(
                execution_id=execution.id,
                message='测试报告已生成',
                data={'step': 'report_created', 'report_path': absolute_path_str}
            )

    except Exception as e:
        # 异常处理: 更新执行记录为错误状态并广播
        error_details = traceback.format_exc()
        logger.error("测试执行异常 (execution_id=%s): %s", execution.id, error_details)

        execution.refresh_from_db()
        execution.status = 'error'
        execution.error_message = str(e)
        execution.completed_at = timezone.now()
        if execution.started_at:
            execution.duration_seconds = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )
        execution.save()

        WebSocketProgressService.broadcast_error(
            execution_id=execution.id,
            error_message=str(e),
            error_details={'traceback': error_details}
        )
        WebSocketProgressService.broadcast_status_change(
            execution_id=execution.id,
            status='error',
            extra_data={'message': f'执行出错: {str(e)}'}
        )


def _start_background_test(execution, task, browser_mode, progress_callback):
    """
    启动后台线程执行测试。

    Args:
        execution: UiTestExecution 实例
        task: 自然语言测试任务文本
        browser_mode: 浏览器模式
        progress_callback: 进度回调函数
    """
    thread = threading.Thread(
        target=_run_test_in_background,
        args=(execution, task, browser_mode, progress_callback),
        daemon=True,
    )
    thread.start()


# ============================================================================
# 视图集
# ============================================================================


class UiTestProjectViewSet(viewsets.ModelViewSet):
    """
    UI 测试项目视图集。

    提供项目的完整 CRUD 操作，以及关联的用例列表、执行记录、统计信息等端点。
    查询集自动按当前用户过滤，仅返回用户自己创建且未删除的项目。

    自定义端点:
        GET  /{id}/test_cases/  - 获取项目下所有未删除的测试用例
        GET  /{id}/executions/  - 获取项目下所有执行记录
        GET  /{id}/statistics/  - 获取项目统计信息（用例数、执行数、通过率等）
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_deleted']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """获取当前用户创建的、未软删除的项目查询集。"""
        return UiTestProject.objects.filter(
            created_by=self.request.user,
            is_deleted=False
        )

    def get_serializer_class(self):
        """详情页使用包含用例列表的详情序列化器，其他操作使用基础序列化器。"""
        if self.action == 'retrieve':
            return UiTestProjectDetailSerializer
        return UiTestProjectSerializer

    def perform_create(self, serializer):
        """创建项目时自动设置 created_by 为当前请求用户。"""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """执行软删除，将 is_deleted 标记为 True。"""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """获取项目下所有未删除的测试用例列表。"""
        project = self.get_object()
        test_cases = project.test_cases.filter(is_deleted=False)
        serializer = UiTestCaseListSerializer(test_cases, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取项目下所有执行记录列表。"""
        project = self.get_object()
        executions = project.executions.all()
        serializer = UiTestExecutionListSerializer(executions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        获取项目统计信息。

        返回数据包括:
            test_cases: 用例总数、启用数、禁用数
            executions: 执行总数、通过数、失败数、错误数、通过率
        """
        project = self.get_object()

        # 统计用例数量
        total_cases = project.test_cases.filter(is_deleted=False).count()
        enabled_cases = project.test_cases.filter(is_deleted=False, is_enabled=True).count()

        # 统计各状态的执行记录数量
        executions = project.executions.all()
        total_executions = executions.count()
        passed_executions = executions.filter(status='passed').count()
        failed_executions = executions.filter(status='failed').count()
        error_executions = executions.filter(status='error').count()

        # 计算通过率（避免除零）
        pass_rate = round((passed_executions / total_executions) * 100, 2) if total_executions > 0 else 0

        return Response({
            'test_cases': {
                'total': total_cases,
                'enabled': enabled_cases,
                'disabled': total_cases - enabled_cases,
            },
            'executions': {
                'total': total_executions,
                'passed': passed_executions,
                'failed': failed_executions,
                'error': error_executions,
                'pass_rate': pass_rate,
            },
        })


class UiTestCaseViewSet(viewsets.ModelViewSet):
    """
    UI 测试用例视图集。

    提供用例的完整 CRUD 操作，以及运行、复制等端点。
    查询集自动按当前用户的项目过滤，仅返回未删除的用例。

    自定义端点:
        GET   /{id}/executions/ - 获取用例的所有执行记录
        POST  /{id}/run/        - 直接运行用例（自动创建执行记录并启动后台测试）
        POST  /{id}/copy/       - 复制用例（副本默认禁用）
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'priority', 'is_enabled', 'is_deleted']
    search_fields = ['name', 'natural_language_task', 'expected_result']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """获取当前用户项目下的、未软删除的用例查询集（预加载项目信息）。"""
        return UiTestCase.objects.filter(
            project__created_by=self.request.user,
            is_deleted=False
        ).select_related('project')

    def get_serializer_class(self):
        """列表使用精简序列化器，详情使用含执行记录的序列化器，其他使用完整序列化器。"""
        if self.action == 'list':
            return UiTestCaseListSerializer
        if self.action == 'retrieve':
            return UiTestCaseDetailSerializer
        return UiTestCaseSerializer

    def create(self, request, *args, **kwargs):
        """
        创建测试用例。

        处理前端字段名与后端字段名的映射:
            test_task  -> natural_language_task
            is_active  -> is_enabled
        """
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

        # 前端字段别名映射为后端模型字段名
        if 'test_task' in data:
            data['natural_language_task'] = data.pop('test_task')
        if 'is_active' in data:
            data['is_enabled'] = data.pop('is_active')

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            logger.warning("UiTestCase 创建验证失败: %s, 数据: %s", serializer.errors, data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_destroy(self, instance):
        """执行软删除，将 is_deleted 标记为 True。"""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取该用例的所有执行记录列表。"""
        test_case = self.get_object()
        executions = test_case.executions.all()
        serializer = UiTestExecutionListSerializer(executions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """
        直接运行测试用例。

        自动创建执行记录（状态为 running），然后在后台线程中通过 CLI 执行测试。
        立即返回 HTTP 202，客户端可通过 WebSocket 订阅实时进度。
        """
        test_case = self.get_object()

        # 前置校验: 用例必须已启用
        if not test_case.is_enabled:
            return Response(
                {'error': '测试用例未启用'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 前置校验: OPENAI_API_KEY 必须已配置
        if not os.environ.get('OPENAI_API_KEY'):
            return Response(
                {'error': 'OPENAI_API_KEY 环境变量未设置，请配置后再试'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 获取浏览器模式（优先使用请求参数，否则使用项目默认值）
        browser_mode = request.data.get('browser_mode', test_case.project.default_browser_mode)

        # 创建执行记录
        execution = UiTestExecution.objects.create(
            project=test_case.project,
            test_case=test_case,
            browser_mode=browser_mode,
            status='running',
            started_at=timezone.now(),
            executed_by=request.user,
        )

        # 在后台线程中启动测试
        progress_callback = create_progress_callback(execution.id)
        _start_background_test(
            execution=execution,
            task=test_case.natural_language_task,
            browser_mode=browser_mode,
            progress_callback=progress_callback,
        )

        # 立即返回执行记录信息
        serializer = UiTestExecutionSerializer(execution)
        return Response({
            'message': '测试执行已启动',
            'execution': serializer.data,
            'status': 'running',
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """
        复制测试用例。

        创建一个副本，名称添加 "(副本)" 后缀。如果同名副本已存在，
        则自动添加递增编号（如 "(副本) (2)"）。副本默认禁用。
        """
        test_case = self.get_object()

        # 生成唯一的副本名称
        new_name = f"{test_case.name} (副本)"
        suffix = 1
        original_name = new_name
        while UiTestCase.objects.filter(
            project=test_case.project,
            name=new_name,
            is_deleted=False
        ).exists():
            suffix += 1
            new_name = f"{original_name} ({suffix})"

        new_test_case = UiTestCase.objects.create(
            project=test_case.project,
            name=new_name,
            description=test_case.description,
            natural_language_task=test_case.natural_language_task,
            expected_result=test_case.expected_result,
            tags=test_case.tags,
            priority=test_case.priority,
            browser_mode=test_case.browser_mode,
            timeout=test_case.timeout,
            retry_count=test_case.retry_count,
            is_enabled=False,  # 副本默认禁用，避免误执行
        )

        serializer = UiTestCaseSerializer(new_test_case)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UiTestExecutionViewSet(viewsets.ModelViewSet):
    """
    UI 测试执行记录视图集。

    提供执行记录的 CRUD 操作，以及运行、取消、查看报告/截图等端点。
    查询集自动按当前用户的项目过滤，支持日期范围筛选。

    自定义端点:
        POST  /{id}/run/         - 运行待执行的记录（通过 CLI 调用执行脚本）
        POST  /{id}/cancel/      - 取消执行（仅 pending/running 状态可取消）
        GET   /{id}/report/      - 获取关联的测试报告
        GET   /{id}/screenshots/  - 获取执行截图列表
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['project', 'test_case', 'status', 'browser_mode']
    search_fields = ['test_case__name', 'final_result', 'error_message']
    ordering_fields = ['created_at', 'started_at', 'completed_at', 'duration_seconds']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        获取当前用户项目下的执行记录查询集。

        支持通过查询参数 created_after/created_before 进行日期范围筛选。
        预加载项目、用例、执行人信息以避免 N+1 查询。
        """
        queryset = UiTestExecution.objects.filter(
            project__created_by=self.request.user
        ).select_related('project', 'test_case', 'executed_by')

        # 日期范围筛选
        created_after = self.request.query_params.get('created_after')
        created_before = self.request.query_params.get('created_before')
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            # 将结束日期加一天，使筛选结果包含当天的所有记录
            end_date = datetime.strptime(created_before, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_date)

        return queryset

    def get_serializer_class(self):
        """列表使用精简序列化器，详情包含报告，创建使用专用序列化器。"""
        if self.action == 'list':
            return UiTestExecutionListSerializer
        if self.action == 'retrieve':
            return UiTestExecutionDetailSerializer
        if self.action == 'create':
            return UiTestExecutionCreateSerializer
        return UiTestExecutionSerializer

    def create(self, request, *args, **kwargs):
        """创建执行记录，返回完整的执行信息（而非仅创建序列化器的字段）。"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        instance = serializer.instance
        detail_serializer = UiTestExecutionSerializer(instance)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """
        运行已存在的待执行记录。

        通过 CLI 调用 run_aiTest.py 脚本执行测试。
        仅 pending 状态的记录可以运行，运行后状态变为 running。
        """
        execution = self.get_object()

        # 前置校验: 仅 pending 状态可运行
        if execution.status != 'pending':
            return Response(
                {'error': f'执行状态为 {execution.get_status_display()}，无法运行'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 前置校验: OPENAI_API_KEY 必须已配置
        if not os.environ.get('OPENAI_API_KEY'):
            return Response(
                {'error': 'OPENAI_API_KEY 环境变量未设置，请配置后再试'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 更新状态为运行中
        execution.status = 'running'
        execution.started_at = timezone.now()
        execution.save()

        # 在后台线程中启动测试
        progress_callback = create_progress_callback(execution.id)
        _start_background_test(
            execution=execution,
            task=execution.test_case.natural_language_task,
            browser_mode=execution.browser_mode,
            progress_callback=progress_callback,
        )

        return Response({
            'message': '测试执行已启动',
            'execution_id': execution.id,
            'status': 'running',
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消测试执行（仅 pending/running 状态可取消）。"""
        execution = self.get_object()

        if execution.status not in ['pending', 'running']:
            return Response(
                {'error': f'执行状态为 {execution.get_status_display()}，无法取消'},
                status=status.HTTP_400_BAD_REQUEST
            )

        execution.status = 'cancelled'
        execution.completed_at = execution.started_at
        execution.save()

        serializer = UiTestExecutionSerializer(execution)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """获取该执行记录关联的测试报告。"""
        execution = self.get_object()

        try:
            report = execution.report
            serializer = UiTestReportSerializer(report)
            return Response(serializer.data)
        except UiTestReport.DoesNotExist:
            return Response(
                {'error': '报告不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def screenshots(self, request, pk=None):
        """获取该执行记录的截图列表。"""
        execution = self.get_object()
        screenshots = execution.screenshots.all()
        serializer = UiScreenshotSerializer(screenshots, many=True)
        return Response(serializer.data)


class UiTestReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UI 测试报告视图集（只读）。

    提供报告的列表和详情查看，以及报告文件下载、截图服务、汇总统计等端点。

    自定义端点:
        GET  /file/         - 获取 JSON 报告文件内容
        GET  /screenshot/   - 获取截图文件（支持 token 查询参数认证）
        GET  /{id}/summary/ - 获取报告汇总统计信息
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['execution']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """获取当前用户项目下的报告查询集（预加载执行记录、项目和用例）。"""
        return UiTestReport.objects.filter(
            execution__project__created_by=self.request.user
        ).select_related('execution__project', 'execution__test_case')

    def get_serializer_class(self):
        """返回报告序列化器。"""
        return UiTestReportSerializer

    # 截图服务允许的图片格式后缀
    ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

    @staticmethod
    def _error_response(error_code: str, message: str, http_status: int):
        """
        构建统一格式的错误响应。

        Args:
            error_code: 错误代码（如 REPORT_NOT_FOUND）
            message: 用户可见的错误消息
            http_status: HTTP 状态码
        """
        return Response(
            {
                'error': message,
                'message': message,
                'error_code': error_code,
            },
            status=http_status,
        )

    def _resolve_and_validate_report_path(self, report_path: str):
        """
        解析并校验报告文件路径。

        仅允许访问 browser-use-0.11.2/report/ 目录内的文件，
        防止路径遍历攻击。

        Args:
            report_path: 用户提供的报告路径

        Returns:
            (file_path, error_response) 元组。成功时 error_response 为 None，
            失败时 file_path 为 None。
        """

        if not report_path:
            return None, self._error_response(
                'REPORT_PATH_MISSING', '请提供报告文件路径', 400
            )

        decoded_path = urllib.parse.unquote(report_path)
        base_report_dir = (PathLib(__file__).parent / 'browser-use-0.11.2' / 'report').resolve()

        try:
            file_path = PathLib(decoded_path).expanduser().resolve()
        except Exception as e:
            return None, self._error_response(
                'REPORT_PATH_INVALID', f'无效的文件路径: {str(e)}', 400
            )

        try:
            file_path.relative_to(base_report_dir)
        except ValueError:
            file_path_str = str(file_path).lower()
            base_dir_str = str(base_report_dir).lower()
            if not file_path_str.startswith(base_dir_str):
                return None, self._error_response(
                    'REPORT_PATH_FORBIDDEN', '非法的文件路径，报告必须在报告目录内', 403
                )

        if not file_path.exists():
            return None, self._error_response(
                'REPORT_NOT_FOUND', f'报告文件不存在: {file_path.name}', 404
            )

        if not file_path.is_file():
            return None, self._error_response(
                'REPORT_PATH_INVALID', '路径不是文件', 400
            )

        return file_path, None

    def _resolve_and_validate_screenshot_path(self, screenshot_path: str):
        """
        解析并校验截图文件路径。

        允许访问 browser-use-0.11.2/ 根目录下的图片文件，
        并检查文件格式是否在允许列表中。

        Args:
            screenshot_path: 用户提供的截图路径

        Returns:
            (file_path, error_response) 元组。成功时 error_response 为 None，
            失败时 file_path 为 None。
        """

        if not screenshot_path:
            return None, self._error_response(
                'REPORT_PATH_MISSING', '请提供截图文件路径', 400
            )

        decoded_path = urllib.parse.unquote(screenshot_path)
        base_dir = (PathLib(__file__).parent / 'browser-use-0.11.2').resolve()

        try:
            file_path = PathLib(decoded_path).expanduser().resolve()
        except Exception as e:
            return None, self._error_response(
                'REPORT_PATH_INVALID', f'无效的文件路径: {str(e)}', 400
            )

        try:
            file_path.relative_to(base_dir)
        except ValueError:
            file_path_str = str(file_path).lower()
            base_dir_str = str(base_dir).lower()
            if not file_path_str.startswith(base_dir_str):
                return None, self._error_response(
                    'REPORT_PATH_FORBIDDEN', '非法的文件路径，截图必须在允许的目录内', 403
                )

        if file_path.suffix.lower() not in self.ALLOWED_IMAGE_EXTENSIONS:
            return None, self._error_response(
                'SCREENSHOT_INVALID_FORMAT',
                f'不支持的图片格式: {file_path.suffix}，允许: {", ".join(self.ALLOWED_IMAGE_EXTENSIONS)}',
                400,
            )

        if not file_path.exists():
            return None, self._error_response(
                'SCREENSHOT_NOT_FOUND', f'截图文件不存在: {file_path.name}', 404
            )

        if not file_path.is_file():
            return None, self._error_response(
                'REPORT_PATH_INVALID', '路径不是文件', 400
            )

        return file_path, None

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def screenshot(self, request):
        """
        获取截图文件。

        由于 HTML <img src> 标签无法携带 Authorization header，
        本端点支持通过 token 查询参数进行认证。

        查询参数:
            path: 截图文件的绝对路径
            token: 认证令牌（可选，未提供时使用 Authorization header）
        """
        # 认证: 优先使用 token 查询参数，其次使用 Authorization header
        token_key = request.query_params.get('token')
        if not token_key:
            if not request.user or not request.user.is_authenticated:
                return self._error_response('SCREENSHOT_NOT_FOUND', '认证失败', 401)
        else:
            try:
                token_obj = Token.objects.select_related('user').get(key=token_key)
                request.user = token_obj.user
            except Token.DoesNotExist:
                return self._error_response('SCREENSHOT_NOT_FOUND', '认证失败', 401)

        screenshot_path = request.query_params.get('path')
        file_path, error_response = self._resolve_and_validate_screenshot_path(screenshot_path)
        if error_response is not None:
            return error_response

        content_type = mimetypes.guess_type(str(file_path))[0] or 'image/png'
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
        )
        response['Content-Disposition'] = f'inline; filename="{file_path.name}"'
        return response

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        获取报告汇总信息。

        优先从 JSON 报告文件中解析步骤统计数据，
        如果文件不存在或解析失败，则回退到数据库中的统计字段。
        """
        report = self.get_object()
        execution = report.execution

        metrics = {
            'total_steps': 0,
            'failed_steps': 0,
            'success_steps': 0,
            'screenshot_count': 0,
        }
        last_result_text = ''

        # 优先从 JSON 报告文件解析统计数据
        if report.json_report_path:
            file_path, error_response = self._resolve_and_validate_report_path(report.json_report_path)
            if error_response is None and file_path is not None:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    history = data.get('history', []) if isinstance(data, dict) else []
                    metrics['total_steps'] = len(history)

                    # 遍历每个步骤，统计失败数和截图数
                    failed_steps = 0
                    screenshot_count = 0
                    for step in history:
                        step_results = step.get('result', []) if isinstance(step, dict) else []
                        # 如果步骤结果中包含 error 字段，则计为失败
                        if any(item.get('error') for item in step_results if isinstance(item, dict)):
                            failed_steps += 1
                        # 如果步骤状态中包含截图路径，则计入截图数
                        state = step.get('state', {}) if isinstance(step, dict) else {}
                        if isinstance(state, dict) and state.get('screenshot_path'):
                            screenshot_count += 1

                    metrics['failed_steps'] = failed_steps
                    metrics['success_steps'] = max(metrics['total_steps'] - failed_steps, 0)
                    metrics['screenshot_count'] = screenshot_count

                    # 提取最后一步的执行结果文本
                    if history:
                        last_step = history[-1]
                        step_results = last_step.get('result', []) if isinstance(last_step, dict) else []
                        if step_results and isinstance(step_results[0], dict):
                            last_result_text = step_results[0].get('extracted_content', '') or ''
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass  # JSON 解析失败时回退到数据库统计
                except Exception:
                    pass  # 其他异常也不阻断响应

        # 回退: 如果 JSON 文件未提供有效数据，使用数据库中的统计字段
        if metrics['total_steps'] == 0:
            metrics['total_steps'] = report.total_steps or 0
            metrics['failed_steps'] = report.failed_steps or 0
            metrics['success_steps'] = max((report.completed_steps or 0) - (report.failed_steps or 0), 0)
            metrics['screenshot_count'] = len(json.loads(report.screenshot_paths or '[]'))

        return Response({
            'id': report.id,
            'execution_id': execution.id,
            'project_id': execution.project_id,
            'project_name': execution.project.name,
            'test_case_name': execution.test_case.name,
            'browser_mode': execution.browser_mode,
            'status': execution.status,
            'started_at': execution.started_at,
            'completed_at': execution.completed_at,
            'duration_seconds': execution.duration_seconds,
            'json_report_path': report.json_report_path,
            'summary': report.summary,
            'final_result': last_result_text,
            'error_message': execution.error_message,
            'metrics': metrics,
        })

    @action(detail=False, methods=['get'])
    def file(self, request):
        """
        获取 JSON 报告文件内容。

        查询参数:
            path: 报告文件路径（绝对路径或相对于 browser-use-0.11.2 的路径）

        返回:
            解析后的 JSON 报告数据
        """
        report_path = request.query_params.get('path')
        file_path, error_response = self._resolve_and_validate_report_path(report_path)
        if error_response is not None:
            return error_response

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Response(data)
        except json.JSONDecodeError as e:
            return self._error_response(
                'REPORT_PARSE_ERROR', f'报告文件格式错误: {str(e)}', 422
            )
        except UnicodeDecodeError:
            return self._error_response(
                'REPORT_ENCODING_ERROR', '报告文件编码错误（需要 UTF-8 编码）', 422
            )
        except Exception as e:
            return self._error_response(
                'REPORT_PARSE_ERROR', f'读取报告文件失败: {str(e)}', 500
            )


class UiScreenshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    UI 测试截图视图集（只读）。

    提供截图的列表和详情查看，按执行记录和步骤序号排序。
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['execution']
    ordering_fields = ['created_at', 'step_number']
    ordering = ['execution', 'step_number']

    def get_queryset(self):
        """获取当前用户项目下的截图查询集（预加载执行记录）。"""
        return UiScreenshot.objects.filter(
            execution__project__created_by=self.request.user
        ).select_related('execution')

    def get_serializer_class(self):
        """返回截图序列化器。"""
        return UiScreenshotSerializer
