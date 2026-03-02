"""
UI 自动化测试模块 - API 序列化器

提供 Django REST Framework 的序列化器，用于 API 请求/响应的数据转换。

序列化器清单:
    TagsField                       - 标签字段的 JSON 序列化/反序列化
    AgentHistoryField               - Agent 历史字段的 JSON 序列化/反序列化
    UiTestProjectSerializer         - 项目（列表/创建/更新）
    UiTestProjectDetailSerializer   - 项目详情（含最近用例列表）
    UiTestCaseSerializer            - 用例（完整字段）
    UiTestCaseListSerializer        - 用例列表（精简字段 + 执行统计）
    UiTestCaseDetailSerializer      - 用例详情（含最近执行记录）
    UiTestExecutionSerializer       - 执行记录（完整字段）
    UiTestExecutionListSerializer   - 执行列表（精简字段）
    UiTestExecutionDetailSerializer - 执行详情（含关联报告）
    UiTestExecutionCreateSerializer - 创建执行记录
    UiTestReportSerializer          - 测试报告
    UiScreenshotSerializer          - 截图
"""

import json

from rest_framework import serializers

from .models import UiTestProject, UiTestCase, UiTestExecution, UiTestReport, UiScreenshot


class TagsField(serializers.Field):
    """
    自定义序列化字段：处理标签的 JSON 序列化与反序列化。

    数据库存储格式: JSON 字符串（如 '["tag1", "tag2"]'）
    API 交互格式: Python 列表（如 ["tag1", "tag2"]）
    """

    def to_representation(self, value):
        """将数据库中的 JSON 字符串转换为 Python 列表用于 API 响应。"""
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []

    def to_internal_value(self, data):
        """将 API 请求中的列表或字符串转换为 JSON 字符串用于数据库存储。"""
        if isinstance(data, list):
            return json.dumps(data)
        if isinstance(data, str):
            return data
        return json.dumps([])


class AgentHistoryField(serializers.Field):
    """
    自定义序列化字段：处理 Agent 执行历史的 JSON 序列化与反序列化。

    数据库存储格式: JSON 字符串或 None
    API 交互格式: Python 字典/列表或 None
    """

    def to_representation(self, value):
        """将数据库中的 JSON 字符串转换为 Python 对象用于 API 响应。"""
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def to_internal_value(self, data):
        """将 API 请求中的对象转换为 JSON 字符串用于数据库存储。"""
        if data is None:
            return None
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        if isinstance(data, str):
            return data
        return None


class UiTestProjectSerializer(serializers.ModelSerializer):
    """
    UI 测试项目序列化器（列表/创建/更新）。

    额外字段:
        created_by_name: 创建人用户名（只读）
        test_cases_count: 项目下未删除的测试用例数量（只读）
    """

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    test_cases_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UiTestProject
        fields = [
            'id',
            'name',
            'description',
            'base_url',
            'default_browser_mode',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
            'is_deleted',
            'test_cases_count',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_test_cases_count(self, obj):
        """获取项目下未删除的测试用例数量。"""
        return obj.test_cases.filter(is_deleted=False).count()


class UiTestProjectDetailSerializer(UiTestProjectSerializer):
    """
    UI 测试项目详情序列化器。

    继承 UiTestProjectSerializer，额外包含最近 10 条未删除的测试用例列表。
    """

    test_cases = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestProjectSerializer.Meta):
        fields = UiTestProjectSerializer.Meta.fields + ['test_cases']

    def get_test_cases(self, obj):
        """获取项目下最近 10 条未删除的测试用例列表。"""
        cases = obj.test_cases.filter(is_deleted=False)[:10]
        return UiTestCaseListSerializer(cases, many=True).data


class UiTestCaseSerializer(serializers.ModelSerializer):
    """
    UI 测试用例序列化器（完整字段）。

    字段映射说明（to_representation 中进行）:
        natural_language_task -> test_task  （前端使用的字段名）
        is_enabled -> is_active            （前端使用的字段名）
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    tags = TagsField(required=False)

    class Meta:
        model = UiTestCase
        fields = [
            'id',
            'project',
            'project_name',
            'name',
            'description',
            'natural_language_task',
            'expected_result',
            'tags',
            'priority',
            'priority_display',
            'browser_mode',
            'timeout',
            'retry_count',
            'is_enabled',
            'created_at',
            'updated_at',
            'is_deleted',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        """返回时将后端字段名映射为前端需要的别名。"""
        data = super().to_representation(instance)
        data['test_task'] = data.pop('natural_language_task', '')
        data['is_active'] = data.pop('is_enabled', True)
        return data


class UiTestCaseListSerializer(serializers.ModelSerializer):
    """
    UI 测试用例列表序列化器（精简版）。

    相比完整版去掉了详细描述和任务内容，增加了执行统计字段:
        execution_count: 总执行次数
        last_execution_status: 最近一次执行的状态和时间
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    execution_count = serializers.SerializerMethodField(read_only=True)
    last_execution_status = serializers.SerializerMethodField(read_only=True)
    tags = TagsField(required=False)

    class Meta:
        model = UiTestCase
        fields = [
            'id',
            'project',
            'project_name',
            'name',
            'priority',
            'priority_display',
            'is_enabled',
            'tags',
            'browser_mode',
            'execution_count',
            'last_execution_status',
            'created_at',
            'updated_at',
        ]

    def get_execution_count(self, obj):
        """获取该用例的总执行次数。"""
        return obj.executions.count()

    def get_last_execution_status(self, obj):
        """获取最近一次执行的状态和时间，无执行记录时返回 None。"""
        last_execution = obj.executions.order_by('-created_at').first()
        if last_execution:
            return {
                'status': last_execution.status,
                'created_at': last_execution.created_at,
            }
        return None

    def to_representation(self, instance):
        """返回时将 is_enabled 映射为前端使用的 is_active 字段名。"""
        data = super().to_representation(instance)
        data['is_active'] = data.pop('is_enabled', True)
        return data


class UiTestCaseDetailSerializer(UiTestCaseSerializer):
    """
    UI 测试用例详情序列化器。

    继承 UiTestCaseSerializer，额外包含最近 5 条执行记录。
    """

    recent_executions = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestCaseSerializer.Meta):
        fields = UiTestCaseSerializer.Meta.fields + ['recent_executions']

    def get_recent_executions(self, obj):
        """获取该用例最近 5 条执行记录。"""
        executions = obj.executions.order_by('-created_at')[:5]
        return UiTestExecutionListSerializer(executions, many=True).data


class UiTestExecutionSerializer(serializers.ModelSerializer):
    """
    UI 测试执行记录序列化器（完整字段）。

    包含关联的项目名称、用例名称、执行人名称等只读字段。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    browser_mode_display = serializers.CharField(source='get_browser_mode_display', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = UiTestExecution
        fields = [
            'id',
            'project',
            'project_name',
            'test_case',
            'test_case_name',
            'status',
            'status_display',
            'browser_mode',
            'browser_mode_display',
            'started_at',
            'completed_at',
            'duration_seconds',
            'duration_display',
            'final_result',
            'error_message',
            'executed_by',
            'executed_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'started_at',
            'completed_at',
            'duration_seconds',
            'final_result',
            'error_message',
            'created_at',
            'updated_at',
        ]


class UiTestExecutionListSerializer(serializers.ModelSerializer):
    """
    UI 测试执行列表序列化器（精简版）。

    仅包含列表展示所需的核心字段，减少数据传输量。
    """

    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_display = serializers.CharField(read_only=True)
    json_report_path = serializers.CharField(source='report.json_report_path', read_only=True, allow_null=True)

    class Meta:
        model = UiTestExecution
        fields = [
            'id',
            'test_case',
            'test_case_name',
            'status',
            'status_display',
            'browser_mode',
            'duration_display',
            'json_report_path',
            'created_at',
        ]


class UiTestExecutionDetailSerializer(UiTestExecutionSerializer):
    """
    UI 测试执行详情序列化器。

    继承 UiTestExecutionSerializer，额外包含关联的测试报告数据。
    """

    report = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestExecutionSerializer.Meta):
        fields = UiTestExecutionSerializer.Meta.fields + ['report']

    def get_report(self, obj):
        """获取关联的测试报告数据，报告不存在时返回 None。"""
        try:
            report = obj.report
            return UiTestReportSerializer(report).data
        except UiTestReport.DoesNotExist:
            return None


class UiTestReportSerializer(serializers.ModelSerializer):
    """
    UI 测试报告序列化器。

    通过嵌套关系从 execution 中获取项目、用例、状态、时间等信息，
    实现"一次请求获取完整报告上下文"的效果。
    """

    execution_id = serializers.IntegerField(source='execution.id', read_only=True)
    project = serializers.IntegerField(source='execution.project.id', read_only=True)
    project_name = serializers.CharField(source='execution.project.name', read_only=True)
    test_case_name = serializers.CharField(source='execution.test_case.name', read_only=True)
    status = serializers.CharField(source='execution.status', read_only=True)
    duration_seconds = serializers.IntegerField(source='execution.duration_seconds', read_only=True, allow_null=True)
    started_at = serializers.DateTimeField(source='execution.started_at', read_only=True, allow_null=True)
    completed_at = serializers.DateTimeField(source='execution.completed_at', read_only=True, allow_null=True)
    agent_history = AgentHistoryField(required=False)
    screenshot_paths = TagsField(required=False)

    class Meta:
        model = UiTestReport
        fields = [
            'id',
            'project',
            'project_name',
            'execution',
            'execution_id',
            'test_case_name',
            'status',
            'duration_seconds',
            'started_at',
            'completed_at',
            'agent_history',
            'total_steps',
            'completed_steps',
            'failed_steps',
            'screenshot_paths',
            'report_file',
            'summary',
            'created_at',
        ]
        read_only_fields = ['created_at']


class UiScreenshotSerializer(serializers.ModelSerializer):
    """UI 测试截图序列化器。"""

    execution_id = serializers.IntegerField(source='execution.id', read_only=True)

    class Meta:
        model = UiScreenshot
        fields = [
            'id',
            'execution',
            'execution_id',
            'image_file',
            'description',
            'step_number',
            'created_at',
        ]
        read_only_fields = ['created_at']


class UiTestExecutionCreateSerializer(serializers.ModelSerializer):
    """
    创建 UI 测试执行记录的序列化器。

    仅接受 test_case 和 browser_mode 两个字段，
    project 字段在 create 时自动从 test_case 的关联关系中获取。
    """

    class Meta:
        model = UiTestExecution
        fields = [
            'test_case',
            'browser_mode',
        ]

    def create(self, validated_data):
        """创建执行记录，自动从 test_case 关联关系中填充 project 字段。"""
        test_case = validated_data['test_case']
        validated_data['project'] = test_case.project
        return super().create(validated_data)
