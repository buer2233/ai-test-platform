"""
api_automation/admin.py

Django Admin 管理后台配置。
为 API 自动化测试模块的各数据模型注册管理界面，
支持列表展示、筛选、搜索和基于用户权限的数据隔离。

权限规则:
    - 超级用户可查看所有数据
    - 普通用户仅可查看自己所属项目的数据
    - 支持软删除的模型会自动过滤已删除记录
"""
from django.contrib import admin

from .models import (
    ApiCollection,
    ApiDataDriver,
    ApiProject,
    ApiTestCase,
    ApiTestEnvironment,
    ApiTestExecution,
    ApiTestReport,
    ApiTestResult,
)


# ---------------------------------------------------------------------------
# 通用辅助方法说明：
# 各 Admin 类中的 get_queryset 方法均实现了基于用户权限的数据隔离，
# 确保普通用户只能访问自己负责的项目数据。
# ---------------------------------------------------------------------------


@admin.register(ApiProject)
class ApiProjectAdmin(admin.ModelAdmin):
    """项目管理 -- 展示项目基本信息，支持按激活状态和创建时间筛选。"""

    list_display = ['name', 'owner', 'is_active', 'created_time', 'updated_time']
    list_filter = ['is_active', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """超级用户查看全部项目，普通用户仅查看自己的项目。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(ApiCollection)
class ApiCollectionAdmin(admin.ModelAdmin):
    """集合管理 -- 展示集合与所属项目的关联关系。"""

    list_display = ['name', 'project', 'created_time', 'updated_time']
    list_filter = ['project', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """按项目归属过滤集合数据。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__owner=request.user)


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    """测试用例管理 -- 展示用例的请求方法、URL 等关键信息。"""

    list_display = [
        'name', 'project', 'collection', 'method', 'url',
        'created_by', 'created_time'
    ]
    list_filter = ['project', 'collection', 'method', 'created_time']
    search_fields = ['name', 'description', 'url']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """按项目归属过滤测试用例。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__owner=request.user)

    def get_form(self, request, obj=None, **kwargs):
        """限制非超级用户的项目选择范围，仅显示自己负责的项目。"""
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['project'].queryset = ApiProject.objects.filter(
                owner=request.user
            )
        return form


@admin.register(ApiTestEnvironment)
class ApiTestEnvironmentAdmin(admin.ModelAdmin):
    """测试环境管理 -- 展示环境的 URL、默认/激活状态。"""

    list_display = [
        'name', 'project', 'base_url', 'is_default', 'is_active', 'created_time'
    ]
    list_filter = ['project', 'is_default', 'is_active', 'created_time']
    search_fields = ['name', 'description', 'base_url']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """过滤已软删除的环境记录，并按项目归属隔离数据。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)


@admin.register(ApiTestExecution)
class ApiTestExecutionAdmin(admin.ModelAdmin):
    """测试执行管理 -- 展示执行状态和用例通过/失败计数。"""

    list_display = [
        'name', 'project', 'environment', 'status',
        'total_count', 'passed_count', 'failed_count',
        'created_by', 'start_time'
    ]
    list_filter = ['project', 'environment', 'status', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time', 'start_time', 'end_time', 'duration']

    def get_queryset(self, request):
        """过滤已软删除的执行记录。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)


@admin.register(ApiTestReport)
class ApiTestReportAdmin(admin.ModelAdmin):
    """测试报告管理 -- 展示报告与执行记录的关联。"""

    list_display = ['name', 'execution', 'created_time']
    list_filter = ['created_time']
    search_fields = ['name', 'execution__name']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """按执行记录的项目归属过滤报告。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(execution__project__owner=request.user)


@admin.register(ApiTestResult)
class ApiTestResultAdmin(admin.ModelAdmin):
    """测试结果管理 -- 展示单个用例的执行状态和响应指标。"""

    list_display = [
        'test_case', 'execution', 'status', 'response_status',
        'response_time', 'start_time'
    ]
    list_filter = ['status', 'response_status', 'execution', 'test_case__project']
    search_fields = ['test_case__name', 'execution__name']
    readonly_fields = ['start_time', 'end_time', 'duration']

    def get_queryset(self, request):
        """按执行记录的项目归属过滤测试结果。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(execution__project__owner=request.user)


@admin.register(ApiDataDriver)
class ApiDataDriverAdmin(admin.ModelAdmin):
    """数据驱动管理 -- 展示数据源配置及其关联的测试用例。"""

    list_display = [
        'name', 'project', 'test_case', 'data_type', 'is_active', 'created_time'
    ]
    list_filter = ['project', 'test_case', 'data_type', 'is_active', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        """过滤已软删除的数据驱动配置。"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)