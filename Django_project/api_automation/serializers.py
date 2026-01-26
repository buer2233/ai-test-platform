"""
api_automation/serializers.py

Django REST Framework 序列化器定义
"""
import json
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
    ApiTestExecution, ApiTestReport, ApiTestResult, ApiDataDriver,
    ApiTestCaseAssertion, ApiTestCaseExtraction, ApiHttpExecutionRecord
)


class JSONFieldSerializer(serializers.Field):
    """自定义 JSON 字段序列化器"""
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Invalid JSON string")
        elif isinstance(data, dict):
            return data
        else:
            raise serializers.ValidationError("Value must be a dict or JSON string")

    def to_representation(self, value):
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ApiProjectSerializer(serializers.ModelSerializer):
    """
    API项目序列化器
    """
    owner = UserSerializer(read_only=True)
    owner_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    collections_count = serializers.SerializerMethodField(read_only=True)
    test_cases_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApiProject
        fields = [
            'id', 'name', 'description', 'owner', 'owner_id',
            'is_active', 'created_time', 'updated_time',
            'collections_count', 'test_cases_count'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']

    def get_collections_count(self, obj):
        """获取集合数量"""
        return obj.api_collections.filter(is_deleted=False).count()

    def get_test_cases_count(self, obj):
        """获取测试用例数量"""
        return obj.test_cases.filter(is_deleted=False).count()

    def validate_name(self, value):
        """验证项目名称"""
        if not value.strip():
            raise serializers.ValidationError("项目名称不能为空")
        return value.strip()

    def create(self, validated_data):
        """创建项目"""
        request = self.context.get('request')
        if request and request.user and not validated_data.get('owner_id'):
            validated_data['owner'] = request.user
        return super().create(validated_data)


class ApiCollectionSerializer(serializers.ModelSerializer):
    """
    API集合序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    test_cases_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ApiCollection
        fields = [
            'id', 'name', 'description', 'project', 'project_name',
            'owner', 'owner_name', 'module',
            'created_time', 'updated_time', 'test_cases_count'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']

    def get_test_cases_count(self, obj):
        """获取测试用例数量"""
        return obj.test_cases.filter(is_deleted=False).count()

    def validate_name(self, value):
        """验证集合名称"""
        if not value.strip():
            raise serializers.ValidationError("集合名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证集合与项目的关系"""
        project = attrs.get('project')
        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")
        return attrs


class ApiTestCaseSerializer(serializers.ModelSerializer):
    """
    API测试用例序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    # 自定义字段显示更友好的格式
    headers_display = serializers.SerializerMethodField(read_only=True)
    params_display = serializers.SerializerMethodField(read_only=True)
    body_display = serializers.SerializerMethodField(read_only=True)

    # 使用自定义 JSON 字段序列化器
    headers = JSONFieldSerializer(required=False, default=dict)
    params = JSONFieldSerializer(required=False, default=dict)
    body = JSONFieldSerializer(required=False, default=dict)
    tests = JSONFieldSerializer(required=False, default=list)

    class Meta:
        model = ApiTestCase
        fields = [
            'id', 'name', 'description', 'project', 'project_name',
            'collection', 'collection_name', 'method', 'url',
            'headers', 'params', 'body', 'tests',
            'headers_display', 'params_display', 'body_display',
            'created_by', 'created_by_name',
            'owner', 'owner_name', 'module',
            'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_by', 'created_time', 'updated_time']

    def get_headers_display(self, obj):
        """格式化显示请求头"""
        if not obj.headers:
            return {}
        return obj.headers

    def get_params_display(self, obj):
        """格式化显示请求参数"""
        if not obj.params:
            return {}
        return obj.params

    def get_body_display(self, obj):
        """格式化显示请求体"""
        if not obj.body:
            return {}
        return obj.body

    def validate_name(self, value):
        """验证用例名称"""
        if not value.strip():
            raise serializers.ValidationError("用例名称不能为空")
        return value.strip()

    def validate_url(self, value):
        """验证URL"""
        if not value.strip():
            raise serializers.ValidationError("URL不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证用例与项目、集合的关系"""
        project = attrs.get('project')
        collection = attrs.get('collection')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if collection and collection.project != project:
            raise serializers.ValidationError("所选集合不属于该项目")

        return attrs

    def create(self, validated_data):
        """创建测试用例"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ApiTestCaseListSerializer(serializers.ModelSerializer):
    """
    API测试用例列表序列化器（简化版）
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    collection_name = serializers.CharField(source='collection.name', read_only=True)

    class Meta:
        model = ApiTestCase
        fields = [
            'id', 'name', 'project', 'project_name',
            'collection', 'collection_name', 'method', 'url',
            'created_time'
        ]


class ApiCollectionDetailSerializer(ApiCollectionSerializer):
    """
    API集合详情序列化器（包含测试用例列表）
    """
    test_cases = serializers.SerializerMethodField()

    def get_test_cases(self, obj):
        """获取集合的测试用例列表（仅未删除的）"""
        test_cases = obj.test_cases.filter(is_deleted=False)
        return ApiTestCaseListSerializer(test_cases, many=True).data

    class Meta(ApiCollectionSerializer.Meta):
        fields = ApiCollectionSerializer.Meta.fields + ['test_cases']


class ApiProjectDetailSerializer(ApiProjectSerializer):
    """
    API项目详情序列化器（包含集合和测试用例）
    """
    collections = ApiCollectionSerializer(many=True, read_only=True)
    recent_test_cases = ApiTestCaseListSerializer(many=True, read_only=True)

    class Meta(ApiProjectSerializer.Meta):
        fields = ApiProjectSerializer.Meta.fields + ['collections', 'recent_test_cases']


class ApiTestEnvironmentSerializer(serializers.ModelSerializer):
    """
    API测试环境序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)

    # 使用自定义 JSON 字段序列化器
    global_headers = JSONFieldSerializer(required=False, default=dict)
    global_variables = JSONFieldSerializer(required=False, default=dict)

    class Meta:
        model = ApiTestEnvironment
        fields = [
            'id', 'name', 'description', 'project', 'project_name',
            'base_url', 'global_headers', 'global_variables',
            'is_default', 'is_active', 'is_favorite', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']

    def validate_name(self, value):
        """验证环境名称"""
        if not value.strip():
            raise serializers.ValidationError("环境名称不能为空")
        return value.strip()

    def validate_base_url(self, value):
        """验证基础URL"""
        if not value.strip():
            raise serializers.ValidationError("基础URL不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证环境与项目的关系"""
        project = attrs.get('project')
        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        # 如果设置为默认环境，确保项目中只有一个默认环境
        is_default = attrs.get('is_default', False)
        if is_default and project:
            existing_default = ApiTestEnvironment.objects.filter(
                project=project, is_default=True, is_deleted=False
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_default.exists():
                raise serializers.ValidationError("项目中已存在默认环境")

        return attrs


class ApiTestExecutionSerializer(serializers.ModelSerializer):
    """
    API测试执行序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    # 使用自定义 JSON 字段序列化器
    test_cases = JSONFieldSerializer(required=False, default=list)

    class Meta:
        model = ApiTestExecution
        fields = [
            'id', 'name', 'description', 'project', 'project_name',
            'environment', 'environment_name', 'test_cases', 'status',
            'total_count', 'passed_count', 'failed_count', 'skipped_count',
            'start_time', 'end_time', 'duration',
            'created_by', 'created_by_name', 'created_time', 'updated_time'
        ]
        read_only_fields = [
            'id', 'status', 'total_count', 'passed_count', 'failed_count',
            'skipped_count', 'start_time', 'end_time', 'duration',
            'created_by', 'created_time', 'updated_time'
        ]

    def validate_name(self, value):
        """验证执行名称"""
        if not value.strip():
            raise serializers.ValidationError("执行名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证执行与项目、环境的关系"""
        project = attrs.get('project')
        environment = attrs.get('environment')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if environment and environment.project != project:
            raise serializers.ValidationError("所选环境不属于该项目")

        return attrs

    def create(self, validated_data):
        """创建执行记录"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ApiTestResultSerializer(serializers.ModelSerializer):
    """
    API测试结果序列化器
    """
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    test_case_method = serializers.CharField(source='test_case.method', read_only=True)
    test_case_url = serializers.CharField(source='test_case.url', read_only=True)

    # 使用自定义 JSON 字段序列化器
    request_headers = JSONFieldSerializer(required=False, default=dict)
    request_body = JSONFieldSerializer(required=False, default=dict)
    response_headers = JSONFieldSerializer(required=False, default=dict)
    response_body = JSONFieldSerializer(required=False, default=dict)
    assertion_results = JSONFieldSerializer(required=False, default=list)

    class Meta:
        model = ApiTestResult
        fields = [
            'id', 'execution', 'test_case', 'test_case_name',
            'test_case_method', 'test_case_url', 'status',
            'response_status', 'response_time', 'response_size',
            'request_url', 'request_method',
            'request_headers', 'request_body',
            'response_headers', 'response_body',
            'assertion_results', 'error_message',
            'start_time', 'end_time', 'duration'
        ]
        read_only_fields = ['id', 'start_time', 'end_time', 'duration']

    def validate(self, attrs):
        """验证结果与执行、用例的关系"""
        execution = attrs.get('execution')
        test_case = attrs.get('test_case')

        if execution and test_case and execution.project != test_case.project:
            raise serializers.ValidationError("所选测试用例不属于该执行记录的项目")

        return attrs


class ApiTestReportSerializer(serializers.ModelSerializer):
    """
    API测试报告序列化器
    """
    project_name = serializers.CharField(source='execution.project.name', read_only=True)
    execution_name = serializers.CharField(source='execution.name', read_only=True)

    # 使用自定义 JSON 字段序列化器
    summary = JSONFieldSerializer(required=False, default=dict)
    test_results = JSONFieldSerializer(required=False, default=list)
    charts_data = JSONFieldSerializer(required=False, default=dict)

    class Meta:
        model = ApiTestReport
        fields = [
            'id', 'execution', 'name', 'project_name', 'execution_name',
            'summary', 'test_results', 'charts_data',
            'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']

    def validate_name(self, value):
        """验证报告名称"""
        if not value.strip():
            raise serializers.ValidationError("报告名称不能为空")
        return value.strip()


class ApiDataDriverSerializer(serializers.ModelSerializer):
    """
    API数据驱动序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)

    # 使用自定义 JSON 字段序列化器
    data_source = JSONFieldSerializer(required=False, default=dict)
    data_content = JSONFieldSerializer(required=False, default=list)
    variable_mapping = JSONFieldSerializer(required=False, default=dict)

    class Meta:
        model = ApiDataDriver
        fields = [
            'id', 'name', 'description', 'project', 'project_name',
            'test_case', 'test_case_name', 'data_type',
            'data_source', 'data_content', 'variable_mapping',
            'is_active', 'created_time', 'updated_time'
        ]
        read_only_fields = ['id', 'created_time', 'updated_time']

    def validate_name(self, value):
        """验证数据源名称"""
        if not value.strip():
            raise serializers.ValidationError("数据源名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证数据驱动与项目、用例的关系"""
        project = attrs.get('project')
        test_case = attrs.get('test_case')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if test_case and test_case.project != project:
            raise serializers.ValidationError("所选测试用例不属于该项目")

        return attrs


class ApiTestExecutionDetailSerializer(ApiTestExecutionSerializer):
    """
    API测试执行详情序列化器（包含测试结果）
    """
    test_results = ApiTestResultSerializer(many=True, read_only=True)
    report = ApiTestReportSerializer(read_only=True)

    class Meta(ApiTestExecutionSerializer.Meta):
        fields = ApiTestExecutionSerializer.Meta.fields + ['test_results', 'report']


class ApiTestEnvironmentDetailSerializer(ApiTestEnvironmentSerializer):
    """
    API测试环境详情序列化器（包含执行历史）
    """
    recent_executions = ApiTestExecutionSerializer(many=True, read_only=True)

    class Meta(ApiTestEnvironmentSerializer.Meta):
        fields = ApiTestEnvironmentSerializer.Meta.fields + ['recent_executions']


class ApiTestCaseAssertionSerializer(serializers.ModelSerializer):
    """
    API测试用例断言配置序列化器
    """
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)

    class Meta:
        model = ApiTestCaseAssertion
        fields = [
            'id', 'test_case', 'test_case_name', 'assertion_type',
            'target', 'operator', 'expected_value', 'is_enabled',
            'order', 'created_time', 'updated_time'
        ]
        # test_case字段设置为只读，因为在perform_create中会从URL参数自动设置
        read_only_fields = ['id', 'test_case', 'test_case_name', 'created_time', 'updated_time']

    def validate_assertion_type(self, value):
        """验证断言类型"""
        valid_types = [choice[0] for choice in ApiTestCaseAssertion.ASSERTION_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的断言类型，必须是: {', '.join(valid_types)}")
        return value

    def validate_operator(self, value):
        """验证操作符"""
        valid_operators = [choice[0] for choice in ApiTestCaseAssertion.OPERATOR_CHOICES]
        if value not in valid_operators:
            raise serializers.ValidationError(f"无效的操作符，必须是: {', '.join(valid_operators)}")
        return value

    def validate(self, attrs):
        """验证断言配置"""
        assertion_type = attrs.get('assertion_type')
        target = attrs.get('target')
        expected_value = attrs.get('expected_value')

        # 某些断言类型需要目标字段
        if assertion_type in ['response_body', 'response_headers', 'json_value']:
            if not target:
                raise serializers.ValidationError(f"{assertion_type} 类型的断言必须指定目标字段")

        # 某些断言类型不需要目标字段
        if assertion_type in ['status_code', 'response_time', 'text_contains']:
            attrs['target'] = assertion_type

        # 验证期望值
        if assertion_type not in ['is_empty', 'is_not_empty', 'valid', 'invalid']:
            if expected_value is None or expected_value == '':
                raise serializers.ValidationError("该断言类型必须指定期望值")

        return attrs


class ApiTestCaseExtractionSerializer(serializers.ModelSerializer):
    """
    API测试用例数据提取配置序列化器
    """
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)

    class Meta:
        model = ApiTestCaseExtraction
        fields = [
            'id', 'test_case', 'test_case_name', 'variable_name',
            'extract_type', 'extract_expression', 'default_value',
            'extract_scope', 'variable_scope', 'is_enabled',
            'created_time', 'updated_time'
        ]
        # test_case字段设置为只读，因为在perform_create中会从URL参数自动设置
        read_only_fields = ['id', 'test_case', 'test_case_name', 'created_time', 'updated_time']

    def validate_variable_name(self, value):
        """验证变量名"""
        if not value or not value.strip():
            raise serializers.ValidationError("变量名不能为空")
        # 检查变量名格式（只允许字母、数字、下划线）
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("变量名只能包含字母、数字和下划线，且不能以数字开头")
        return value.strip()

    def validate_extract_type(self, value):
        """验证提取类型"""
        valid_types = [choice[0] for choice in ApiTestCaseExtraction.EXTRACT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的提取类型，必须是: {', '.join(valid_types)}")
        return value

    def validate_extract_expression(self, value):
        """验证提取表达式"""
        if not value or not value.strip():
            raise serializers.ValidationError("提取表达式不能为空")
        return value.strip()

    def validate(self, attrs):
        """验证提取配置"""
        extract_type = attrs.get('extract_type')
        extract_expression = attrs.get('extract_expression')
        extract_scope = attrs.get('extract_scope')

        # 验证表达式类型
        if extract_type == 'json_path':
            if not extract_expression.startswith('$.'):
                raise serializers.ValidationError("JSON路径表达式必须以 '$.' 开头")
        elif extract_type == 'regex':
            # 验证正则表达式
            import re
            try:
                re.compile(extract_expression)
            except re.error:
                raise serializers.ValidationError("无效的正则表达式")

        # 验证提取范围
        if extract_type == 'header' and extract_scope != 'headers':
            raise serializers.ValidationError("Header提取类型的范围必须是headers")
        if extract_type == 'cookie' and extract_scope != 'headers':
            raise serializers.ValidationError("Cookie提取类型的范围必须是headers")

        return attrs


class ApiTestCaseDetailSerializer(ApiTestCaseSerializer):
    """
    API测试用例详情序列化器（包含断言和数据提取配置）
    """
    assertions = ApiTestCaseAssertionSerializer(many=True, read_only=True)
    extractions = ApiTestCaseExtractionSerializer(many=True, read_only=True)

    class Meta(ApiTestCaseSerializer.Meta):
        fields = ApiTestCaseSerializer.Meta.fields + ['assertions', 'extractions', 'input_variables', 'output_variables']


class ApiHttpExecutionRecordSerializer(serializers.ModelSerializer):
    """
    HTTP执行记录序列化器
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True, default='')
    executed_by_username = serializers.CharField(source='executed_by.username', read_only=True, default='')

    # 格式化字段
    request_size_formatted = serializers.SerializerMethodField()
    response_size_formatted = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ApiHttpExecutionRecord
        fields = [
            'id', 'test_case', 'test_case_name', 'execution', 'project', 'project_name',
            'request_method', 'request_url', 'request_base_url', 'request_path',
            'request_headers', 'request_params', 'request_body', 'request_body_type', 'request_size',
            'response_status', 'response_status_text', 'response_headers', 'response_body',
            'response_body_text', 'response_size', 'response_encoding',
            'request_time', 'response_time', 'duration',
            'status', 'error_type', 'error_message', 'stack_trace',
            'assertion_results', 'assertions_passed', 'assertions_failed',
            'extraction_results', 'extracted_variables',
            'environment', 'environment_name', 'executed_by', 'executed_by_username',
            'execution_source', 'is_favorite', 'created_time',
            'request_size_formatted', 'response_size_formatted', 'duration_formatted'
        ]

    def get_request_size_formatted(self, obj):
        """格式化请求大小"""
        if obj.request_size:
            return f"{obj.request_size} B"
        return '-'

    def get_response_size_formatted(self, obj):
        """格式化响应大小"""
        if obj.response_size:
            if obj.response_size < 1024:
                return f"{obj.response_size} B"
            elif obj.response_size < 1024 * 1024:
                return f"{obj.response_size / 1024:.2f} KB"
            else:
                return f"{obj.response_size / (1024 * 1024):.2f} MB"
        return '-'

    def get_duration_formatted(self, obj):
        """格式化响应时间"""
        if obj.duration:
            return f"{obj.duration} ms"
        return '-'
