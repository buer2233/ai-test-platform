"""
api_automation/serializers.py

Django REST Framework 序列化器定义。

本模块定义了 API 自动化测试平台所有模型的序列化器，负责:
    - 模型实例与 JSON 之间的相互转换
    - 输入数据的校验（名称非空、关联关系合法性等）
    - 派生字段的计算（如集合数量、格式化显示等）

序列化器层级:
    基础序列化器 -- 用于列表和创建/更新操作
    详情序列化器 -- 继承基础序列化器，额外包含关联数据（如嵌套的子资源列表）
"""
import json
import re

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    ApiCollection,
    ApiDataDriver,
    ApiHttpExecutionRecord,
    ApiProject,
    ApiTestCase,
    ApiTestCaseAssertion,
    ApiTestCaseExtraction,
    ApiTestEnvironment,
    ApiTestExecution,
    ApiTestReport,
    ApiTestResult,
)


class JSONFieldSerializer(serializers.Field):
    """
    自定义 JSON 字段序列化器。

    处理前端传入的 JSON 数据，接受字典或 JSON 字符串两种格式，
    统一转换为 Python 字典后传递给模型层。
    """

    def to_internal_value(self, data):
        """将输入数据转换为 Python 字典（写入方向）。"""
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
        """将模型值直接输出为 JSON（读取方向，无需额外转换）。"""
        return value


# =============================================================================
# 用户序列化器
# =============================================================================


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器，仅暴露基本用户属性（只读 ID）。"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


# =============================================================================
# 项目序列化器
# =============================================================================


class ApiProjectSerializer(serializers.ModelSerializer):
    """
    API项目序列化器。

    包含项目基本信息及派生统计字段（集合数量、测试用例数量）。
    创建时若未指定 owner，自动设置为当前请求用户。
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
        """统计项目下未删除的集合数量。"""
        return obj.api_collections.filter(is_deleted=False).count()

    def get_test_cases_count(self, obj):
        """统计项目下未删除的测试用例数量。"""
        return obj.test_cases.filter(is_deleted=False).count()

    def validate_name(self, value):
        """校验项目名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("项目名称不能为空")
        return value.strip()

    def create(self, validated_data):
        """创建项目时，若未指定负责人则自动设置为当前用户。"""
        request = self.context.get('request')
        if request and request.user and not validated_data.get('owner_id'):
            validated_data['owner'] = request.user
        return super().create(validated_data)


# =============================================================================
# 集合序列化器
# =============================================================================


class ApiCollectionSerializer(serializers.ModelSerializer):
    """
    API集合序列化器。

    包含集合基本信息、所属项目名称和测试用例数量统计。
    校验集合名称非空，以及所属项目必须处于激活状态。
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
        """统计集合下未删除的测试用例数量。"""
        return obj.test_cases.filter(is_deleted=False).count()

    def validate_name(self, value):
        """校验集合名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("集合名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """校验关联关系：所属项目必须处于激活状态。"""
        project = attrs.get('project')
        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")
        return attrs


# =============================================================================
# 测试用例序列化器
# =============================================================================


class ApiTestCaseSerializer(serializers.ModelSerializer):
    """
    API测试用例序列化器。

    包含完整的 HTTP 请求定义（方法、URL、请求头、参数、请求体），
    以及用于前端友好展示的格式化字段。
    创建时自动设置 created_by 为当前用户。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    collection_name = serializers.CharField(source='collection.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    # 格式化展示字段：返回原始值或空字典
    headers_display = serializers.SerializerMethodField(read_only=True)
    params_display = serializers.SerializerMethodField(read_only=True)
    body_display = serializers.SerializerMethodField(read_only=True)

    # JSON 字段使用自定义序列化器处理
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
        """返回请求头数据，为空时返回空字典。"""
        return obj.headers or {}

    def get_params_display(self, obj):
        """返回请求参数数据，为空时返回空字典。"""
        return obj.params or {}

    def get_body_display(self, obj):
        """返回请求体数据，为空时返回空字典。"""
        return obj.body or {}

    def validate_name(self, value):
        """校验用例名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("用例名称不能为空")
        return value.strip()

    def validate_url(self, value):
        """校验 URL：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("URL不能为空")
        return value.strip()

    def validate(self, attrs):
        """校验关联关系：项目须激活，集合须归属该项目。"""
        project = attrs.get('project')
        collection = attrs.get('collection')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if collection and collection.project != project:
            raise serializers.ValidationError("所选集合不属于该项目")

        return attrs

    def create(self, validated_data):
        """创建用例时自动设置 created_by 为当前请求用户。"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ApiTestCaseListSerializer(serializers.ModelSerializer):
    """API测试用例列表序列化器（精简版），仅包含列表页所需的关键字段。"""

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
    """API集合详情序列化器，在基础序列化器上额外嵌套未删除的测试用例列表。"""

    test_cases = serializers.SerializerMethodField()

    def get_test_cases(self, obj):
        """获取集合下未删除的测试用例列表（精简格式）。"""
        test_cases = obj.test_cases.filter(is_deleted=False)
        return ApiTestCaseListSerializer(test_cases, many=True).data

    class Meta(ApiCollectionSerializer.Meta):
        fields = ApiCollectionSerializer.Meta.fields + ['test_cases']


class ApiProjectDetailSerializer(ApiProjectSerializer):
    """API项目详情序列化器，在基础序列化器上额外嵌套集合和最近测试用例。"""

    collections = ApiCollectionSerializer(many=True, read_only=True)
    recent_test_cases = ApiTestCaseListSerializer(many=True, read_only=True)

    class Meta(ApiProjectSerializer.Meta):
        fields = ApiProjectSerializer.Meta.fields + ['collections', 'recent_test_cases']


# =============================================================================
# 环境序列化器
# =============================================================================


class ApiTestEnvironmentSerializer(serializers.ModelSerializer):
    """
    API测试环境序列化器。

    包含环境配置信息（基础URL、全局请求头、全局变量等），
    校验环境名称和 URL 非空，以及同一项目下仅允许一个默认环境。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)

    # JSON 字段使用自定义序列化器处理
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
        """校验环境名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("环境名称不能为空")
        return value.strip()

    def validate_base_url(self, value):
        """校验基础 URL：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("基础URL不能为空")
        return value.strip()

    def validate(self, attrs):
        """
        校验关联关系和默认环境唯一性。

        规则:
            - 所属项目必须处于激活状态
            - 同一项目下最多只能有一个默认环境
        """
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


# =============================================================================
# 执行与结果序列化器
# =============================================================================


class ApiTestExecutionSerializer(serializers.ModelSerializer):
    """
    API测试执行序列化器。

    包含执行基本信息和状态统计。
    创建时自动设置 created_by 为当前用户。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

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
        """校验执行名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("执行名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """校验关联关系：项目须激活，环境须归属该项目。"""
        project = attrs.get('project')
        environment = attrs.get('environment')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if environment and environment.project != project:
            raise serializers.ValidationError("所选环境不属于该项目")

        return attrs

    def create(self, validated_data):
        """创建执行记录时自动设置 created_by 为当前请求用户。"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ApiTestResultSerializer(serializers.ModelSerializer):
    """
    API测试结果序列化器。

    包含单个测试用例的执行结果详情，包括请求/响应数据和断言结果。
    校验执行记录与测试用例须属于同一项目。
    """

    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    test_case_method = serializers.CharField(source='test_case.method', read_only=True)
    test_case_url = serializers.CharField(source='test_case.url', read_only=True)

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
        """校验关联关系：测试用例须属于执行记录所在项目。"""
        execution = attrs.get('execution')
        test_case = attrs.get('test_case')

        if execution and test_case and execution.project != test_case.project:
            raise serializers.ValidationError("所选测试用例不属于该执行记录的项目")

        return attrs


# =============================================================================
# 报告序列化器
# =============================================================================


class ApiTestReportSerializer(serializers.ModelSerializer):
    """API测试报告序列化器，包含报告摘要、详细结果和图表数据。"""

    project_name = serializers.CharField(source='execution.project.name', read_only=True)
    execution_name = serializers.CharField(source='execution.name', read_only=True)

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
        """校验报告名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("报告名称不能为空")
        return value.strip()


# =============================================================================
# 数据驱动序列化器
# =============================================================================


class ApiDataDriverSerializer(serializers.ModelSerializer):
    """
    API数据驱动序列化器。

    包含数据源配置、数据内容和变量映射信息。
    校验数据源名称非空，以及测试用例须属于指定项目。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)

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
        """校验数据源名称：不允许为空或纯空格。"""
        if not value.strip():
            raise serializers.ValidationError("数据源名称不能为空")
        return value.strip()

    def validate(self, attrs):
        """校验关联关系：项目须激活，测试用例须属于指定项目。"""
        project = attrs.get('project')
        test_case = attrs.get('test_case')

        if project and not project.is_active:
            raise serializers.ValidationError("所选项目已被禁用")

        if test_case and test_case.project != project:
            raise serializers.ValidationError("所选测试用例不属于该项目")

        return attrs


# =============================================================================
# 详情序列化器（嵌套关联数据）
# =============================================================================


class ApiTestExecutionDetailSerializer(ApiTestExecutionSerializer):
    """API测试执行详情序列化器，额外嵌套测试结果列表和报告。"""

    test_results = ApiTestResultSerializer(many=True, read_only=True)
    report = ApiTestReportSerializer(read_only=True)

    class Meta(ApiTestExecutionSerializer.Meta):
        fields = ApiTestExecutionSerializer.Meta.fields + ['test_results', 'report']


class ApiTestEnvironmentDetailSerializer(ApiTestEnvironmentSerializer):
    """API测试环境详情序列化器，额外嵌套最近的执行记录。"""

    recent_executions = ApiTestExecutionSerializer(many=True, read_only=True)

    class Meta(ApiTestEnvironmentSerializer.Meta):
        fields = ApiTestEnvironmentSerializer.Meta.fields + ['recent_executions']


# =============================================================================
# 断言与数据提取序列化器
# =============================================================================


class ApiTestCaseAssertionSerializer(serializers.ModelSerializer):
    """
    测试用例断言配置序列化器。

    校验断言类型和操作符的合法性，以及根据断言类型自动设置目标字段
    和校验期望值是否必填。test_case 字段为只读，由视图层通过 URL 参数自动设置。
    """

    test_case_name = serializers.CharField(source='test_case.name', read_only=True)

    class Meta:
        model = ApiTestCaseAssertion
        fields = [
            'id', 'test_case', 'test_case_name', 'assertion_type',
            'target', 'operator', 'expected_value', 'is_enabled',
            'order', 'created_time', 'updated_time'
        ]
        # test_case 由视图层 perform_create 中从 URL 参数自动设置
        read_only_fields = ['id', 'test_case', 'test_case_name', 'created_time', 'updated_time']

    def validate_assertion_type(self, value):
        """校验断言类型是否在允许的选项范围内。"""
        valid_types = [choice[0] for choice in ApiTestCaseAssertion.ASSERTION_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的断言类型，必须是: {', '.join(valid_types)}")
        return value

    def validate_operator(self, value):
        """校验操作符是否在允许的选项范围内。"""
        valid_operators = [choice[0] for choice in ApiTestCaseAssertion.OPERATOR_CHOICES]
        if value not in valid_operators:
            raise serializers.ValidationError(f"无效的操作符，必须是: {', '.join(valid_operators)}")
        return value

    def validate(self, attrs):
        """
        校验断言配置的完整性。

        规则:
            - response_body/response_headers/json_value 类型必须指定目标字段
            - status_code/response_time/text_contains 类型自动设置目标字段
            - 除 is_empty/is_not_empty/valid/invalid 外，均需指定期望值
        """
        assertion_type = attrs.get('assertion_type')
        target = attrs.get('target')
        expected_value = attrs.get('expected_value')

        # 某些断言类型需要目标字段
        if assertion_type in ['response_body', 'response_headers', 'json_value']:
            if not target:
                raise serializers.ValidationError(
                    f"{assertion_type} 类型的断言必须指定目标字段"
                )

        # 某些断言类型自动填充目标字段为断言类型本身
        if assertion_type in ['status_code', 'response_time', 'text_contains']:
            attrs['target'] = assertion_type

        # 非状态类操作符要求必须填写期望值
        if assertion_type not in ['is_empty', 'is_not_empty', 'valid', 'invalid']:
            if expected_value is None or expected_value == '':
                raise serializers.ValidationError("该断言类型必须指定期望值")

        return attrs


class ApiTestCaseExtractionSerializer(serializers.ModelSerializer):
    """
    测试用例数据提取配置序列化器。

    校验变量名格式（字母/数字/下划线，不以数字开头）、提取类型合法性、
    提取表达式格式（如 JSONPath 需以 $. 开头）以及提取范围的一致性。
    test_case 字段为只读，由视图层通过 URL 参数自动设置。
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
        # test_case 由视图层 perform_create 中从 URL 参数自动设置
        read_only_fields = ['id', 'test_case', 'test_case_name', 'created_time', 'updated_time']

    def validate_variable_name(self, value):
        """校验变量名格式：仅允许字母/数字/下划线，且不以数字开头。"""
        if not value or not value.strip():
            raise serializers.ValidationError("变量名不能为空")
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "变量名只能包含字母、数字和下划线，且不能以数字开头"
            )
        return value.strip()

    def validate_extract_type(self, value):
        """校验提取类型是否在允许的选项范围内。"""
        valid_types = [choice[0] for choice in ApiTestCaseExtraction.EXTRACT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"无效的提取类型，必须是: {', '.join(valid_types)}")
        return value

    def validate_extract_expression(self, value):
        """校验提取表达式：不允许为空或纯空格。"""
        if not value or not value.strip():
            raise serializers.ValidationError("提取表达式不能为空")
        return value.strip()

    def validate(self, attrs):
        """
        校验提取配置的一致性。

        规则:
            - JSONPath 表达式必须以 $. 开头
            - 正则表达式必须是合法的 regex 语法
            - header/cookie 类型的提取范围必须是 headers
        """
        extract_type = attrs.get('extract_type')
        extract_expression = attrs.get('extract_expression')
        extract_scope = attrs.get('extract_scope')

        if extract_type == 'json_path':
            if not extract_expression.startswith('$.'):
                raise serializers.ValidationError("JSON路径表达式必须以 '$.' 开头")
        elif extract_type == 'regex':
            try:
                re.compile(extract_expression)
            except re.error:
                raise serializers.ValidationError("无效的正则表达式")

        # header/cookie 提取类型的范围必须限定为响应头
        if extract_type == 'header' and extract_scope != 'headers':
            raise serializers.ValidationError("Header提取类型的范围必须是headers")
        if extract_type == 'cookie' and extract_scope != 'headers':
            raise serializers.ValidationError("Cookie提取类型的范围必须是headers")

        return attrs


class ApiTestCaseDetailSerializer(ApiTestCaseSerializer):
    """API测试用例详情序列化器，额外嵌套断言配置、数据提取配置和变量定义。"""

    assertions = ApiTestCaseAssertionSerializer(many=True, read_only=True)
    extractions = ApiTestCaseExtractionSerializer(many=True, read_only=True)

    class Meta(ApiTestCaseSerializer.Meta):
        fields = ApiTestCaseSerializer.Meta.fields + ['assertions', 'extractions', 'input_variables', 'output_variables']


# =============================================================================
# HTTP执行记录序列化器
# =============================================================================


class ApiHttpExecutionRecordSerializer(serializers.ModelSerializer):
    """
    HTTP执行记录序列化器。

    包含完整的请求/响应信息，以及格式化后的大小和耗时展示字段。
    """

    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    environment_name = serializers.CharField(
        source='environment.name', read_only=True, default=''
    )
    executed_by_username = serializers.CharField(
        source='executed_by.username', read_only=True, default=''
    )

    # 格式化展示字段
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
        """将请求大小格式化为可读字符串（如 '128 B'）。"""
        if obj.request_size:
            return f"{obj.request_size} B"
        return '-'

    def get_response_size_formatted(self, obj):
        """将响应大小格式化为可读字符串，自动选择 B/KB/MB 单位。"""
        if not obj.response_size:
            return '-'
        size = obj.response_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"

    def get_duration_formatted(self, obj):
        """将响应耗时格式化为毫秒字符串（如 '150 ms'）。"""
        if obj.duration:
            return f"{obj.duration} ms"
        return '-'
