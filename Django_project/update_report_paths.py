"""
更新现有执行记录的报告路径

为有 final_result 的执行记录创建或更新 UiTestReport 记录
"""
import os
import sys
import django

# 添加项目路径
sys.path.insert(0, 'D:/AI/AI-test-project/Django_project')

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ui_automation.models import UiTestExecution, UiTestReport
import json


def update_report_paths():
    """为现有执行记录更新报告路径"""
    print("开始更新执行记录的报告路径...")

    # 获取所有有 final_result 的执行记录
    executions = UiTestExecution.objects.exclude(final_result='').filter(
        status__in=['passed', 'failed']
    )

    print(f"找到 {executions.count()} 条执行记录")

    updated_count = 0
    created_count = 0

    for execution in executions:
        try:
            # 解析 final_result
            final_result = json.loads(execution.final_result) if execution.final_result else {}
            report_path = final_result.get('report_path')

            print(f"\n执行记录 #{execution.id}:")
            print(f"  状态: {execution.status}")
            print(f"  报告路径: {report_path}")

            if report_path:
                # 检查是否已有报告
                try:
                    report = execution.report
                    print(f"  已有报告记录: #{report.id}")
                    # 更新现有报告
                    report.json_report_path = report_path
                    report.save()
                    updated_count += 1
                    print(f"  ✓ 已更新报告路径")
                except UiTestReport.DoesNotExist:
                    # 创建新报告
                    total_steps = final_result.get('total_steps', 0)
                    report = UiTestReport.objects.create(
                        execution=execution,
                        total_steps=total_steps,
                        completed_steps=total_steps if execution.status == 'passed' else 0,
                        failed_steps=0 if execution.status == 'passed' else total_steps,
                        agent_history='',
                        json_report_path=report_path,
                        summary=f"测试{'成功' if execution.status == 'passed' else '失败'}",
                    )
                    created_count += 1
                    print(f"  ✓ 已创建报告记录: #{report.id}")
        except Exception as e:
            print(f"  ✗ 处理执行 #{execution.id} 时出错: {e}")

    print(f"\n完成: 创建 {created_count} 条报告, 更新 {updated_count} 条报告")


if __name__ == '__main__':
    update_report_paths()
