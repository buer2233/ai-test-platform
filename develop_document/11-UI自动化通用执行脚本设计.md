# UI自动化通用执行脚本设计文档

> 创建日期：2026-01-21
> 状态：脑暴完成，设计方案确认
> 版本：v1.0.0

---

## 一、概述

### 1.1 设计目标

创建一个通用的 browser-use 执行脚本 `run_aiTest.py`，支持以下两种调用模式：

1. **独立 CLI 模式**：用户可通过命令行直接执行测试，用于单独调试
2. **API 调用模式**：Django 后端通过 subprocess 调用该脚本，实现前端触发的测试执行

### 1.2 架构模式

采用**混合模式（方案B）**设计：

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Vue 3)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  填写自然语言用例 + 配置参数 → 调用后端接口                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       后端层 (Django)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  UiTestExecutionViewSet.execute()                         │  │
│  │    ├── 创建执行记录                                        │  │
│  │    └── 调用 CliTestExecutorService.run_cli_test()         │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CliTestExecutorService                                   │  │
│  │    ├── subprocess.Popen() 调用 run_aiTest.py             │  │
│  │    ├── 实时读取 stdout/stderr 输出                         │  │
│  │    ├── WebSocket 推送执行日志                              │  │
│  │    └── 监控执行状态和报告生成                              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   run_aiTest.py (CLI 执行脚本)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. 解析 CLI 参数（task, browser_mode, model, 等）        │  │
│  │  2. 从 .env 加载 OPENAI_API_KEY 和 OPENAI_API_BASE_URL    │  │
│  │  3. 初始化 browser-use Agent                              │  │
│  │  4. 执行测试任务                                          │  │
│  │  5. 输出执行进度到 stdout（JSON格式）                      │  │
│  │  6. 保存测试报告到 report/ 目录                            │  │
│  │  7. 输出最终结果到 stdout（JSON格式）                      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    browser-use 执行层                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Agent(task=task, llm=llm)                                 │  │
│  │    ├── 执行浏览器操作                                      │  │
│  │    ├── 生成执行历史                                        │  │
│  │    └── 保存报告到指定目录                                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心设计

### 2.1 run_aiTest.py 脚本设计

#### 文件位置
```
D:\AI\AI-test-project\Django_project\ui_automation\browser-use-0.11.2\run\run_aiTest.py
```

#### CLI 参数设计

```bash
# 基础用法
python run_aiTest.py --task "测试任务描述"

# 完整参数示例
python run_aiTest.py \
  --task "在谷歌搜索 browser-use 并告诉我前3个结果" \
  --browser-mode headless \
  --model gpt-4o-mini \
  --max-steps 50 \
  --report-dir ./report \
  --report-format json \
  --execution-id "exec_123" \
  --output-format json
```

#### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--task` | string | 必填 | 自然语言描述的测试任务 |
| `--browser-mode` | string | headless | 浏览器模式：headless（无头）/ headed（有头） |
| `--model` | string | gpt-4o-mini | 使用的 LLM 模型 |
| `--max-steps` | int | 50 | 最大执行步骤数 |
| `--report-dir` | string | ./report | 测试报告保存目录 |
| `--report-format` | string | json | 报告格式：json / html |
| `--execution-id` | string | auto | 执行记录 ID（用于关联数据库） |
| `--output-format` | string | json | 输出格式：json / text |
| `--use-vision` | bool | True | 是否启用视觉模式 |
| `--timeout` | int | 180 | 单步超时时间（秒） |

#### 核心代码结构

```python
#!/usr/bin/env python3
"""
UI自动化测试通用执行脚本

支持两种运行模式：
1. 独立 CLI 模式：直接执行测试
2. API 调用模式：通过 Django 后端调用
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 添加 browser_use 到路径
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserProfile
from langchain_openai import ChatOpenAI

# 加载环境变量
load_dotenv()

# 报告输出目录（固定）
REPORT_DIR = Path(__file__).parent.parent / "report"


class ExecutionLogger:
    """执行日志输出器"""

    def __init__(self, output_format: str = "json"):
        self.output_format = output_format
        self.execution_start_time = datetime.now()

    def log_progress(self, level: str, message: str, data: Optional[Dict] = None):
        """输出执行进度"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }

        if self.output_format == "json":
            print(f"##PROGRESS##{json.dumps(log_entry, ensure_ascii=False)}", flush=True)
        else:
            print(f"[{level.upper()}] {message}", flush=True)

    def log_result(self, success: bool, data: Optional[Dict] = None):
        """输出最终结果"""
        result = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.execution_start_time).total_seconds(),
            "data": data or {}
        }

        if self.output_format == "json":
            print(f"##RESULT##{json.dumps(result, ensure_ascii=False)}", flush=True)
        else:
            print(f"\n{'='*50}")
            print(f"执行{'成功' if success else '失败'}")
            print(f"耗时: {result['duration_seconds']:.2f}秒")
            print(f"{'='*50}", flush=True)


class AITestRunner:
    """AI 测试执行器"""

    def __init__(
        self,
        task: str,
        browser_mode: str = "headless",
        model: str = "gpt-4o-mini",
        max_steps: int = 50,
        report_dir: Path = REPORT_DIR,
        execution_id: Optional[str] = None,
        use_vision: bool = True,
        timeout: int = 180,
        logger: Optional[ExecutionLogger] = None,
    ):
        self.task = task
        self.browser_mode = browser_mode
        self.model = model
        self.max_steps = max_steps
        self.report_dir = Path(report_dir)
        self.execution_id = execution_id or f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.use_vision = use_vision
        self.timeout = timeout
        self.logger = logger or ExecutionLogger()

        # 确保报告目录存在
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # 获取 API 配置
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.api_base = os.environ.get("OPENAI_API_BASE_URL")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 环境变量未设置")

    async def run(self) -> Dict[str, Any]:
        """执行测试任务"""
        try:
            self.logger.log_progress("info", "初始化浏览器和 LLM")

            # 初始化 LLM
            llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.api_base,
                temperature=0.0,
            )

            # 初始化浏览器
            browser_profile = BrowserProfile(
                headless=(self.browser_mode == "headless"),
            )

            self.logger.log_progress("info", "创建 Agent")

            # 创建 Agent
            agent = Agent(
                task=self.task,
                llm=llm,
                browser_profile=browser_profile,
                use_vision=self.use_vision,
                max_steps=None,  # 我们通过 run() 参数控制
            )

            self.logger.log_progress("info", f"开始执行任务: {self.task[:100]}...")

            # 执行任务
            history = await agent.run(max_steps=self.max_steps)

            # 保存报告
            report_path = self._save_report(history)

            # 判断执行结果
            is_done = history.is_done()
            is_successful = history.is_successful() if is_done else False

            result_data = {
                "execution_id": self.execution_id,
                "report_path": str(report_path),
                "is_done": is_done,
                "is_successful": is_successful,
                "total_steps": len(history.history),
                "final_result": history.final_result(),
            }

            self.logger.log_result(success=is_successful, data=result_data)

            return result_data

        except Exception as e:
            self.logger.log_progress("error", f"执行失败: {str(e)}")
            self.logger.log_result(success=False, data={"error": str(e)})
            raise

    def _save_report(self, history) -> Path:
        """保存测试报告"""
        report_path = self.report_dir / f"{self.execution_id}.json"

        self.logger.log_progress("info", f"保存测试报告: {report_path}")

        # 保存历史记录
        history.save_to_file(report_path)

        return report_path


def parse_arguments():
    """解析 CLI 参数"""
    parser = argparse.ArgumentParser(
        description="UI自动化测试通用执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础用法
  python run_aiTest.py --task "搜索 browser-use"

  # 完整参数
  python run_aiTest.py \\
    --task "在谷歌搜索 browser-use 并告诉我前3个结果" \\
    --browser-mode headless \\
    --model gpt-4o-mini \\
    --max-steps 50 \\
    --execution-id "test_001"
        """
    )

    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help="自然语言描述的测试任务"
    )

    parser.add_argument(
        "--browser-mode",
        type=str,
        default="headless",
        choices=["headless", "headed"],
        help="浏览器模式（默认: headless）"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="使用的 LLM 模型（默认: gpt-4o-mini）"
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=50,
        help="最大执行步骤数（默认: 50）"
    )

    parser.add_argument(
        "--report-dir",
        type=str,
        default=str(REPORT_DIR),
        help=f"测试报告保存目录（默认: {REPORT_DIR}）"
    )

    parser.add_argument(
        "--execution-id",
        type=str,
        default=None,
        help="执行记录 ID（用于关联数据库）"
    )

    parser.add_argument(
        "--use-vision",
        action="store_true",
        default=True,
        help="是否启用视觉模式（默认: True）"
    )

    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="禁用视觉模式"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="单步超时时间（秒，默认: 180）"
    )

    parser.add_argument(
        "--output-format",
        type=str,
        default="json",
        choices=["json", "text"],
        help="输出格式（默认: json）"
    )

    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_arguments()

    # 创建日志记录器
    logger = ExecutionLogger(output_format=args.output_format)

    # 创建执行器
    runner = AITestRunner(
        task=args.task,
        browser_mode=args.browser_mode,
        model=args.model,
        max_steps=args.max_steps,
        report_dir=Path(args.report_dir),
        execution_id=args.execution_id,
        use_vision=not args.no_vision,
        timeout=args.timeout,
        logger=logger,
    )

    # 执行测试
    await runner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n执行被用户中断", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n执行错误: {e}", file=sys.stderr)
        sys.exit(1)
```

---

### 2.2 后端服务重构设计

#### 2.2.1 新建 CliTestExecutorService

创建文件：`Django_project/ui_automation/services/cli_test_executor_service.py`

```python
"""
CLI 测试执行服务

通过 subprocess 调用 run_aiTest.py 脚本执行测试，
并实时监控执行状态和输出。
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from django.conf import settings


class CliTestExecutorService:
    """CLI 测试执行服务"""

    # 脚本路径
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
            browser_mode: 浏览器模式
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

    def execute(self) -> Dict[str, Any]:
        """
        执行测试（同步）

        Returns:
            执行结果字典
        """
        try:
            # 构建 CLI 命令
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

            self._emit_progress("启动 CLI 执行", {"command": " ".join(cmd)})

            # 启动子进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
            )

            final_result = None

            # 实时读取输出
            while True:
                # 读取 stdout
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    parsed = self._parse_output_line(line)

                    if parsed["type"] == "progress":
                        self.execution_steps.append(parsed["data"])
                        self._emit_progress(
                            parsed["data"].get("message", ""),
                            parsed["data"].get("data", {})
                        )
                    elif parsed["type"] == "result":
                        final_result = parsed["data"]
                    else:
                        # 普通输出
                        print(f"[CLI] {parsed['data']}")

            # 等待进程结束
            return_code = self.process.wait()

            # 读取 stderr
            stderr_output = self.process.stderr.read()

            if return_code != 0:
                return {
                    'success': False,
                    'execution_id': self.execution_id,
                    'error': f"CLI 执行失败 (退出码: {return_code})",
                    'stderr': stderr_output,
                }

            # 返回结果
            if final_result:
                return {
                    'success': final_result.get('success', False),
                    'execution_id': self.execution_id,
                    'report_path': final_result.get('report_path'),
                    'total_steps': final_result.get('total_steps', 0),
                    'is_successful': final_result.get('is_successful', False),
                    'duration': final_result.get('duration_seconds', 0),
                }
            else:
                return {
                    'success': False,
                    'execution_id': self.execution_id,
                    'error': "未获取到执行结果",
                }

        except Exception as e:
            return {
                'success': False,
                'execution_id': self.execution_id,
                'error': str(e),
            }

    def cancel(self) -> bool:
        """取消执行"""
        try:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self._emit_progress("CLI 执行已取消")
                return True
            return False
        except Exception as e:
            print(f"Cancel error: {e}")
            return False
```

#### 2.2.2 修改 UiTestExecutionViewSet

在 `views.py` 中修改 execute 方法：

```python
@action(detail=True, methods=['post'])
def execute(self, request, pk=None):
    """执行测试用例（通过 CLI 调用）"""
    test_case = self.get_object()

    # 检查用例是否启用
    if not test_case.is_enabled:
        return Response(
            {'error': '测试用例未启用'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 获取浏览器模式
    browser_mode = request.data.get('browser_mode', test_case.project.default_browser_mode)

    # 创建执行记录
    execution = UiTestExecution.objects.create(
        test_case=test_case,
        browser_mode=browser_mode,
        status='pending',
        created_by=request.user,
    )

    # 创建进度回调（用于 WebSocket 推送）
    def progress_callback(data):
        # 这里可以调用 WebSocket 服务推送实时进度
        from .services.websocket_service import broadcast_execution_progress
        asyncio.create_task(broadcast_execution_progress(execution.id, data))

    # 使用 CLI 执行服务
    from .services.cli_test_executor_service import CliTestExecutorService

    executor = CliTestExecutorService(
        execution_id=execution.id,
        task=test_case.natural_language_task,
        browser_mode=browser_mode,
        progress_callback=progress_callback,
    )

    # 在后台线程中执行
    import threading
    def run_in_background():
        result = executor.execute()

        # 更新执行记录
        execution.status = 'passed' if result['success'] else 'failed'
        execution.final_result = json.dumps(result.get('report_path', ''), ensure_ascii=False)
        execution.error_message = result.get('error', '')
        execution.completed_at = timezone.now()
        execution.duration_seconds = result.get('duration', 0)
        execution.save()

        # 创建测试报告
        if result.get('report_path'):
            UiTestReport.objects.create(
                execution=execution,
                report_path=result['report_path'],
            )

    thread = threading.Thread(target=run_in_background)
    thread.start()

    serializer = UiTestExecutionSerializer(execution)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
```

---

## 三、执行流程

### 3.1 完整执行流程图

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户在前端填写自然语言用例和配置参数                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 前端调用 POST /api/v1/ui-automation/test-cases/{id}/execute/│
│    请求体: { browser_mode: "headless" }                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 后端 UiTestExecutionViewSet.execute()                         │
│    - 创建 UiTestExecution 记录（status=pending）                  │
│    - 初始化 CliTestExecutorService                               │
│    - 启动后台线程执行                                            │
│    - 立即返回 execution_id 给前端                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. CliTestExecutorService.execute() (后台线程)                  │
│    - 构建 subprocess 命令                                         │
│    - 启动 run_aiTest.py 子进程                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. run_aiTest.py 执行测试                                         │
│    - 解析 CLI 参数                                               │
│    - 从 .env 加载 OPENAI_API_KEY                                 │
│    - 初始化 browser-use Agent                                    │
│    - 执行测试任务                                                │
│    - 输出进度: ##PROGRESS##{json}                                │
│    - 保存报告到 report/ 目录                                     │
│    - 输出结果: ##RESULT##{json}                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. CliTestExecutorService 实时读取子进程输出                      │
│    - 解析 ##PROGRESS## 消息                                      │
│    - 通过 WebSocket 推送到前端                                   │
│    - 解析 ##RESULT## 消息                                        │
│    - 更新 UiTestExecution 状态                                   │
│    - 创建 UiTestReport 记录                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. 前端实时显示执行进度                                          │
│    - WebSocket 接收进度消息                                      │
│    - 显示执行步骤和日志                                          │
│    - 执行完成后跳转到报告页面                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、数据流设计

### 4.1 CLI 输出格式

#### 进度输出格式
```
##PROGRESS##{"timestamp": "2026-01-21T10:30:00", "level": "info", "message": "初始化浏览器和 LLM", "data": {}}
##PROGRESS##{"timestamp": "2026-01-21T10:30:01", "level": "info", "message": "创建 Agent", "data": {}}
##PROGRESS##{"timestamp": "2026-01-21T10:30:02", "level": "info", "message": "执行步骤: click", "data": {"step": {...}}}
```

#### 结果输出格式
```
##RESULT##{
  "success": true,
  "timestamp": "2026-01-21T10:35:00",
  "duration_seconds": 300.5,
  "data": {
    "execution_id": "db_exec_123",
    "report_path": "D:\\...\\report\\db_exec_123.json",
    "is_done": true,
    "is_successful": true,
    "total_steps": 15,
    "final_result": "找到了3个相关结果"
  }
}
```

### 4.2 WebSocket 推送格式

```json
{
  "type": "execution_progress",
  "execution_id": 123,
  "message": "执行步骤: 点击搜索按钮",
  "data": {
    "step": 5,
    "action": "click",
    "element": "搜索按钮",
    "screenshot": "base64_encoded_image"
  },
  "timestamp": "2026-01-21T10:30:15"
}
```

---

## 五、测试报告格式

### 5.1 报告存储位置

```
D:\AI\AI-test-project\Django_project\ui_automation\browser-use-0.11.2\report\
├── db_exec_123.json        # 执行ID为123的报告
├── db_exec_124.json        # 执行ID为124的报告
└── ...
```

### 5.2 报告内容格式

browser-use 生成的报告格式（AgentHistoryList.save_to_file()）：

```json
{
  "history": [
    {
      "model_output": {
        "evaluation_previous_goal": "Starting search...",
        "memory": "Need to search for browser-use",
        "next_goal": "Go to Google",
        "action": [
          {"go_to_url": "https://google.com"}
        ]
      },
      "result": [
        {
          "is_done": false,
          "long_term_memory": "Navigated to Google"
        }
      ],
      "state": {
        "url": "https://google.com",
        "title": "Google",
        "screenshot_path": "/path/to/screenshot.png"
      },
      "metadata": {
        "step_number": 1,
        "step_start_time": 1234567890.123,
        "step_end_time": 1234567895.456
      }
    }
  ],
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 5678,
    "total_cost": 0.012
  }
}
```

---

## 六、开发步骤

### 阶段 1：创建 run_aiTest.py 脚本
1. 创建 `run/run_aiTest.py` 文件
2. 实现 CLI 参数解析
3. 实现 AITestRunner 核心逻辑
4. 实现报告保存功能
5. 测试独立 CLI 执行

### 阶段 2：创建 CliTestExecutorService
1. 创建 `services/cli_test_executor_service.py`
2. 实现 subprocess 调用逻辑
3. 实现实时输出解析
4. 实现进度回调机制

### 阶段 3：修改后端 API
1. 修改 `views.py` 中的 execute 方法
2. 集成 CliTestExecutorService
3. 实现后台线程执行
4. 更新执行记录状态

### 阶段 4：前端集成
1. 修改执行监控页面，支持实时进度显示
2. 解析 WebSocket 推送的进度消息
3. 实现报告页面展示

### 阶段 5：测试验证
1. 测试独立 CLI 执行
2. 测试 API 调用执行
3. 测试实时进度推送
4. 测试报告生成和展示

---

## 七、风险与注意事项

### 7.1 潜在风险

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| subprocess 调用失败 | 测试无法执行 | 添加错误处理和重试机制 |
| 实时输出解析失败 | 进度无法展示 | 严格定义输出格式，添加容错处理 |
| 报告文件读写冲突 | 报告损坏 | 使用唯一的 execution_id 作为文件名 |
| WebSocket 连接断开 | 实时进度丢失 | 实现断线重连机制 |

### 7.2 注意事项

1. **路径问题**：确保 run_aiTest.py 可以正确导入 browser_use 模块
2. **环境变量**：确保 .env 文件中的 OPENAI_API_KEY 配置正确
3. **超时处理**：合理设置单步超时时间，避免长时间等待
4. **日志记录**：保留足够的日志用于问题排查
5. **资源清理**：确保子进程和浏览器资源正确释放

---

## 八、后续扩展

### 8.1 可扩展配置

1. 支持配置文件（YAML/JSON）
2. 支持环境变量覆盖
3. 支持多模型并行执行
4. 支持自定义输出格式

### 8.2 功能增强

1. 支持测试用例批量执行
2. 支持定时任务执行
3. 支持执行结果对比分析
4. 支持 CI/CD 集成

---

*文档维护：本文档将持续更新，记录开发进度和设计变更*
