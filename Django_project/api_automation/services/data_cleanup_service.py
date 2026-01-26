"""
data_cleanup_service.py

数据清理服务，使用Celery定时任务清理7天前的测试数据。

功能：
1. 定时清理7天前的执行记录
2. 定时清理7天前的测试结果
3. 定时清理7天前的HTTP执行记录
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.celery import shared_task
from api_automation.models import (
    ApiTestExecution, ApiTestResult, ApiHttpExecutionRecord
)

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_test_data():
    """
    定时清理7天前的测试数据

    清理规则：
    - 保留最近7天的数据
    - 删除7天前的ApiTestExecution记录
    - 删除7天前的ApiTestResult记录
    - 删除7天前的ApiHttpExecutionRecord记录

    建议配置：
    CELERYBEAT_SCHEDULE = {
        'cleanup-old-test-data': {
            'task': 'api_automation.services.data_cleanup_service.cleanup_old_test_data',
            'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
        },
    }
    """
    try:
        # 计算7天前的日期
        seven_days_ago = timezone.now() - timedelta(days=7)

        logger.info(f"开始清理7天前的测试数据（{seven_days_ago}之前的数据）")

        # 统计清理前的数据量
        execution_count_before = ApiTestExecution.objects.filter(
            created_time__lt=seven_days_ago
        ).count()
        result_count_before = ApiTestResult.objects.filter(
            created_time__lt=seven_days_ago
        ).count()
        http_record_count_before = ApiHttpExecutionRecord.objects.filter(
            created_time__lt=seven_days_ago
        ).count()

        logger.info(f"清理前统计: Executions={execution_count_before}, "
                   f"Results={result_count_before}, HttpRecords={http_record_count_before}")

        # 清理ApiTestResult（先清理子表）
        results_deleted, _ = ApiTestResult.objects.filter(
            created_time__lt=seven_days_ago
        ).delete()

        # 清理ApiHttpExecutionRecord
        http_records_deleted, _ = ApiHttpExecutionRecord.objects.filter(
            created_time__lt=seven_days_ago
        ).delete()

        # 清理ApiTestExecution（最后清理主表）
        executions_deleted, _ = ApiTestExecution.objects.filter(
            created_time__lt=seven_days_ago
        ).delete()

        logger.info(f"清理完成: 删除了 {executions_deleted} 条执行记录, "
                   f"{results_deleted} 条测试结果, {http_records_deleted} 条HTTP记录")

        return {
            'status': 'success',
            'executions_deleted': executions_deleted,
            'results_deleted': results_deleted,
            'http_records_deleted': http_records_deleted,
            'cleanup_date': seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),
        }

    except Exception as e:
        logger.error(f"清理数据时出错: {e}")
        return {
            'status': 'error',
            'error': str(e),
        }


@shared_task
def cleanup_by_project(project_id: int, days: int = 7):
    """
    按项目清理指定天数前的测试数据

    Args:
        project_id: 项目ID
        days: 清理多少天前的数据（默认7天）

    Returns:
        清理结果统计
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        logger.info(f"开始清理项目 {project_id} {days}天前的数据（{cutoff_date}之前）")

        # 获取该项目的执行记录
        executions = ApiTestExecution.objects.filter(
            project_id=project_id,
            created_time__lt=cutoff_date
        )

        execution_ids = list(executions.values_list('id', flat=True))

        # 清理关联的测试结果
        results_deleted = ApiTestResult.objects.filter(
            execution_id__in=execution_ids
        ).delete()[0]

        # 清理关联的HTTP记录
        http_records_deleted = ApiHttpExecutionRecord.objects.filter(
            execution_id__in=execution_ids
        ).delete()[0]

        # 清理执行记录
        executions_deleted = executions.delete()[0]

        logger.info(f"项目 {project_id} 清理完成: 删除了 {executions_deleted} 条执行记录")

        return {
            'status': 'success',
            'project_id': project_id,
            'executions_deleted': executions_deleted,
            'results_deleted': results_deleted,
            'http_records_deleted': http_records_deleted,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    except Exception as e:
        logger.error(f"按项目清理数据时出错: {e}")
        return {
            'status': 'error',
            'project_id': project_id,
            'error': str(e),
        }


@shared_task
def cleanup_by_environment(environment_id: int, days: int = 7):
    """
    按环境清理指定天数前的测试数据

    Args:
        environment_id: 环境ID
        days: 清理多少天前的数据（默认7天）

    Returns:
        清理结果统计
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        logger.info(f"开始清理环境 {environment_id} {days}天前的数据（{cutoff_date}之前）")

        # 获取该环境的执行记录
        executions = ApiTestExecution.objects.filter(
            environment_id=environment_id,
            created_time__lt=cutoff_date
        )

        execution_ids = list(executions.values_list('id', flat=True))

        # 清理关联的测试结果
        results_deleted = ApiTestResult.objects.filter(
            execution_id__in=execution_ids
        ).delete()[0]

        # 清理关联的HTTP记录
        http_records_deleted = ApiHttpExecutionRecord.objects.filter(
            execution_id__in=execution_ids
        ).delete()[0]

        # 清理执行记录
        executions_deleted = executions.delete()[0]

        logger.info(f"环境 {environment_id} 清理完成: 删除了 {executions_deleted} 条执行记录")

        return {
            'status': 'success',
            'environment_id': environment_id,
            'executions_deleted': executions_deleted,
            'results_deleted': results_deleted,
            'http_records_deleted': http_records_deleted,
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    except Exception as e:
        logger.error(f"按环境清理数据时出错: {e}")
        return {
            'status': 'error',
            'environment_id': environment_id,
            'error': str(e),
        }


def get_cleanup_stats() -> dict:
    """
    获取清理统计信息

    Returns:
        包含以下信息的字典：
        - total_executions: 总执行记录数
        - total_results: 总测试结果数
        - total_http_records: 总HTTP记录数
        - old_executions: 7天前的执行记录数
        - old_results: 7天前的测试结果数
        - old_http_records: 7天前的HTTP记录数
        - estimated_space_saved: 估计节省的空间（字节）
    """
    seven_days_ago = timezone.now() - timedelta(days=7)

    total_executions = ApiTestExecution.objects.count()
    total_results = ApiTestResult.objects.count()
    total_http_records = ApiHttpExecutionRecord.objects.count()

    old_executions = ApiTestExecution.objects.filter(
        created_time__lt=seven_days_ago
    ).count()
    old_results = ApiTestResult.objects.filter(
        created_time__lt=seven_days_ago
    ).count()
    old_http_records = ApiHttpExecutionRecord.objects.filter(
        created_time__lt=seven_days_ago
    ).count()

    # 估算空间（粗略估计）
    avg_execution_size = 1024  # 1KB
    avg_result_size = 2048  # 2KB
    avg_http_record_size = 4096  # 4KB

    estimated_space_saved = (
        old_executions * avg_execution_size +
        old_results * avg_result_size +
        old_http_records * avg_http_record_size
    )

    return {
        'total_executions': total_executions,
        'total_results': total_results,
        'total_http_records': total_http_records,
        'old_executions': old_executions,
        'old_results': old_results,
        'old_http_records': old_http_records,
        'estimated_space_saved': estimated_space_saved,
        'estimated_space_saved_mb': round(estimated_space_saved / (1024 * 1024), 2),
        'cleanup_date': seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),
    }
