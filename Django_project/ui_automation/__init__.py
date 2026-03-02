"""
UI 自动化测试模块

AI 驱动的 UI 自动化测试模块，基于 browser_use 框架实现自然语言驱动的浏览器自动化测试。

模块功能:
    - 自然语言测试用例定义与管理
    - browser_use Agent 执行引擎（支持 CLI 和直接调用两种模式）
    - WebSocket 实时执行进度推送
    - HTML / JSON 格式测试报告生成

目录结构:
    models.py           - 数据模型（项目、用例、执行记录、报告、截图）
    serializers.py      - DRF 序列化器
    views.py            - API 视图集
    urls.py             - URL 路由配置
    routing.py          - WebSocket 路由配置
    services/           - 业务服务层
        browser_use_service.py          - BrowserUse Agent 封装
        cli_test_executor_service.py    - CLI 子进程执行服务
        test_executor_service.py        - 直接调用执行服务
        websocket_service.py            - WebSocket 推送服务
        report_generator.py             - HTML 报告生成器
        update_report_paths.py          - 历史数据迁移脚本
"""

default_app_config = 'ui_automation.apps.UiAutomationConfig'
