r"""
CLI 测试执行服务

通过 subprocess 调用 run_aiTest.py 脚本执行测试，
并实时监控执行状态和输出。

文件位置: D:\AI\AI-test-project\Django_project\ui_automation\services\cli_test_executor_service.py
"""

import asyncio
import json
import os
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List


class CliTestExecutorService:
    """CLI 测试执行服务"""

    # 脚本路径 (从 services/cli_test_executor_service.py 到 browser-use-0.11.2/run/run_aiTest.py)
    # __file__ = .../ui_automation/services/cli_test_executor_service.py
    # __file__.parent = .../ui_automation/services/
    # __file__.parent.parent = .../ui_automation/
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
        初始化 CLI 测试执行服务

        Args:
            execution_id: 执行记录 ID
            task: 自然语言测试任务
            browser_mode: 浏览器模式 (headless/headed)
            model: LLM 模型
            max_steps: 最大步骤数
            progress_callback: 进度回调函数
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
        """发送进度更新"""
        if self.progress_callback:
            try:
                self.progress_callback({
                    'execution_id': self.execution_id,
                    'message': message,
                    'data': data or {},
                    'timestamp': datetime.now().isoformat(),
                })
            except Exception as e:
                print(f"Progress callback error: {e}")

    def _parse_output_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析输出行

        支持:
        - ##PROGRESS##{json} - 进度信息
        - ##RESULT##{json} - 最终结果
        - 其他 - 普通输出
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
        """构建 CLI 命令"""
        cmd = [
            "python",
            str(self.SCRIPT_PATH),
            "--task", self.task,
            "--browser-mode", self.browser_mode,
            "--model", self.model,
            "--max-steps", str(self.max_steps),
            "--execution-id", f"db_exec_{self.execution_id}",
            "--output-format", "json",
        ]
        return cmd

    def execute(self) -> Dict[str, Any]:
        """
        执行测试（同步）

        Returns:
            执行结果字典
        """
        try:
            cmd = self._build_command()

            # 启动子进程
            # 使用 python.exe 在 Windows 上
            python_exe = self._get_python_executable()
            cmd[0] = python_exe

            print(f"[CLI Executor] Python: {python_exe}")
            print(f"[CLI Executor] Script: {self.SCRIPT_PATH}")
            print(f"[CLI Executor] Command: {' '.join(cmd)}")
            print(f"[CLI Executor] Script exists: {self.SCRIPT_PATH.exists()}")

            self._emit_progress("启动 CLI 执行", {
                "command": " ".join(cmd),
                "script_path": str(self.SCRIPT_PATH),
                "python": python_exe,
            })

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
            )

            print(f"[CLI Executor] Process started with PID: {self.process.pid}")

            final_result = None
            stderr_output = []

            # 实时读取输出
            while True:
                # 读取 stdout
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
                        print(f"[CLI Progress] {parsed['data'].get('message', '')}")
                    elif parsed and parsed["type"] == "result":
                        final_result = parsed["data"]
                        print(f"[CLI Result] {final_result}")
                    elif parsed:
                        # 普通输出，记录到日志
                        print(f"[CLI Output] {parsed['data']}")

            # 等待进程结束
            return_code = self.process.wait()
            print(f"[CLI Executor] Process exited with code: {return_code}")

            # 读取剩余的 stderr
            remaining_stderr = self.process.stderr.read()
            if remaining_stderr:
                stderr_output.append(remaining_stderr)
                print(f"[CLI Stderr] {remaining_stderr}")

            stderr_text = "\n".join(stderr_output)

            if return_code != 0:
                return {
                    'success': False,
                    'execution_id': self.execution_id,
                    'error': f"CLI 执行失败 (退出码: {return_code})",
                    'stderr': stderr_text,
                    'steps': len(self.execution_steps),
                }

            # 返回结果
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
            print(f"[CLI Executor] File not found: {e}")
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
                'steps': len(self.execution_steps),
            }
        except Exception as e:
            print(f"[CLI Executor] Exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': f"执行异常: {str(e)}",
                'steps': len(self.execution_steps),
            }

    def _get_python_executable(self) -> str:
        """获取 Python 可执行文件路径"""
        # 优先使用项目指定的 Python 路径 D:\Python3.12\python.exe
        project_python = r'D:\Python3.12\python.exe'
        if os.path.exists(project_python):
            return project_python

        # 备选：使用 sys.executable（当前 Python 解释器）
        import sys
        current_python = sys.executable
        if current_python and os.path.exists(current_python):
            return current_python

        # Windows 上尝试 python.exe
        if os.name == 'nt':
            return 'python'

        # 其他系统尝试 python3
        return 'python3'

    def execute_async(self) -> Dict[str, Any]:
        """
        异步执行测试（在线程中运行）

        Returns:
            执行结果字典
        """
        # 在新线程中执行
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
        取消执行

        Returns:
            是否成功取消
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
        """获取执行步骤列表"""
        return self.execution_steps

    def get_final_result(self) -> Optional[Dict]:
        """获取最终结果"""
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
    执行测试用例的便捷函数

    Args:
        execution_id: 执行记录 ID
        task: 自然语言测试任务
        browser_mode: 浏览器模式
        model: LLM 模型
        max_steps: 最大步骤数
        progress_callback: 进度回调函数

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
