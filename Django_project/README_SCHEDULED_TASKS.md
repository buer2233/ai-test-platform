# 定时任务配置指南

## 自动清理执行记录

项目中已创建管理命令 `cleanup_old_records`，用于自动删除7天前的HTTP执行记录。

## 使用方法

### 手动执行

```bash
# 删除7天前的记录
python manage.py cleanup_old_records

# 删除30天前的记录
python manage.py cleanup_old_records --days 30

# 预览将要删除的记录（不实际删除）
python manage.py cleanup_old_records --dry-run
```

---

## 配置自动执行

### Linux/Mac (使用 cron)

1. 编辑 crontab:
   ```bash
   crontab -e
   ```

2. 添加以下行（每天凌晨0点执行）:
   ```bash
   0 0 * * * cd /path/to/Django_project && /path/to/python/bin/python manage.py cleanup_old_records >> /tmp/cleanup_old_records.log 2>&1
   ```

### Windows (使用计划任务)

1. 打开"任务计划程序"（Task Scheduler）

2. 创建基本任务:
   - 名称: `清理HTTP执行记录`
   - 触发器: 每天 00:00
   - 操作: 启动程序
   - 程序/脚本: `D:\Python\python.exe`
   - 添加参数: `D:\AI\AI-test-project\Django_project\manage.py cleanup_old_records`
   - 起始于: `D:\AI\AI-test-project\Django_project`

### Windows (使用批处理文件)

创建批处理文件 `cleanup_records.bat`:
```batch
@echo off
cd /d D:\AI\AI-test-project\Django_project
D:\Python\python.exe manage.py cleanup_old_records
```

然后在计划任务中设置运行此批处理文件。

---

## 使用 Celery Beat (推荐用于生产环境)

### 安装依赖

```bash
pip install celery
pip install django-celery-beat
```

### 配置 settings.py

```python
INSTALLED_APPS = [
    ...
    'django_celery_beat',
]

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-execution-records': {
        'task': 'api_automation.tasks.cleanup_old_records',
        'schedule': crontab(hour=0, minute=0),  # 每天凌晨0点
    },
}
```

### 创建 tasks.py

在 `api_automation/` 目录下创建 `tasks.py`:
```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from api_automation.models import ApiHttpExecutionRecord

@shared_task
def cleanup_old_records(days=7):
    cutoff_date = timezone.now() - timedelta(days=days)
    old_records = ApiHttpExecutionRecord.objects.filter(
        created_time__lt=cutoff_date
    )
    count, _ = old_records.delete()
    return count
```

### 启动 Celery Worker 和 Beat

```bash
# 启动 Celery Worker
celery -A config worker -l info

# 启动 Celery Beat（调度器）
celery -A config beat -l info
```
