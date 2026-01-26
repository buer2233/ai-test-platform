from django.apps import AppConfig


class ApiAutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_automation'
    verbose_name = '接口自动化测试'

    def ready(self):
        pass