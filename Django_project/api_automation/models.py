"""
api_automation/models.py

API自动化测试模块的数据模型定义。

本模块定义了 API 自动化测试平台的核心数据结构，涵盖从项目组织到测试执行的完整生命周期。
所有支持软删除的模型均包含 is_deleted 字段，物理删除由回收站服务统一管理。

模型层级关系:
    ApiProject（项目）
    ├── ApiCollection（集合）
    │   └── ApiTestCase（测试用例）
    │       ├── ApiTestCaseAssertion（断言配置）
    │       ├── ApiTestCaseExtraction（数据提取配置）
    │       └── ApiDataDriver（数据驱动配置）
    ├── ApiTestEnvironment（测试环境）
    └── ApiTestExecution（执行记录）
        ├── ApiTestResult（执行结果）
        ├── ApiTestReport（测试报告）
        └── ApiHttpExecutionRecord（HTTP请求记录）

数据库表命名规范: 所有表名使用 api_ 前缀 + 小写下划线 + 复数形式。
"""
import json

from django.contrib.auth.models import User
from django.db import models


# =============================================================================
# 自定义字段
# =============================================================================


class JSONField(models.TextField):
    """
    兼容 SQLite 的自定义 JSON 字段。

    在数据库中以 TEXT 类型存储 JSON 字符串，
    读取时自动反序列化为 Python 字典/列表，写入时自动序列化为 JSON 字符串。
    适用于不支持原生 JSONField 的数据库后端（如 SQLite）。
    """

    description = "JSON data"

    def from_db_value(self, value, expression, connection):
        """从数据库读取时，将 JSON 字符串反序列化为 Python 对象。"""
        if value is None:
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def to_python(self, value):
        """将值转换为 Python 对象（表单验证和反序列化时调用）。"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return value
        return value

    def get_prep_value(self, value):
        """写入数据库前，将 Python 对象序列化为 JSON 字符串。"""
        if value is None:
            return value
        return json.dumps(value, ensure_ascii=False)

    def value_to_string(self, obj):
        """序列化时将字段值转为字符串表示（用于 dumpdata 等场景）。"""
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


# =============================================================================
# 项目与集合管理
# =============================================================================


class ApiProject(models.Model):
    """
    API测试项目 -- 最顶层的组织单元。

    每个项目可包含多个集合、测试用例、环境配置和执行记录。
    通过 owner 字段实现基于用户的数据隔离。
    """

    name = models.CharField(max_length=100, verbose_name='项目名称')
    description = models.TextField(blank=True, null=True, verbose_name='项目描述')
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_projects',
        verbose_name='负责人'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_projects'
        verbose_name = 'API项目'
        verbose_name_plural = 'API项目'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['owner', 'is_deleted'], name='project_owner_deleted_idx'),
            models.Index(fields=['created_time'], name='project_created_idx'),
        ]

    def __str__(self):
        return self.name


class ApiCollection(models.Model):
    """
    API集合 -- 用于组织和分组同一项目下的测试用例。

    集合是项目下的二级组织单元，可按业务模块或功能维度对测试用例进行分组。
    """

    name = models.CharField(max_length=100, verbose_name='集合名称')
    description = models.TextField(blank=True, null=True, verbose_name='集合描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='api_collections',
        verbose_name='所属项目'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections',
        verbose_name='负责人'
    )
    module = models.CharField(max_length=100, null=True, blank=True, verbose_name='所属模块')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_collections'
        verbose_name = 'API集合'
        verbose_name_plural = 'API集合'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'is_deleted'], name='collection_project_deleted_idx'),
            models.Index(fields=['project', 'name'], name='collection_project_name_idx'),
            models.Index(fields=['created_time'], name='collection_created_idx'),
            models.Index(fields=['owner'], name='collection_owner_idx'),
            models.Index(fields=['module'], name='collection_module_idx'),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"


# =============================================================================
# 测试用例及其配置
# =============================================================================


class ApiTestCase(models.Model):
    """
    API测试用例 -- 记录单个接口的请求定义和期望验证。

    包含完整的 HTTP 请求信息（方法、URL、请求头、参数、请求体）、
    断言配置以及用于串联执行的输入/输出变量定义。
    """

    name = models.CharField(max_length=100, verbose_name='用例名称')
    description = models.TextField(blank=True, null=True, verbose_name='用例描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='所属项目'
    )
    collection = models.ForeignKey(
        ApiCollection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_cases',
        verbose_name='所属集合'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_cases',
        verbose_name='负责人'
    )
    module = models.CharField(max_length=100, null=True, blank=True, verbose_name='所属模块')

    # HTTP 请求定义
    method = models.CharField(
        max_length=10,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
        ],
        verbose_name='请求方法'
    )
    url = models.TextField(verbose_name='接口地址')
    headers = JSONField(default=dict, blank=True, verbose_name='请求头')
    params = JSONField(default=dict, blank=True, verbose_name='请求参数')
    body = JSONField(default=dict, blank=True, verbose_name='请求体')
    tests = JSONField(default=list, blank=True, verbose_name='断言配置')

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_test_cases',
        verbose_name='创建者'
    )
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    # 串联执行预留字段：输入变量（从前置用例或环境中获取）
    input_variables = JSONField(
        default=dict,
        blank=True,
        verbose_name='输入变量定义',
        help_text='定义从前置用例或环境中获取的输入变量'
    )

    # 串联执行预留字段：输出变量（从响应中提取供后续用例使用）
    output_variables = JSONField(
        default=dict,
        blank=True,
        verbose_name='输出变量定义',
        help_text='定义从响应中提取的输出变量，供后续用例使用'
    )

    class Meta:
        db_table = 'api_test_cases'
        verbose_name = 'API测试用例'
        verbose_name_plural = 'API测试用例'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['collection', 'is_deleted'], name='case_collection_deleted_idx'),
            models.Index(fields=['project', 'is_deleted'], name='case_project_deleted_idx'),
            models.Index(fields=['created_time'], name='case_created_idx'),
            models.Index(fields=['owner'], name='case_owner_idx'),
            models.Index(fields=['module'], name='case_module_idx'),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ApiTestCaseAssertion(models.Model):
    """
    测试用例断言配置 -- 定义对接口响应的验证规则。

    支持多种断言类型（状态码、响应时间、JSON值等）和操作符（等于、包含、正则等），
    可按 order 字段控制断言执行顺序。
    """

    # 断言类型选项
    ASSERTION_TYPE_CHOICES = [
        ('status_code', 'HTTP状态码'),
        ('response_time', '响应时间'),
        ('response_body', '响应体'),
        ('response_headers', '响应头'),
        ('json_value', 'JSON值'),
        ('text_contains', '文本包含'),
        ('json_schema', 'JSON Schema'),
    ]

    # 比较操作符选项
    OPERATOR_CHOICES = [
        ('equals', '等于'),
        ('not_equals', '不等于'),
        ('contains', '包含'),
        ('not_contains', '不包含'),
        ('less_than', '小于'),
        ('less_than_equal', '小于等于'),
        ('greater_than', '大于'),
        ('greater_than_equal', '大于等于'),
        ('regex', '正则匹配'),
        ('json_path', 'JSON路径'),
        ('is_empty', '为空'),
        ('is_not_empty', '不为空'),
        ('range', '范围'),
        ('valid', '有效'),
        ('invalid', '无效'),
    ]

    SCOPE_CHOICES = [
        ('local', '当前测试用例'),
        ('global', '全局作用域'),
    ]

    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='assertions',
        verbose_name='测试用例'
    )
    assertion_type = models.CharField(
        max_length=20,
        choices=ASSERTION_TYPE_CHOICES,
        verbose_name='断言类型'
    )
    target = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='目标字段',
        help_text='如: status_code, headers.content-type, $.data.id'
    )
    operator = models.CharField(
        max_length=20,
        choices=OPERATOR_CHOICES,
        verbose_name='操作符'
    )
    expected_value = models.TextField(blank=True, null=True, verbose_name='期望值')
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    order = models.IntegerField(default=0, verbose_name='执行顺序')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_test_case_assertions'
        verbose_name = '测试用例断言'
        verbose_name_plural = '测试用例断言'
        ordering = ['order', 'created_time']

    def __str__(self):
        return f"{self.test_case.name} - {self.get_assertion_type_display()}"


class ApiTestCaseExtraction(models.Model):
    """
    测试用例数据提取配置 -- 定义如何从接口响应中提取变量。

    支持多种提取方式（正则、JSONPath、XPath 等），提取的变量可在后续
    串联用例中通过变量引用使用，实现接口间的数据传递。
    """

    EXTRACT_TYPE_CHOICES = [
        ('regex', '正则表达式'),
        ('json_path', 'JSON路径'),
        ('xpath', 'XPath表达式'),
        ('css_selector', 'CSS选择器'),
        ('header', 'Header解析'),
        ('cookie', 'Cookie解析'),
    ]

    SCOPE_CHOICES = [
        ('local', '局部变量'),
        ('global', '全局变量'),
    ]

    EXTRACT_SCOPE_CHOICES = [
        ('body', '响应体'),
        ('headers', '响应头'),
        ('url', 'URL'),
    ]

    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='extractions',
        verbose_name='测试用例'
    )
    variable_name = models.CharField(
        max_length=100,
        verbose_name='变量名',
        help_text='变量名，用于在后续请求中引用'
    )
    extract_type = models.CharField(
        max_length=20,
        choices=EXTRACT_TYPE_CHOICES,
        verbose_name='提取类型'
    )
    extract_expression = models.TextField(
        verbose_name='提取表达式',
        help_text='根据提取类型，填写相应的表达式'
    )
    default_value = models.TextField(
        blank=True,
        null=True,
        verbose_name='默认值',
        help_text='提取失败时使用的默认值'
    )
    extract_scope = models.CharField(
        max_length=20,
        choices=EXTRACT_SCOPE_CHOICES,
        default='body',
        verbose_name='提取范围'
    )
    variable_scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='local',
        verbose_name='变量作用域'
    )
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_test_case_extractions'
        verbose_name = '测试用例数据提取'
        verbose_name_plural = '测试用例数据提取'
        ordering = ['created_time']

    def __str__(self):
        return f"{self.test_case.name} - ${self.variable_name}"


# =============================================================================
# 测试环境
# =============================================================================


class ApiTestEnvironment(models.Model):
    """
    API测试环境 -- 定义接口测试的目标服务器及全局配置。

    包含基础 URL、全局请求头和全局变量等配置。
    每个项目可创建多个环境（如开发、测试、预发布），
    通过 is_default 标记默认环境。
    """

    name = models.CharField(max_length=100, verbose_name='环境名称')
    description = models.TextField(blank=True, null=True, verbose_name='环境描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='test_environments',
        verbose_name='所属项目'
    )
    base_url = models.URLField(verbose_name='基础URL')
    global_headers = JSONField(default=dict, blank=True, verbose_name='全局请求头')
    global_variables = JSONField(default=dict, blank=True, verbose_name='全局变量')
    is_default = models.BooleanField(default=False, verbose_name='是否默认环境')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    is_favorite = models.BooleanField(default=False, verbose_name='是否收藏')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_test_environments'
        verbose_name = 'API测试环境'
        verbose_name_plural = 'API测试环境'
        ordering = ['-is_favorite', '-created_time']
        indexes = [
            models.Index(fields=['project', 'is_deleted'], name='env_project_deleted_idx'),
            models.Index(fields=['project', 'is_default'], name='env_project_default_idx'),
            models.Index(fields=['is_favorite'], name='env_favorite_idx'),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"


# =============================================================================
# 测试执行与结果
# =============================================================================


class ApiTestExecution(models.Model):
    """
    API测试执行记录 -- 记录一次批量测试执行的整体信息。

    一次执行可包含多个测试用例，记录执行状态、统计计数、
    起止时间等信息。通过 WebSocket 实时推送执行进度。
    """

    name = models.CharField(max_length=200, verbose_name='执行名称')
    description = models.TextField(blank=True, null=True, verbose_name='执行描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='test_executions',
        verbose_name='所属项目'
    )
    environment = models.ForeignKey(
        ApiTestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_executions',
        verbose_name='执行环境'
    )
    test_cases = JSONField(default=list, verbose_name='测试用例ID列表')
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', '待执行'),
            ('RUNNING', '执行中'),
            ('COMPLETED', '已完成'),
            ('FAILED', '执行失败'),
            ('CANCELLED', '已取消'),
        ],
        default='PENDING',
        verbose_name='执行状态'
    )
    total_count = models.IntegerField(default=0, verbose_name='总用例数')
    passed_count = models.IntegerField(default=0, verbose_name='通过数')
    failed_count = models.IntegerField(default=0, verbose_name='失败数')
    skipped_count = models.IntegerField(default=0, verbose_name='跳过数')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='执行时长(秒)')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_executions',
        verbose_name='创建者'
    )
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_test_executions'
        verbose_name = 'API测试执行'
        verbose_name_plural = 'API测试执行'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'created_time'], name='exec_project_created_idx'),
            models.Index(fields=['environment', 'status'], name='exec_env_status_idx'),
            models.Index(fields=['status', 'created_time'], name='exec_status_created_idx'),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ApiTestReport(models.Model):
    """
    API测试报告 -- 与执行记录一对一关联的汇总报告。

    包含执行摘要、详细测试结果和图表数据，
    用于生成可视化的测试报告。
    """

    execution = models.OneToOneField(
        ApiTestExecution,
        on_delete=models.CASCADE,
        related_name='report',
        verbose_name='执行记录'
    )
    name = models.CharField(max_length=200, verbose_name='报告名称')
    summary = JSONField(default=dict, verbose_name='执行摘要')
    test_results = JSONField(default=list, verbose_name='测试结果详情')
    charts_data = JSONField(default=dict, verbose_name='图表数据')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_test_reports'
        verbose_name = 'API测试报告'
        verbose_name_plural = 'API测试报告'
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.execution.project.name} - {self.name}"


class ApiTestResult(models.Model):
    """
    API测试结果 -- 记录单个测试用例在一次执行中的详细结果。

    采用数据分级存储策略:
        - HTTP 2xx 响应：仅存储请求/响应摘要信息（节省存储空间）
        - 非 2xx 或错误响应：存储完整请求/响应数据（方便问题排查）
    """

    execution = models.ForeignKey(
        ApiTestExecution,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name='执行记录'
    )
    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='test_results',
        verbose_name='测试用例'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PASSED', '通过'),
            ('FAILED', '失败'),
            ('SKIPPED', '跳过'),
            ('ERROR', '错误'),
        ],
        verbose_name='测试状态'
    )
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_time = models.IntegerField(null=True, blank=True, verbose_name='响应时间(ms)')
    response_size = models.IntegerField(null=True, blank=True, verbose_name='响应大小(bytes)')
    request_url = models.TextField(blank=True, null=True, verbose_name='请求URL')
    request_method = models.CharField(max_length=10, blank=True, null=True, verbose_name='请求方法')

    # 兼容字段：保留供现有代码使用
    request_headers = JSONField(default=dict, blank=True, verbose_name='请求头（兼容）')
    request_body = JSONField(default=dict, blank=True, verbose_name='请求体（兼容）')
    response_headers = JSONField(default=dict, blank=True, verbose_name='响应头（兼容）')
    response_body = JSONField(default=dict, blank=True, verbose_name='响应体（兼容）')

    # 分级存储：成功响应的摘要信息
    request_summary = JSONField(
        default=dict,
        blank=True,
        verbose_name='请求摘要',
        help_text='HTTP 200时存储：method, url, 关键headers'
    )
    response_summary = JSONField(
        default=dict,
        blank=True,
        verbose_name='响应摘要',
        help_text='HTTP 200时存储：status_code, response_time, content_length'
    )

    # 分级存储：失败/错误响应的完整信息
    request_full = JSONField(
        default=dict,
        blank=True,
        verbose_name='完整请求信息',
        help_text='HTTP非200时存储：完整headers、body、params等'
    )
    response_full = JSONField(
        default=dict,
        blank=True,
        verbose_name='完整响应信息',
        help_text='HTTP非200时存储：完整headers、body、error_stack等'
    )
    error_info = JSONField(
        default=dict,
        blank=True,
        verbose_name='错误详情',
        help_text='存储错误类型、堆栈、断言失败详情等'
    )

    assertion_results = JSONField(default=list, blank=True, verbose_name='断言结果')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='执行时长(ms)')

    # 数据提取结果（支持串联执行的变量传递）
    extracted_variables = JSONField(
        default=dict,
        blank=True,
        verbose_name='提取的变量',
        help_text='存储从响应中提取的变量，供后续用例使用'
    )

    class Meta:
        db_table = 'api_test_results'
        verbose_name = 'API测试结果'
        verbose_name_plural = 'API测试结果'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['execution', 'status'], name='result_exec_status_idx'),
            models.Index(fields=['test_case', 'start_time'], name='result_case_time_idx'),
            models.Index(fields=['status', 'start_time'], name='result_status_time_idx'),
        ]

    def __str__(self):
        return f"{self.test_case.name} - {self.status}"


# =============================================================================
# 数据驱动
# =============================================================================


class ApiDataDriver(models.Model):
    """
    API数据驱动配置 -- 为测试用例提供参数化数据源。

    支持多种数据源类型（JSON、CSV、Excel、数据库），
    通过变量映射将数据源字段对应到测试用例的请求参数。
    """

    name = models.CharField(max_length=100, verbose_name='数据源名称')
    description = models.TextField(blank=True, null=True, verbose_name='数据源描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='data_drivers',
        verbose_name='所属项目'
    )
    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='data_drivers',
        verbose_name='关联测试用例'
    )
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('JSON', 'JSON数据'),
            ('CSV', 'CSV文件'),
            ('EXCEL', 'Excel文件'),
            ('DATABASE', '数据库'),
        ],
        default='JSON',
        verbose_name='数据类型'
    )
    data_source = JSONField(default=dict, verbose_name='数据源配置')
    data_content = JSONField(default=list, verbose_name='数据内容')
    variable_mapping = JSONField(default=dict, verbose_name='变量映射')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_data_drivers'
        verbose_name = 'API数据驱动'
        verbose_name_plural = 'API数据驱动'
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


# =============================================================================
# HTTP执行记录
# =============================================================================


class ApiHttpExecutionRecord(models.Model):
    """
    HTTP接口执行记录 -- 记录每次 HTTP 请求的完整执行信息。

    用于调试、历史查询和执行回放。记录包含完整的请求/响应数据、
    断言结果、数据提取结果以及错误堆栈等信息。
    """

    # ---- 关联信息 ----
    test_case = models.ForeignKey(
        'ApiTestCase',
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='测试用例',
        null=True,
        blank=True
    )
    execution = models.ForeignKey(
        'ApiTestExecution',
        on_delete=models.CASCADE,
        related_name='http_records',
        verbose_name='执行批次',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='http_execution_records',
        verbose_name='所属项目'
    )

    # ---- 请求信息 ----
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_url = models.TextField(verbose_name='完整请求URL')
    request_base_url = models.TextField(verbose_name='基础URL')
    request_path = models.TextField(verbose_name='请求路径')
    request_headers = JSONField(default=dict, verbose_name='请求头')
    request_params = JSONField(default=dict, verbose_name='Query参数')
    request_body = JSONField(default=dict, blank=True, verbose_name='请求体')
    request_body_type = models.CharField(
        max_length=20,
        choices=[
            ('JSON', 'JSON'),
            ('FORM', '表单'),
            ('RAW', '原始'),
            ('NONE', '无'),
        ],
        default='NONE',
        verbose_name='请求体类型'
    )
    request_size = models.IntegerField(null=True, blank=True, verbose_name='请求大小(bytes)')

    # ---- 响应信息 ----
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_status_text = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='响应状态文本'
    )
    response_headers = JSONField(default=dict, blank=True, verbose_name='响应头')
    response_body = JSONField(default=dict, blank=True, verbose_name='响应体')
    response_body_text = models.TextField(
        blank=True, null=True, verbose_name='响应体原文(非JSON)'
    )
    response_size = models.IntegerField(null=True, blank=True, verbose_name='响应大小(bytes)')
    response_encoding = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='响应编码'
    )

    # ---- 时间信息 ----
    request_time = models.DateTimeField(verbose_name='请求发送时间')
    response_time = models.DateTimeField(null=True, blank=True, verbose_name='响应接收时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='响应时间(ms)')

    # ---- 执行状态 ----
    status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', '成功'),
            ('FAILED', '失败'),
            ('TIMEOUT', '超时'),
            ('ERROR', '错误'),
        ],
        default='ERROR',
        verbose_name='执行状态'
    )

    # ---- 错误信息 ----
    error_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='错误类型')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    stack_trace = models.TextField(blank=True, null=True, verbose_name='错误堆栈')

    # ---- 断言结果 ----
    assertion_results = JSONField(default=list, blank=True, verbose_name='断言结果列表')
    assertions_passed = models.IntegerField(default=0, verbose_name='断言通过数')
    assertions_failed = models.IntegerField(default=0, verbose_name='断言失败数')

    # ---- 数据提取结果（串联执行预留）----
    extraction_results = JSONField(default=dict, blank=True, verbose_name='数据提取结果')
    extracted_variables = JSONField(default=dict, blank=True, verbose_name='提取的变量')

    # ---- 环境信息 ----
    environment = models.ForeignKey(
        'ApiTestEnvironment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='http_records',
        verbose_name='执行环境'
    )
    environment_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='环境名称'
    )

    # ---- 执行者信息 ----
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='http_executions',
        verbose_name='执行者'
    )
    execution_source = models.CharField(
        max_length=20,
        choices=[
            ('MANUAL', '手动执行'),
            ('BATCH', '批量执行'),
            ('SCHEDULED', '定时执行'),
            ('API', 'API触发'),
        ],
        default='MANUAL',
        verbose_name='执行来源'
    )

    is_favorite = models.BooleanField(default=False, verbose_name='是否收藏')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'api_http_execution_records'
        verbose_name = 'HTTP接口执行记录'
        verbose_name_plural = 'HTTP接口执行记录'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['test_case', 'created_time'], name='record_case_time_idx'),
            models.Index(fields=['execution', 'created_time'], name='record_exec_time_idx'),
            models.Index(fields=['project', 'created_time'], name='record_project_time_idx'),
            models.Index(fields=['status', 'created_time'], name='record_status_time_idx'),
            models.Index(fields=['environment', 'created_time'], name='record_env_time_idx'),
            models.Index(fields=['is_favorite', 'created_time'], name='record_favorite_time_idx'),
            models.Index(fields=['executed_by', 'created_time'], name='record_user_time_idx'),
        ]

    def __str__(self):
        return f"{self.request_method} {self.request_url} - {self.status}"