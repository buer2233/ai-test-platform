"""
api_automation/admin.py

管理员界面配置
"""
from django.contrib import admin
from .models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
    ApiTestExecution, ApiTestReport, ApiTestResult, ApiDataDriver
)


@admin.register(ApiProject)
class ApiProjectAdmin(admin.ModelAdmin):
    """项目管理"""
    list_display = ['name', 'owner', 'is_active', 'created_time', 'updated_time']
    list_filter = ['is_active', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        # 超级用户可以看到所有项目，其他用户只能看到自己的项目
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(ApiCollection)
class ApiCollectionAdmin(admin.ModelAdmin):
    """集合管理"""
    list_display = ['name', 'project', 'created_time', 'updated_time']
    list_filter = ['project', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__owner=request.user)


@admin.register(ApiTestCase)
class ApiTestCaseAdmin(admin.ModelAdmin):
    """测试用例管理"""
    list_display = ['name', 'project', 'collection', 'method', 'url', 'created_by', 'created_time']
    list_filter = ['project', 'collection', 'method', 'created_time']
    search_fields = ['name', 'description', 'url']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__owner=request.user)

    def get_form(self, request, obj=None, **kwargs):
        # 在表单中限制项目的选择范围
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['project'].queryset = ApiProject.objects.filter(owner=request.user)
        return form


@admin.register(ApiTestEnvironment)
class ApiTestEnvironmentAdmin(admin.ModelAdmin):
    """测试环境管理"""
    list_display = ['name', 'project', 'base_url', 'is_default', 'is_active', 'created_time']
    list_filter = ['project', 'is_default', 'is_active', 'created_time']
    search_fields = ['name', 'description', 'base_url']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)


@admin.register(ApiTestExecution)
class ApiTestExecutionAdmin(admin.ModelAdmin):
    """测试执行管理"""
    list_display = ['name', 'project', 'environment', 'status', 'total_count', 'passed_count', 'failed_count', 'created_by', 'start_time']
    list_filter = ['project', 'environment', 'status', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time', 'start_time', 'end_time', 'duration']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)


@admin.register(ApiTestReport)
class ApiTestReportAdmin(admin.ModelAdmin):
    """测试报告管理"""
    list_display = ['name', 'execution', 'created_time']
    list_filter = ['created_time']
    search_fields = ['name', 'execution__name']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(execution__project__owner=request.user)


@admin.register(ApiTestResult)
class ApiTestResultAdmin(admin.ModelAdmin):
    """测试结果管理"""
    list_display = ['test_case', 'execution', 'status', 'response_status', 'response_time', 'start_time']
    list_filter = ['status', 'response_status', 'execution', 'test_case__project']
    search_fields = ['test_case__name', 'execution__name']
    readonly_fields = ['start_time', 'end_time', 'duration']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(execution__project__owner=request.user)


@admin.register(ApiDataDriver)
class ApiDataDriverAdmin(admin.ModelAdmin):
    """数据驱动管理"""
    list_display = ['name', 'project', 'test_case', 'data_type', 'is_active', 'created_time']
    list_filter = ['project', 'test_case', 'data_type', 'is_active', 'created_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(is_deleted=False)
        return qs.filter(project__owner=request.user, is_deleted=False)