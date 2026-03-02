"""
数据清理服务

使用Celery定时任务清理过期的测试数据，防止数据库无限增长。

清理范围：
1. ApiTestExecution - 测试执行记录
2. ApiTestResult - 测试结果记录
3. ApiHttpExecutionRecord - HTTP请求执行记录

支持三种清理维度：
- 全局清理：清理所有7天前的数据
- 按项目清理：清理指定项目的过期数据
- 按环境清理：清理指定环境的过期数据

建议配置 Celery Beat 定时任务，在每天凌晨低峰期执行。
"""

import logging
from datetime import timedelta

from django.celery import shared_task
from django.utils import timezone

from api_automation.models import (
    ApiHttpExecutionRecord,
    ApiTestExecution,
    ApiTestResult,
)

logger = logging.getLogger(__name__)

# 默认数据保留天数
DEFAULT_RETENTION_DAYS = 7


@shared_task
def cleanup_old_test_data():
    """
    全局定时清理任务：删除7天前的所有测试数据

    清理顺序（先子表后主表，避免外键约束冲突）：
    1. ApiTestResult（测试结果）
    2. ApiHttpExecutionRecord（HTTP请求记录）
    3. ApiTestExecution（执行记录）

    建议配置示例:
        CELERYBEAT_SCHEDULE = {
            'cleanup-old-test-data': {
                'task': 'api_automation.services.data_cleanup_service.cleanup_old_test_data',
                'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
            },
        }

    Returns:
        清理结果统计字典
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=DEFAULT_RETENTION_DAYS)

        logger.info(f"开始清理 {cutoff_date} 之前的测试数据")

        # 清理前统计
        stats_before = {
            'executions': ApiTestExecution.objects.filter(
                created_time__lt=cutoff_date
            ).count(),
            'results': ApiTestResult.objects.filter(
                created_time__lt=cutoff_date
            ).count(),
            'http_records': ApiHttpExecutionRecord.objects.filter(
                created_time__lt=cutoff_date
            ).count(),
        }

        logger.info(
            f"清理前统计: Executions={stats_before['executions']}, "
            f"Results={stats_before['results']}, "
            f"HttpRecords={stats_before['http_records']}"
        )

        # 按顺序删除：先子表后主表
        results_deleted, _ = ApiTestResult.objects.filter(
            created_time__lt=cutoff_date
        ).delete()

        http_records_deleted, _ = ApiHttpExecutionRecord.objects.filter(
            created_time__lt=cutoff_date
        ).delete()

        executions_deleted, _ = ApiTestExecution.objects.filter(
            created_time__lt=cutoff_date
        ).delete()

        logger.info(
            f"清理完成: 删除了 {executions_deleted} 条执行记录, "
            f"{results_deleted} 条测试结果, "
            f"{http_records_deleted} 条HTTP记录"
        )

        return {
            'status': 'success',
            'executions_deleted': executions_deleted,
            'results_deleted': results_deleted,
            'http_records_deleted': http_records_deleted,
            'cleanup_date': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

    except Exception as e:
        logger.error(f"清理数据时出错: {e}")
        return {'status': 'error', 'error': str(e)}


def _cleanup_by_execution_ids(execution_ids: list) -> tuple:
    """
    根据执行记录ID列表清理关联的子数据

    这是 cleanup_by_project 和 cleanup_by_environment 的共用逻辑。

    Args:
        execution_ids: 执行记录ID列表

    Returns:
        (results_deleted, http_records_deleted) 元组
    """
    results_deleted = ApiTestResult.objects.filter(
        execution_id__in=execution_ids
    ).delete()[0]

    http_records_deleted = ApiHttpExecutionRecord.objects.filter(
        execution_id__in=execution_ids
    ).delete()[0]

    return results_deleted, http_records_deleted


@shared_task
def cleanup_by_project(project_id: int, days: int = DEFAULT_RETENTION_DAYS):
    """
    按项目清理指定天数前的测试数据

    先查找项目下的过期执行记录，再级联删除关联的结果和HTTP记录。

    Args:
        project_id: 项目ID
        days: 保留天数（默认7天）

    Returns:
        清理结果统计字典
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        logger.info(
            f"开始清理项目 {project_id} {days}天前的数据"
            f"（{cutoff_date}之前）"
        )

        executions = ApiTestExecution.objects.filter(
            project_id=project_id,
            created_time__lt=cutoff_date
        )

        execution_ids = list(executions.values_list('id', flat=True))
        results_deleted, http_records_deleted = _cleanup_by_execution_ids(
            execution_ids
        )
        executions_deleted = executions.delete()[0]

        logger.info(
            f"项目 {project_id} 清理完成: "
            f"删除了 {executions_deleted} 条执行记录"
        )

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
def cleanup_by_environment(
    environment_id: int,
    days: int = DEFAULT_RETENTION_DAYS
):
    """
    按环境清理指定天数前的测试数据

    先查找环境下的过期执行记录，再级联删除关联的结果和HTTP记录。

    Args:
        environment_id: 环境ID
        days: 保留天数（默认7天）

    Returns:
        清理结果统计字典
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        logger.info(
            f"开始清理环境 {environment_id} {days}天前的数据"
            f"（{cutoff_date}之前）"
        )

        executions = ApiTestExecution.objects.filter(
            environment_id=environment_id,
            created_time__lt=cutoff_date
        )

        execution_ids = list(executions.values_list('id', flat=True))
        results_deleted, http_records_deleted = _cleanup_by_execution_ids(
            execution_ids
        )
        executions_deleted = executions.delete()[0]

        logger.info(
            f"环境 {environment_id} 清理完成: "
            f"删除了 {executions_deleted} 条执行记录"
        )

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
    获取数据清理统计信息

    统计当前数据库中各类型记录的总量和7天前的过期数量，
    并根据平均大小估算清理后可释放的空间。

    Returns:
        包含总量、过期量、估算可释放空间的统计字典
    """
    cutoff_date = timezone.now() - timedelta(days=DEFAULT_RETENTION_DAYS)

    total_executions = ApiTestExecution.objects.count()
    total_results = ApiTestResult.objects.count()
    total_http_records = ApiHttpExecutionRecord.objects.count()

    old_executions = ApiTestExecution.objects.filter(
        created_time__lt=cutoff_date
    ).count()
    old_results = ApiTestResult.objects.filter(
        created_time__lt=cutoff_date
    ).count()
    old_http_records = ApiHttpExecutionRecord.objects.filter(
        created_time__lt=cutoff_date
    ).count()

    # 按各记录类型的平均大小粗略估算可释放空间
    AVG_EXECUTION_SIZE = 1024   # 约1KB/条
    AVG_RESULT_SIZE = 2048      # 约2KB/条
    AVG_HTTP_RECORD_SIZE = 4096 # 约4KB/条

    estimated_space_saved = (
        old_executions * AVG_EXECUTION_SIZE
        + old_results * AVG_RESULT_SIZE
        + old_http_records * AVG_HTTP_RECORD_SIZE
    )

    return {
        'total_executions': total_executions,
        'total_results': total_results,
        'total_http_records': total_http_records,
        'old_executions': old_executions,
        'old_results': old_results,
        'old_http_records': old_http_records,
        'estimated_space_saved': estimated_space_saved,
        'estimated_space_saved_mb': round(
            estimated_space_saved / (1024 * 1024), 2
        ),
        'cleanup_date': cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),
    }
