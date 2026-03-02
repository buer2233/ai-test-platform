"""
UI 自动化测试服务层

提供核心业务服务，包括:
    - BrowserUse Agent 封装（直接调用模式）
    - CLI 子进程执行服务（通过 subprocess 调用 run_aiTest.py）
    - 测试执行编排服务
    - WebSocket 实时进度推送
    - HTML 测试报告生成
"""

from .browser_use_service import (
    BrowserUseService,
    create_browser_use_service,
)
from .cli_test_executor_service import (
    CliTestExecutorService,
    execute_test_case_cli,
)
from .report_generator import (
    ReportGenerator,
    generate_report,
    save_report,
)
from .test_executor_service import (
    TestExecutorService,
    execute_test_case,
    execute_test_case_async,
)
from .websocket_service import (
    WebSocketProgressService,
    UiAutomationConsumer,
    create_progress_callback,
    create_screenshot_callback,
)

__all__ = [
    # BrowserUse 直接调用服务
    'BrowserUseService',
    'create_browser_use_service',
    # CLI 子进程执行服务
    'CliTestExecutorService',
    'execute_test_case_cli',
    # 测试执行编排服务
    'TestExecutorService',
    'execute_test_case',
    'execute_test_case_async',
    # WebSocket 推送服务
    'WebSocketProgressService',
    'UiAutomationConsumer',
    'create_progress_callback',
    'create_screenshot_callback',
    # 报告生成服务
    'ReportGenerator',
    'generate_report',
    'save_report',
]
