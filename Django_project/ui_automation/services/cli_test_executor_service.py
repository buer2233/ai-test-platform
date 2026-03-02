r"""
CLI 测试执行服务

通过 subprocess 调用 browser-use-0.11.2/run/run_aiTest.py 脚本执行测试，
并实时解析子进程的标准输出以监控执行状态和进度。

输出协议:
    子进程通过标准输出发送结构化消息，格式如下:
    - ##PROGRESS##{json} - 进度信息（步骤完成、操作描述等）
    - ##RESULT##{json}   - 最终执行结果
    - 其他行             - 普通日志输出
"""

import json
import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CliTestExecutorService:
    """
    CLI 测试执行服务。

    通过 subprocess.Popen 启动子进程运行测试脚本，实时读取输出并解析进度信息。

    Attributes:
        SCRIPT_PATH: 测试脚本的绝对路径
        execution_id: 关联的执行记录 ID
        process: 子进程实例（执行期间有效）
        execution_steps: 已收集的执行步骤列表
    """

    # 测试脚本路径（从 services/ 目录向上两级到 ui_automation/，再进入 browser-use-0.11.2/）
    SCRIPT_PATH = Path(__file__).parent.parent / "browser-use-0.11.2" / "run" / "run_aiTest.py"

    def __init__(
        self,
        execution_id: int,
        task: str,
        browser_mode: str = "headless",
        model: str = "gpt-4o-mini",
        max_steps: int = 50,
        progress_callback: Optional[Callable] = None,
    ):
        """
        初始化 CLI 测试执行服务。

        Args:
            execution_id: 执行记录 ID，用于追踪和报告路径生成
            task: 自然语言测试任务描述
            browser_mode: 浏览器模式（headless/headed）
            model: LLM 模型名称
            max_steps: Agent 最大执行步骤数
            progress_callback: 进度回调函数，签名: (dict) -> None

        Raises:
            FileNotFoundError: 测试脚本文件不存在
        """
        self.execution_id = execution_id
        self.task = task
        self.browser_mode = browser_mode
        self.model = model
        self.max_steps = max_steps
        self.progress_callback = progress_callback

        self.process: Optional[subprocess.Popen] = None
        self.execution_steps = []
        self.final_result: Optional[Dict] = None

        # 验证脚本路径
        if not self.SCRIPT_PATH.exists():
            raise FileNotFoundError(f"执行脚本不存在: {self.SCRIPT_PATH}")

    def _emit_progress(self, message: str, data: Optional[Dict] = None) -> None:
        """通过回调函数发送进度更新。"""
        if self.progress_callback:
            try:
                self.progress_callback({
                    'execution_id': self.execution_id,
                    'message': message,
                    'data': data or {},
                    'timestamp': datetime.now().isoformat(),
                })
            except Exception as e:
                logger.warning("进度回调执行失败: %s", e)

    def _parse_output_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析子进程输出行。

        根据前缀标记识别消息类型:
            ##PROGRESS##  - 进度信息（JSON 载荷偏移量: 12）
            ##RESULT##    - 最终结果（JSON 载荷偏移量: 10）
            其他          - 普通输出

        Args:
            line: 已去除首尾空白的输出行

        Returns:
            解析后的消息字典 {"type": str, "data": ...}，空行返回 None
        """
        if not line:
            return None

        if line.startswith("##PROGRESS##"):
            try:
                return {"type": "progress", "data": json.loads(line[11:])}
            except json.JSONDecodeError:
                return {"type": "output", "data": line}
        elif line.startswith("##RESULT##"):
            try:
                return {"type": "result", "data": json.loads(line[10:])}
            except json.JSONDecodeError:
                return {"type": "output", "data": line}
        else:
            return {"type": "output", "data": line}

    def _build_command(self) -> List[str]:
        """构建 CLI 命令行参数列表。"""
        return [
            "python",
            str(self.SCRIPT_PATH),
            "--task", self.task,
            "--browser-mode", self.browser_mode,
            "--model", self.model,
            "--max-steps", str(self.max_steps),
            "--execution-id", f"db_exec_{self.execution_id}",
            "--output-format", "json",
        ]

    def execute(self) -> Dict[str, Any]:
        """
        同步执行测试。

        启动子进程，实时读取标准输出并解析进度/结果消息，
        等待子进程结束后返回结果。

        Returns:
            执行结果字典，包含 success、execution_id、report_path 等字段
        """
        try:
            cmd = self._build_command()

            # 使用项目配置的 Python 解释器
            python_exe = self._get_python_executable()
            cmd[0] = python_exe

            logger.info("[CLI Executor] Python: %s, Script: %s", python_exe, self.SCRIPT_PATH)
            logger.debug("[CLI Executor] Command: %s", ' '.join(cmd))

            self._emit_progress("启动 CLI 执行", {
                "command": " ".join(cmd),
                "script_path": str(self.SCRIPT_PATH),
                "python": python_exe,
            })

            # 启动子进程，使用行缓冲模式以便实时读取输出
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
            )

            logger.info("[CLI Executor] Process started with PID: %d", self.process.pid)

            final_result = None
            stderr_output = []

            # 实时读取标准输出，解析进度和结果消息
            while True:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    parsed = self._parse_output_line(line)

                    if parsed and parsed["type"] == "progress":
                        self.execution_steps.append(parsed["data"])
                        self._emit_progress(
                            parsed["data"].get("message", ""),
                            parsed["data"].get("data", {})
                        )
                        logger.debug("[CLI Progress] %s", parsed['data'].get('message', ''))
                    elif parsed and parsed["type"] == "result":
                        final_result = parsed["data"]
                        logger.info("[CLI Result] %s", final_result)
                    elif parsed:
                        logger.debug("[CLI Output] %s", parsed['data'])

            # 等待子进程结束
            return_code = self.process.wait()
            logger.info("[CLI Executor] Process exited with code: %d", return_code)

            # 读取残留的 stderr 输出
            remaining_stderr = self.process.stderr.read()
            if remaining_stderr:
                stderr_output.append(remaining_stderr)
                logger.warning("[CLI Stderr] %s", remaining_stderr)

            stderr_text = "\n".join(stderr_output)

            # 非零退出码表示 CLI 执行失败
            if return_code != 0:
                return {
                    'success': False,
                    'execution_id': self.execution_id,
                    'error': f"CLI 执行失败 (退出码: {return_code})",
                    'stderr': stderr_text,
                    'steps': len(self.execution_steps),
                }

            # 解析最终结果
            if final_result:
                result_data = final_result.get('data', {})
                return {
                    'success': final_result.get('success', False),
                    'execution_id': self.execution_id,
                    'report_path': result_data.get('report_path'),
                    'total_steps': result_data.get('total_steps', 0),
                    'is_successful': result_data.get('is_successful', False),
                    'is_done': result_data.get('is_done', False),
                    'duration': final_result.get('duration_seconds', 0),
                    'final_result': result_data.get('final_result'),
                    'steps': len(self.execution_steps),
                }
            else:
                return {
                    'success': False,
                    'execution_id': self.execution_id,
                    'error': "未获取到执行结果",
                    'stderr': stderr_text,
                    'steps': len(self.execution_steps),
                }

        except FileNotFoundError as e:
            logger.error("[CLI Executor] File not found: %s", e)
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
                'steps': len(self.execution_steps),
            }
        except Exception as e:
            logger.error("[CLI Executor] Exception: %s", e, exc_info=True)
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': f"执行异常: {str(e)}",
                'steps': len(self.execution_steps),
            }

    def _get_python_executable(self) -> str:
        """
        获取 Python 可执行文件路径。

        优先级:
            1. 项目指定的路径 D:\\Python3.12\\python.exe
            2. 当前解释器路径 sys.executable
            3. Windows 上使用 'python'，其他系统使用 'python3'
        """
        # 优先使用项目指定的 Python 路径
        project_python = r'D:\Python3.12\python.exe'
        if os.path.exists(project_python):
            return project_python

        # 备选: 当前 Python 解释器
        current_python = sys.executable
        if current_python and os.path.exists(current_python):
            return current_python

        # 最终回退: 系统默认 Python
        return 'python' if os.name == 'nt' else 'python3'

    def execute_async(self) -> Dict[str, Any]:
        """
        在独立线程中执行测试（阻塞等待结果，最长 1 小时）。

        Returns:
            执行结果字典

        Raises:
            Exception: 线程内发生的异常会被重新抛出
        """
        result = {}
        exception = None

        def run_in_thread():
            nonlocal result, exception
            try:
                result = self.execute()
            except Exception as e:
                exception = e

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=3600)  # 最大等待时间 1 小时

        if exception:
            raise exception

        return result

    def cancel(self) -> bool:
        """
        取消正在执行的子进程。

        先发送 SIGTERM，等待 5 秒后如果仍未退出则发送 SIGKILL。

        Returns:
            是否成功取消（进程已在运行且被终止返回 True）
        """
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

                self._emit_progress("CLI 执行已取消")
                return True
            return False
        except Exception as e:
            print(f"Cancel error: {e}")
            return False

    def get_execution_steps(self) -> list:
        """获取已收集的执行步骤列表。"""
        return self.execution_steps

    def get_final_result(self) -> Optional[Dict]:
        """获取最终执行结果。"""
        return self.final_result


def execute_test_case_cli(
    execution_id: int,
    task: str,
    browser_mode: str = "headless",
    model: str = "gpt-4o-mini",
    max_steps: int = 50,
    progress_callback: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    CLI 方式执行测试用例的便捷函数。

    创建 CliTestExecutorService 实例并立即执行，参数含义同构造函数。

    Returns:
        执行结果字典
    """
    executor = CliTestExecutorService(
        execution_id=execution_id,
        task=task,
        browser_mode=browser_mode,
        model=model,
        max_steps=max_steps,
        progress_callback=progress_callback,
    )
    return executor.execute()
