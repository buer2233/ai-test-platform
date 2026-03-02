"""
api_automation/apps.py

API自动化测试模块的应用配置。
定义模块名称、自增主键类型等基本信息。
"""
from django.apps import AppConfig


class ApiAutomationConfig(AppConfig):
    """API自动化测试应用配置类，由 Django 自动加载。"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_automation'
    verbose_name = '接口自动化测试'