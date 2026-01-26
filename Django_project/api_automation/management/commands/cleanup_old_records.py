"""
Django 管理命令：自动清理过期的HTTP执行记录

用法：
    python manage.py cleanup_old_records

可通过 cron 或 Windows 计划任务设置每天凌晨0点执行
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api_automation.models import ApiHttpExecutionRecord


class Command(BaseCommand):
    help = '清理7天前的HTTP执行记录'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='删除多少天前的记录（默认：7天）',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将要删除的记录数量，不实际删除',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # 计算截止日期
        cutoff_date = timezone.now() - timedelta(days=days)

        # 查询需要删除的记录
        old_records = ApiHttpExecutionRecord.objects.filter(
            created_time__lt=cutoff_date
        )

        count = old_records.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f'没有找到{days}天前的执行记录'))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[Dry Run] 将要删除 {count} 条执行记录（{days}天前）')
            )
            return

        # 确认删除
        self.stdout.write(f'准备删除 {count} 条执行记录（{days}天前）...')

        # 批量删除
        deleted_count, _ = old_records.delete()

        self.stdout.write(
            self.style.SUCCESS(f'成功删除 {deleted_count} 条执行记录')
        )

        # 输出统计信息
        total_records = ApiHttpExecutionRecord.objects.count()
        self.stdout.write(f'当前剩余记录数: {total_records}')
