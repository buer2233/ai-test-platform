"""
检查仪表盘数据脚本
"""
import os
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api_automation.models import ApiTestResult, ApiTestExecution, ApiProject, ApiTestCase
from django.contrib.auth.models import User

print("=" * 60)
print("仪表盘数据检查")
print("=" * 60)

# 检查用户
admin_user = User.objects.filter(username='admin').first()
print(f"\n管理员用户: {admin_user}")

# 检查项目
projects = ApiProject.objects.filter(is_deleted=False)
print(f"\n项目总数: {projects.count()}")
for p in projects:
    owner_name = p.owner.username if p.owner else 'None'
    print(f"  - ID={p.id}, Name={p.name}, Owner={owner_name}")

# 检查测试执行
executions = ApiTestExecution.objects.all()
print(f"\n测试执行记录总数: {executions.count()}")
for e in executions:
    print(f"  - ID={e.id}, 项目={e.project.name if e.project else 'None'}, 状态={e.status}")

# 检查测试结果
results = ApiTestResult.objects.all()
print(f"\n测试结果总数: {results.count()}")
for r in results:
    has_execution = r.execution is not None
    has_test_case = r.test_case is not None
    execution_project = r.execution.project.name if r.execution and r.execution.project else 'None'
    test_case_name = r.test_case.name if r.test_case else 'None'
    print(f"  - ID={r.id}, status={r.status}, 有执行记录={has_execution}, 有测试用例={has_test_case}")
    print(f"    执行项目={execution_project}, 测试用例={test_case_name}")

# 检查管理员能访问的结果
admin_projects = ApiProject.objects.filter(owner=admin_user, is_deleted=False)
print(f"\n管理员可访问项目数: {admin_projects.count()}")
admin_project_ids = list(admin_projects.values_list('id', flat=True))
print(f"管理员项目ID列表: {admin_project_ids}")

accessible_results = ApiTestResult.objects.filter(execution__project__in=admin_project_ids)
print(f"\n管理员可访问的测试结果数: {accessible_results.count()}")
for r in accessible_results:
    print(f"  - ID={r.id}, status={r.status}, execution_id={r.execution_id}, project={r.execution.project.name if r.execution and r.execution.project else 'None'}")

print("\n" + "=" * 60)
