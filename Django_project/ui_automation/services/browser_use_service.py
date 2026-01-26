"""
BrowserUse 服务模块

封装 browser_use Agent，提供统一的UI自动化执行接口。
"""

import asyncio
import os
import base64
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

# 尝试导入 browser_use，如果失败则设置标志
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
    BrowserUse 服务类

    封装 browser_use Agent，执行自然语言描述的UI测试任务。
    """

    def __init__(
        self,
        task: str,
        browser_mode: str = 'headless',
        screenshot_callback: Optional[Callable] = None,
        step_callback: Optional[Callable] = None,
    ):
        """
        初始化 BrowserUse 服务

        Args:
            task: 自然语言描述的测试任务
            browser_mode: 浏览器模式 ('headless' 或 'headed')
            screenshot_callback: 截图回调函数
            step_callback: 步骤回调函数
        """
        # 检查 browser_use 是否可用
        if not BROWSER_USE_AVAILABLE:
            raise RuntimeError(
                f"browser_use 模块未安装或导入失败: {IMPORT_ERROR}\n"
                "请确保已安装 browser_use 及其依赖。"
            )

        self.task = task
        self.browser_mode = browser_mode
        self.screenshot_callback = screenshot_callback
        self.step_callback = step_callback
        self.agent = None
        self.browser = None
        self.controller = None
        self.history = []
        self.screenshots = []

        # 从环境变量获取 OpenAI 配置
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.api_base = os.environ.get('OPENAI_API_BASE_URL')

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

    async def _initialize_browser(self) -> None:
        """初始化浏览器"""
        try:
            # 配置浏览器
            browser_config = BrowserConfig(
                headless=(self.browser_mode == 'headless'),
                disable_security=True,
            )

            self.browser = Browser(config=browser_config)
            await self.browser.start()

            # 创建 Controller
            self.controller = Controller()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {str(e)}")

    async def _initialize_agent(self) -> None:
        """初始化 Agent"""
        try:
            # 配置 LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self.api_key,
                base_url=self.api_base,
                temperature=0.0,
            )

            # 创建 Agent
            self.agent = Agent(
                task=self.task,
                llm=llm,
                browser=self.browser,
                controller=self.controller,
            )

        except Exception as e:
            raise RuntimeError(f"Failed to initialize agent: {str(e)}")

    def _on_step(self, step: Dict[str, Any]) -> None:
        """
        步骤回调

        Args:
            step: 步骤信息字典
        """
        self.history.append(step)

        if self.step_callback:
            try:
                asyncio.create_task(self.step_callback(step))
            except Exception as e:
                print(f"Step callback error: {e}")

    async def _capture_screenshot(self, description: str = "") -> str:
        """
        捕获截图

        Args:
            description: 截图描述

        Returns:
            截图文件的base64编码
        """
        try:
            if self.browser:
                # 这里应该使用 browser_use 的截图功能
                # 暂时返回空字符串，具体实现需要根据 browser_use 的 API 调整
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
        执行测试任务

        Returns:
            执行结果字典，包含历史记录和截图
        """
        try:
            # 初始化浏览器和 Agent
            await self._initialize_browser()
            await self._initialize_agent()

            # 执行任务
            result = await self.agent.run()

            # 返回结果
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
            # 清理资源
            await self.cleanup()

    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def run_sync(self) -> Dict[str, Any]:
        """
        同步执行测试任务

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
    创建 BrowserUse 服务实例的工厂函数

    Args:
        task: 自然语言描述的测试任务
        browser_mode: 浏览器模式 ('headless' 或 'headed')
        screenshot_callback: 截图回调函数
        step_callback: 步骤回调函数

    Returns:
        BrowserUseService 实例
    """
    return BrowserUseService(
        task=task,
        browser_mode=browser_mode,
        screenshot_callback=screenshot_callback,
        step_callback=step_callback,
    )
