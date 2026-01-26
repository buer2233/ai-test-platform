"""
更新现有执行记录的报告路径

为有 final_result 的执行记录创建或更新 UiTestReport 记录
"""
import os
import django
import json

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ui_automation.models import UiTestExecution, UiTestReport


def update_report_paths():
    """为现有执行记录更新报告路径"""
    executions = UiTestExecution.objects.exclude(final_result='').filter(
        status__in=['passed', 'failed', 'error']
    )

    updated_count = 0
    created_count = 0

    for execution in executions:
        try:
            # 解析 final_result
            final_result = json.loads(execution.final_result) if execution.final_result else {}
            report_path = final_result.get('report_path')

            if report_path:
                # 检查是否已有报告
                report = execution.report if hasattr(execution, 'report') else None

                if not report:
                    # 创建新报告
                    report = UiTestReport.objects.create(
                        execution=execution,
                        total_steps=final_result.get('total_steps', 0),
                        completed_steps=final_result.get('total_steps', 0) if execution.status == 'passed' else 0,
                        failed_steps=0 if execution.status == 'passed' else final_result.get('total_steps', 0),
                        agent_history='',
                        json_report_path=report_path,
                        summary=f"测试{'成功' if execution.status == 'passed' else '失败'}",
                    )
                    created_count += 1
                    print(f"创建报告记录: 执行 #{execution.id} -> {report_path}")
                else:
                    # 更新现有报告
                    report.json_report_path = report_path
                    report.save()
                    updated_count += 1
                    print(f"更新报告记录: 执行 #{execution.id} -> {report_path}")
        except Exception as e:
            print(f"处理执行 #{execution.id} 时出错: {e}")

    print(f"\n完成: 创建 {created_count} 条, 更新 {updated_count} 条")


if __name__ == '__main__':
    update_report_paths()
