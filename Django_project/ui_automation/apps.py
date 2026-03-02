"""
UI 自动化测试模块 - Django App 配置

定义模块的元信息和启动钩子。
"""

from django.apps import AppConfig


class UiAutomationConfig(AppConfig):
    """
    UI 自动化测试模块的 Django 应用配置。

    Attributes:
        default_auto_field: 主键字段类型，使用 BigAutoField 支持大量数据
        name: 应用名称，对应 Python 包名
        verbose_name: 后台管理界面中显示的可读名称
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ui_automation'
    verbose_name = 'UI自动化测试'

    def ready(self):
        """应用启动时的初始化钩子，用于注册信号处理器等。"""
