"""
UI自动化测试 API 序列化器

提供 Django REST Framework 的序列化器，用于 API 请求/响应的数据转换。
"""

from rest_framework import serializers
from .models import UiTestProject, UiTestCase, UiTestExecution, UiTestReport, UiScreenshot
import json


class TagsField(serializers.Field):
    """自定义字段：处理标签的JSON序列化"""

    def to_representation(self, value):
        """将数据库值转换为API响应"""
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []

    def to_internal_value(self, data):
        """将API请求转换为数据库值"""
        if isinstance(data, list):
            return json.dumps(data)
        if isinstance(data, str):
            return data
        return json.dumps([])


class AgentHistoryField(serializers.Field):
    """自定义字段：处理Agent历史的JSON序列化"""

    def to_representation(self, value):
        """将数据库值转换为API响应"""
        if not value:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None

    def to_internal_value(self, data):
        """将API请求转换为数据库值"""
        if data is None:
            return None
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        if isinstance(data, str):
            return data
        return None


class UiTestProjectSerializer(serializers.ModelSerializer):
    """UI测试项目序列化器"""

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
        """获取项目下的测试用例数量"""
        return obj.test_cases.filter(is_deleted=False).count()


class UiTestProjectDetailSerializer(UiTestProjectSerializer):
    """UI测试项目详情序列化器"""

    test_cases = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestProjectSerializer.Meta):
        fields = UiTestProjectSerializer.Meta.fields + ['test_cases']

    def get_test_cases(self, obj):
        """获取项目下的测试用例列表"""
        cases = obj.test_cases.filter(is_deleted=False)[:10]
        return UiTestCaseListSerializer(cases, many=True).data


class UiTestCaseSerializer(serializers.ModelSerializer):
    """UI测试用例序列化器"""

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
        """返回时添加前端需要的字段别名"""
        data = super().to_representation(instance)
        # 添加前端字段别名
        data['test_task'] = data.pop('natural_language_task', '')
        data['is_active'] = data.pop('is_enabled', True)
        return data


class UiTestCaseListSerializer(serializers.ModelSerializer):
    """UI测试用例列表序列化器（精简版）"""

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
        """获取执行次数"""
        return obj.executions.count()

    def get_last_execution_status(self, obj):
        """获取最后一次执行状态"""
        last_execution = obj.executions.order_by('-created_at').first()
        if last_execution:
            return {
                'status': last_execution.status,
                'created_at': last_execution.created_at,
            }
        return None

    def to_representation(self, instance):
        """返回时添加前端需要的字段别名"""
        data = super().to_representation(instance)
        # 添加前端字段别名
        data['is_active'] = data.pop('is_enabled', True)
        return data


class UiTestCaseDetailSerializer(UiTestCaseSerializer):
    """UI测试用例详情序列化器"""

    recent_executions = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestCaseSerializer.Meta):
        fields = UiTestCaseSerializer.Meta.fields + ['recent_executions']

    def get_recent_executions(self, obj):
        """获取最近的执行记录"""
        executions = obj.executions.order_by('-created_at')[:5]
        return UiTestExecutionListSerializer(executions, many=True).data


class UiTestExecutionSerializer(serializers.ModelSerializer):
    """UI测试执行序列化器"""

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
    """UI测试执行列表序列化器（精简版）"""

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
    """UI测试执行详情序列化器"""

    report = serializers.SerializerMethodField(read_only=True)

    class Meta(UiTestExecutionSerializer.Meta):
        fields = UiTestExecutionSerializer.Meta.fields + ['report']

    def get_report(self, obj):
        """获取测试报告"""
        try:
            report = obj.report
            return UiTestReportSerializer(report).data
        except UiTestReport.DoesNotExist:
            return None


class UiTestReportSerializer(serializers.ModelSerializer):
    """UI测试报告序列化器"""

    execution_id = serializers.IntegerField(source='execution.id', read_only=True)
    test_case_name = serializers.CharField(source='execution.test_case.name', read_only=True)
    agent_history = AgentHistoryField(required=False)
    screenshot_paths = TagsField(required=False)

    class Meta:
        model = UiTestReport
        fields = [
            'id',
            'execution',
            'execution_id',
            'test_case_name',
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
    """UI测试截图序列化器"""

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
    """创建UI测试执行的序列化器"""

    class Meta:
        model = UiTestExecution
        fields = [
            'test_case',
            'browser_mode',
        ]

    def create(self, validated_data):
        """创建执行记录"""
        test_case = validated_data['test_case']
        validated_data['project'] = test_case.project
        return super().create(validated_data)
