"""
UI 自动化测试模块 - 数据模型

定义 UI 自动化测试的核心数据结构，所有表使用 ui_ 前缀，与 api_automation 模块完全隔离。

模型清单:
    UiTestProject   - 测试项目，组织和管理测试用例的顶层容器
    UiTestCase      - 测试用例，使用自然语言描述的 UI 测试步骤
    UiTestExecution  - 执行记录，记录每次测试运行的状态和结果
    UiTestReport    - 测试报告，存储 Agent 执行历史和统计信息
    UiScreenshot    - 测试截图，存储执行过程中的截图文件
"""

from django.contrib.auth.models import User
from django.db import models


def get_report_upload_path(instance, filename):
    """
    生成报告文件的存储路径。

    路径格式: ui_reports/<项目ID>/<执行ID>/<文件名>

    Args:
        instance: UiTestReport 实例
        filename: 原始文件名
    """
    return f'ui_reports/{instance.execution.project.id}/{instance.execution.id}/{filename}'


def get_screenshot_upload_path(instance, filename):
    """
    生成截图文件的存储路径。

    路径格式: ui_screenshots/<项目ID>/<执行ID>/<文件名>

    Args:
        instance: UiScreenshot 实例
        filename: 原始文件名
    """
    return f'ui_screenshots/{instance.execution.project.id}/{instance.execution.id}/{filename}'


class UiTestProject(models.Model):
    """
    UI 测试项目模型。

    作为测试用例的顶层组织容器，一个项目包含多个测试用例。
    支持软删除，删除后不会从数据库中物理移除。

    关联关系:
        -> UiTestCase (一对多): 项目下的测试用例
        -> UiTestExecution (一对多): 项目下的执行记录
    """

    # ---- 基础信息 ----
    name = models.CharField(max_length=200, verbose_name='项目名称', help_text='项目名称')
    description = models.TextField(blank=True, verbose_name='项目描述', help_text='项目描述')

    # ---- 测试配置 ----
    base_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='基础URL',
        help_text='被测应用的基础URL，例如: https://www.example.com'
    )
    default_browser_mode = models.CharField(
        max_length=20,
        choices=[
            ('headless', '无头模式'),
            ('headed', '有头模式'),
        ],
        default='headless',
        verbose_name='默认浏览器模式',
        help_text='执行测试时的默认浏览器模式'
    )

    # ---- 元数据 ----
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ui_projects_created',
        verbose_name='创建人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # ---- 软删除 ----
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'ui_test_projects'
        verbose_name = 'UI测试项目'
        verbose_name_plural = 'UI测试项目'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """软删除：将 is_deleted 标记为 True，而非物理删除记录。"""
        self.is_deleted = True
        self.save()


class UiTestCase(models.Model):
    """
    UI 测试用例模型。

    使用自然语言描述的 UI 测试用例，由 browser_use Agent 执行。
    核心字段 natural_language_task 存储用户编写的自然语言测试步骤，
    AI 引擎会自动解析并执行这些步骤。

    关联关系:
        <- UiTestProject (多对一): 所属项目
        -> UiTestExecution (一对多): 用例的执行记录
    """

    # ---- 关联项目 ----
    project = models.ForeignKey(
        UiTestProject,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name='所属项目'
    )

    # ---- 基础信息 ----
    name = models.CharField(max_length=200, verbose_name='用例名称', help_text='测试用例名称')
    description = models.TextField(
        blank=True,
        verbose_name='用例描述',
        help_text='测试用例的详细描述'
    )

    # ---- 核心字段：自然语言任务描述（AI 引擎根据此内容自动执行操作） ----
    natural_language_task = models.TextField(
        verbose_name='自然语言任务描述',
        help_text='用自然语言描述测试任务，AI将自动理解并执行。例如: 打开首页，点击登录按钮，输入用户名和密码，验证登录成功'
    )

    # ---- 执行配置（用例级别，可覆盖项目默认值） ----
    browser_mode = models.CharField(
        max_length=20,
        choices=[
            ('headless', '无头模式'),
            ('headed', '有头模式'),
        ],
        default='headless',
        verbose_name='浏览器模式',
        help_text='执行此用例时的浏览器模式'
    )

    timeout = models.IntegerField(
        default=120,
        verbose_name='超时时间(秒)',
        help_text='单步操作的超时时间'
    )

    retry_count = models.IntegerField(
        default=0,
        verbose_name='重试次数',
        help_text='失败后的重试次数'
    )

    # ---- 预期结果 ----
    expected_result = models.TextField(
        blank=True,
        verbose_name='预期结果',
        help_text='测试的预期结果描述'
    )

    # ---- 标签（JSON 字符串存储，使用 TextField 兼容 SQLite） ----
    tags = models.TextField(
        default='[]',
        blank=True,
        verbose_name='标签',
        help_text='测试用例标签，用于分类管理'
    )

    # ---- 优先级 ----
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', '低'),
            ('medium', '中'),
            ('high', '高'),
            ('critical', '紧急'),
        ],
        default='medium',
        verbose_name='优先级'
    )

    # ---- 启用状态 ----
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')

    # ---- 元数据 ----
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # ---- 软删除 ----
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'ui_test_cases'
        verbose_name = 'UI测试用例'
        verbose_name_plural = 'UI测试用例'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['project']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_enabled']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        return f'{self.project.name} - {self.name}'

    def delete(self, using=None, keep_parents=False):
        """软删除：将 is_deleted 标记为 True，而非物理删除记录。"""
        self.is_deleted = True
        self.save()


class UiTestExecution(models.Model):
    """
    UI 测试执行记录模型。

    记录每次测试执行的详细信息，包括执行状态、时间、结果等。
    一个测试用例可以被执行多次，每次执行产生一条记录。

    状态流转:
        pending -> running -> passed / failed / error
        pending / running -> cancelled

    关联关系:
        <- UiTestProject (多对一): 所属项目
        <- UiTestCase (多对一): 关联的测试用例
        -> UiTestReport (一对一): 执行报告
        -> UiScreenshot (一对多): 执行截图
    """

    # ---- 关联项目和用例 ----
    project = models.ForeignKey(
        UiTestProject,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='所属项目'
    )
    test_case = models.ForeignKey(
        UiTestCase,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='测试用例'
    )

    # ---- 执行状态 ----
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待执行'),
            ('running', '执行中'),
            ('passed', '通过'),
            ('failed', '失败'),
            ('error', '错误'),
            ('cancelled', '已取消'),
        ],
        default='pending',
        verbose_name='执行状态'
    )

    # ---- 执行配置 ----
    browser_mode = models.CharField(
        max_length=20,
        choices=[
            ('headless', '无头模式'),
            ('headed', '有头模式'),
        ],
        default='headless',
        verbose_name='浏览器模式'
    )

    # ---- 时间信息 ----
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    duration_seconds = models.IntegerField(null=True, blank=True, verbose_name='执行时长(秒)')

    # ---- 执行结果 ----
    final_result = models.TextField(blank=True, verbose_name='最终结果')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # ---- 执行人 ----
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ui_executions',
        verbose_name='执行人'
    )

    # ---- 元数据 ----
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'ui_test_executions'
        verbose_name = 'UI测试执行'
        verbose_name_plural = 'UI测试执行'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['project']),
            models.Index(fields=['test_case']),
            models.Index(fields=['status']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        return f'{self.test_case.name} - {self.get_status_display()}'

    @property
    def duration_display(self):
        """将执行时长格式化为易读的中文字符串（如: '2分30秒'）。"""
        if self.duration_seconds is None:
            return '-'
        if self.duration_seconds < 60:
            return f'{self.duration_seconds}秒'
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f'{minutes}分{seconds}秒'


class UiTestReport(models.Model):
    """
    UI 测试报告模型。

    存储测试执行的详细报告，包括 Agent 执行历史、步骤统计、截图路径等。
    每个执行记录最多关联一份报告（OneToOne 关系）。

    关联关系:
        <- UiTestExecution (一对一): 关联的执行记录
    """

    # ---- 关联执行记录 ----
    execution = models.OneToOneField(
        UiTestExecution,
        on_delete=models.CASCADE,
        related_name='report',
        verbose_name='执行记录'
    )

    # ---- browser_use Agent 执行历史（JSON 字符串，使用 TextField 兼容 SQLite） ----
    agent_history = models.TextField(
        null=True,
        blank=True,
        verbose_name='Agent执行历史',
        help_text='browser_use Agent 的完整执行步骤历史'
    )

    # ---- 步骤统计 ----
    total_steps = models.IntegerField(default=0, verbose_name='总步骤数')
    completed_steps = models.IntegerField(default=0, verbose_name='已完成步骤数')
    failed_steps = models.IntegerField(default=0, verbose_name='失败步骤数')

    # ---- 截图文件路径列表（JSON 字符串，使用 TextField 兼容 SQLite） ----
    screenshot_paths = models.TextField(
        default='[]',
        blank=True,
        verbose_name='截图路径列表',
        help_text='执行过程中产生的截图文件路径'
    )

    # ---- 报告文件（HTML 格式） ----
    report_file = models.FileField(
        upload_to=get_report_upload_path,
        null=True,
        blank=True,
        verbose_name='报告文件',
        help_text='生成的HTML格式测试报告文件'
    )

    # ---- JSON 报告路径（browser-use 生成的原始 JSON 报告文件路径） ----
    json_report_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='JSON报告路径',
        help_text='browser-use Agent 生成的 JSON 格式执行报告文件路径'
    )

    # ---- 报告摘要 ----
    summary = models.TextField(blank=True, verbose_name='报告摘要')

    # ---- 元数据 ----
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ui_test_reports'
        verbose_name = 'UI测试报告'
        verbose_name_plural = 'UI测试报告'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['execution']),
        ]

    def __str__(self):
        return f'报告 - {self.execution.test_case.name}'


class UiScreenshot(models.Model):
    """
    UI 测试截图模型。

    存储测试执行过程中每个步骤的截图文件及其描述信息。

    关联关系:
        <- UiTestExecution (多对一): 关联的执行记录
    """

    # ---- 关联执行记录 ----
    execution = models.ForeignKey(
        UiTestExecution,
        on_delete=models.CASCADE,
        related_name='screenshots',
        verbose_name='执行记录'
    )

    # ---- 截图文件 ----
    image_file = models.ImageField(
        upload_to=get_screenshot_upload_path,
        verbose_name='截图文件'
    )

    # ---- 截图描述 ----
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='截图描述',
        help_text='截图对应的操作步骤描述'
    )

    # ---- 步骤序号 ----
    step_number = models.IntegerField(verbose_name='步骤序号')

    # ---- 元数据 ----
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'ui_screenshots'
        verbose_name = 'UI测试截图'
        verbose_name_plural = 'UI测试截图'
        ordering = ['execution', 'step_number']
        indexes = [
            models.Index(fields=['execution', 'step_number']),
        ]

    def __str__(self):
        return f'{self.execution.test_case.name} - 步骤{self.step_number}'
