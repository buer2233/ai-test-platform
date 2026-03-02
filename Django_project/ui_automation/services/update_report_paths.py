"""
历史数据迁移脚本 - 更新报告路径

为已有 final_result 但缺少 UiTestReport 记录的执行记录
创建或更新对应的报告关联。

此脚本可独立运行:
    python manage.py shell < ui_automation/services/update_report_paths.py
    或
    python ui_automation/services/update_report_paths.py
"""

import json
import os

import django

# 设置 Django 环境（独立运行时需要）
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ui_automation.models import UiTestExecution, UiTestReport


def update_report_paths():
    """
    为已完成的执行记录补充报告路径。

    扫描所有状态为 passed/failed/error 且 final_result 非空的执行记录，
    从 final_result JSON 中提取 report_path，创建或更新对应的 UiTestReport。
    """
    executions = UiTestExecution.objects.exclude(final_result='').filter(
        status__in=['passed', 'failed', 'error']
    )

    updated_count = 0
    created_count = 0

    for execution in executions:
        try:
            final_result = json.loads(execution.final_result) if execution.final_result else {}
            report_path = final_result.get('report_path')

            if not report_path:
                continue

            # 检查是否已有关联报告
            existing_report = getattr(execution, 'report', None)

            if not existing_report:
                # 创建新报告记录
                total_steps = final_result.get('total_steps', 0)
                is_passed = execution.status == 'passed'

                UiTestReport.objects.create(
                    execution=execution,
                    total_steps=total_steps,
                    completed_steps=total_steps if is_passed else 0,
                    failed_steps=0 if is_passed else total_steps,
                    agent_history='',
                    json_report_path=report_path,
                    summary=f"测试{'成功' if is_passed else '失败'}",
                )
                created_count += 1
                print(f"创建报告记录: 执行 #{execution.id} -> {report_path}")
            else:
                # 更新已有报告的路径
                existing_report.json_report_path = report_path
                existing_report.save()
                updated_count += 1
                print(f"更新报告记录: 执行 #{execution.id} -> {report_path}")
        except Exception as e:
            print(f"处理执行 #{execution.id} 时出错: {e}")

    print(f"\n完成: 创建 {created_count} 条, 更新 {updated_count} 条")


if __name__ == '__main__':
    update_report_paths()
