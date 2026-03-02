"""
BrowserUse 服务模块

封装 browser_use Agent，提供统一的 UI 自动化执行接口。
通过自然语言描述的测试任务驱动浏览器执行操作。

注意: 本模块依赖 browser_use 和 langchain_openai 包，
如果未安装则 BROWSER_USE_AVAILABLE 标志为 False，
创建 BrowserUseService 实例时会抛出 RuntimeError。
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional

# 尝试导入 browser_use 相关依赖，导入失败时记录错误信息
BROWSER_USE_AVAILABLE = True
try:
    from browser_use import Agent, BrowserConfig
    from browser_use.browser.browser import Browser
    from browser_use.controller.service import Controller
    from langchain_openai import ChatOpenAI
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    IMPORT_ERROR = str(e)


class BrowserUseService:
    """
    BrowserUse 服务类。

    封装 browser_use Agent，执行自然语言描述的 UI 测试任务。
    支持异步执行和同步执行两种模式。

    生命周期:
        1. __init__: 配置任务和浏览器参数
        2. run / run_sync: 初始化浏览器和 Agent，执行任务
        3. cleanup: 关闭浏览器释放资源（run 方法会自动调用）

    Attributes:
        task: 自然语言测试任务描述
        browser_mode: 浏览器模式（headless/headed）
        history: 执行步骤历史记录
        screenshots: 截图数据列表
    """

    def __init__(
        self,
        task: str,
        browser_mode: str = 'headless',
        screenshot_callback: Optional[Callable] = None,
        step_callback: Optional[Callable] = None,
    ):
        """
        初始化 BrowserUse 服务。

        Args:
            task: 自然语言描述的测试任务
            browser_mode: 浏览器模式（'headless' 或 'headed'）
            screenshot_callback: 截图回调函数，签名: async (data, description) -> None
            step_callback: 步骤回调函数，签名: async (step_info) -> None

        Raises:
            RuntimeError: browser_use 模块未安装或导入失败
            ValueError: OPENAI_API_KEY 环境变量未设置
        """
        if not BROWSER_USE_AVAILABLE:
            raise RuntimeError(
                f"browser_use 模块未安装或导入失败: {IMPORT_ERROR}\n"
                "请确保已安装 browser_use 及其依赖。"
            )

        self.task = task
        self.browser_mode = browser_mode
        self.screenshot_callback = screenshot_callback
        self.step_callback = step_callback

        # 运行时状态
        self.agent = None
        self.browser = None
        self.controller = None
        self.history = []
        self.screenshots = []

        # OpenAI 配置
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_base = os.environ.get('OPENAI_API_BASE_URL')

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

    async def _initialize_browser(self) -> None:
        """初始化浏览器实例，根据 browser_mode 配置有头/无头模式。"""
        try:
            browser_config = BrowserConfig(
                headless=(self.browser_mode == 'headless'),
                disable_security=True,
            )
            self.browser = Browser(config=browser_config)
            await self.browser.start()
            self.controller = Controller()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {str(e)}")

    async def _initialize_agent(self) -> None:
        """初始化 browser_use Agent，配置 LLM 模型和控制器。"""
        try:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self.api_key,
                base_url=self.api_base,
                temperature=0.0,
            )
            self.agent = Agent(
                task=self.task,
                llm=llm,
                browser=self.browser,
                controller=self.controller,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize agent: {str(e)}")

    def _on_step(self, step: Dict[str, Any]) -> None:
        """步骤回调处理器，记录步骤到历史并触发外部回调。"""
        self.history.append(step)

        if self.step_callback:
            try:
                asyncio.create_task(self.step_callback(step))
            except Exception as e:
                print(f"Step callback error: {e}")

    async def _capture_screenshot(self, description: str = "") -> str:
        """
        捕获当前页面截图。

        Args:
            description: 截图描述（对应的操作步骤说明）

        Returns:
            截图数据的 base64 编码字符串（当前为占位实现，返回空字符串）
        """
        try:
            if self.browser:
                # TODO: 接入 browser_use 的截图 API，当前为占位实现
                screenshot_data = ""

                if self.screenshot_callback:
                    await self.screenshot_callback(screenshot_data, description)

                self.screenshots.append({
                    'description': description,
                    'data': screenshot_data,
                    'timestamp': datetime.now().isoformat(),
                })

                return screenshot_data
        except Exception as e:
            print(f"Screenshot capture error: {e}")

        return ""

    async def run(self) -> Dict[str, Any]:
        """
        异步执行测试任务。

        完整流程: 初始化浏览器 -> 初始化 Agent -> 执行任务 -> 清理资源。

        Returns:
            执行结果字典，包含 success、history、screenshots 等字段
        """
        try:
            await self._initialize_browser()
            await self._initialize_agent()

            result = await self.agent.run()

            return {
                'success': True,
                'history': self.history,
                'screenshots': self.screenshots,
                'result': result,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'history': self.history,
                'screenshots': self.screenshots,
            }
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """关闭浏览器，释放资源。"""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def run_sync(self) -> Dict[str, Any]:
        """
        同步执行测试任务（在新的事件循环中运行异步方法）。

        Returns:
            执行结果字典
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.run())
        finally:
            loop.close()


def create_browser_use_service(
    task: str,
    browser_mode: str = 'headless',
    screenshot_callback: Optional[Callable] = None,
    step_callback: Optional[Callable] = None,
) -> BrowserUseService:
    """
    创建 BrowserUseService 实例的工厂函数。

    提供简洁的创建入口，参数含义同 BrowserUseService.__init__。
    """
    return BrowserUseService(
        task=task,
        browser_mode=browser_mode,
        screenshot_callback=screenshot_callback,
        step_callback=step_callback,
    )
