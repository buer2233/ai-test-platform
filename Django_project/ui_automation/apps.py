"""
Django App 配置
"""

from django.apps import AppConfig


class UiAutomationConfig(AppConfig):
    """UI自动化模块配置"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ui_automation'
    verbose_name = 'UI自动化测试'

    def ready(self):
        """应用启动时初始化"""
        # 导入信号处理器（如果需要）
        pass
