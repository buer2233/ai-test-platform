"""
UI自动化测试服务模块

提供 BrowserUse 集成、测试执行、WebSocket 推送和报告生成服务。
"""

from .browser_use_service import (
    BrowserUseService,
    create_browser_use_service,
)

from .test_executor_service import (
    TestExecutorService,
    execute_test_case,
    execute_test_case_async,
)

from .cli_test_executor_service import (
    CliTestExecutorService,
    execute_test_case_cli,
)

from .websocket_service import (
    WebSocketProgressService,
    UiAutomationConsumer,
    create_progress_callback,
    create_screenshot_callback,
)

from .report_generator import (
    ReportGenerator,
    generate_report,
    save_report,
)

__all__ = [
    # BrowserUse Service
    'BrowserUseService',
    'create_browser_use_service',
    # Test Executor Service
    'TestExecutorService',
    'execute_test_case',
    'execute_test_case_async',
    # CLI Test Executor Service (NEW)
    'CliTestExecutorService',
    'execute_test_case_cli',
    # WebSocket Service
    'WebSocketProgressService',
    'UiAutomationConsumer',
    'create_progress_callback',
    'create_screenshot_callback',
    # Report Generator
    'ReportGenerator',
    'generate_report',
    'save_report',
]
