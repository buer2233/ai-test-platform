"""
测试报告生成器

根据测试执行结果生成 HTML 格式的可视化报告。

报告包含:
    - 测试状态总览（通过/失败/错误）
    - 执行统计卡片（步骤数、完成数、失败数、时长）
    - 测试用例信息（名称、任务描述、预期结果、浏览器模式）
    - 执行步骤时间线
    - 错误信息详情
    - 执行截图画廊
"""

import json
import os
from typing import Dict, List

from django.template import Template, Context
from django.utils import timezone


class ReportGenerator:
    """
    HTML 测试报告生成器。

    使用 Django 模板引擎将执行结果渲染为独立的 HTML 报告文件。
    报告包含内联 CSS 样式，无需外部依赖即可在浏览器中直接打开。

    使用方式:
        generator = ReportGenerator(execution)
        html = generator.generate_html()        # 获取 HTML 字符串
        generator.save_to_file('/path/to.html')  # 保存为文件
    """

    # HTML 模板
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI自动化测试报告 - {{ test_case_name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header .meta { opacity: 0.9; font-size: 14px; }
        .status-banner {
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: bold;
        }
        .status-passed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-error { background: #fff3cd; color: #856404; }
        .status-cancelled { background: #e2e3e5; color: #383d41; }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-label { color: #6c757d; font-size: 14px; margin-bottom: 5px; }
        .card-value { font-size: 28px; font-weight: bold; color: #333; }
        .section {
            background: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .info-row {
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid #e9ecef;
        }
        .info-label {
            width: 150px;
            color: #6c757d;
            font-weight: 500;
        }
        .info-value { color: #333; }
        .steps-list { list-style: none; }
        .step-item {
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .step-number {
            display: inline-block;
            background: #667eea;
            color: white;
            width: 28px;
            height: 28px;
            line-height: 28px;
            text-align: center;
            border-radius: 50%;
            margin-right: 10px;
            font-weight: bold;
        }
        .step-action { font-weight: bold; margin-bottom: 5px; }
        .step-time { color: #6c757d; font-size: 12px; }
        .step-success { border-left-color: #28a745; }
        .step-failed { border-left-color: #dc3545; }
        .screenshots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
        }
        .screenshot-item {
            background: #f8f9fa;
            border-radius: 8px;
            overflow: hidden;
        }
        .screenshot-item img {
            width: 100%;
            height: auto;
            display: block;
        }
        .screenshot-caption {
            padding: 10px;
            font-size: 14px;
            color: #6c757d;
        }
        .error-box {
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .error-title { font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{{ test_case_name }}</h1>
            <div class="meta">
                <p>项目: {{ project_name }}</p>
                <p>执行时间: {{ execution_time }}</p>
            </div>
        </div>

        <!-- Status Banner -->
        <div class="status-banner status-{{ status }}">
            {% if status == 'passed' %}✓ 测试通过{% elif status == 'failed' %}✗ 测试失败{% elif status == 'error' %}⚠ 执行错误{% else %}○ 已取消{% endif %}
        </div>

        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="card">
                <div class="card-label">总步骤数</div>
                <div class="card-value">{{ total_steps }}</div>
            </div>
            <div class="card">
                <div class="card-label">完成步骤</div>
                <div class="card-value">{{ completed_steps }}</div>
            </div>
            <div class="card">
                <div class="card-label">失败步骤</div>
                <div class="card-value">{{ failed_steps }}</div>
            </div>
            <div class="card">
                <div class="card-label">执行时长</div>
                <div class="card-value">{{ duration }}</div>
            </div>
        </div>

        <!-- Test Case Info -->
        <div class="section">
            <div class="section-title">测试用例信息</div>
            <div class="info-row">
                <div class="info-label">用例名称:</div>
                <div class="info-value">{{ test_case_name }}</div>
            </div>
            <div class="info-row">
                <div class="info-label">自然语言任务:</div>
                <div class="info-value">{{ natural_language_task }}</div>
            </div>
            <div class="info-row">
                <div class="info-label">预期结果:</div>
                <div class="info-value">{{ expected_result }}</div>
            </div>
            <div class="info-row">
                <div class="info-label">浏览器模式:</div>
                <div class="info-value">{{ browser_mode }}</div>
            </div>
        </div>

        {% if steps %}
        <!-- Execution Steps -->
        <div class="section">
            <div class="section-title">执行步骤</div>
            <ul class="steps-list">
                {% for step in steps %}
                <li class="step-item {% if step.success %}step-success{% else %}step-failed{% endif %}">
                    <span class="step-number">{{ forloop.counter }}</span>
                    <div class="step-action">{{ step.action }}</div>
                    <div class="step-time">{{ step.timestamp }}</div>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if error_message %}
        <!-- Error Message -->
        <div class="section">
            <div class="section-title">错误信息</div>
            <div class="error-box">
                <div class="error-title">执行错误</div>
                <div>{{ error_message }}</div>
            </div>
        </div>
        {% endif %}

        {% if screenshots %}
        <!-- Screenshots -->
        <div class="section">
            <div class="section-title">执行截图</div>
            <div class="screenshots-grid">
                {% for screenshot in screenshots %}
                <div class="screenshot-item">
                    <img src="data:image/png;base64,{{ screenshot.data }}" alt="{{ screenshot.description }}">
                    <div class="screenshot-caption">{{ screenshot.description }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
    """

    def __init__(self, execution):
        """
        初始化报告生成器。

        Args:
            execution: UiTestExecution 实例，需要已关联 test_case、project 和 report
        """
        self.execution = execution

    def _parse_agent_history(self) -> List[Dict]:
        """从关联的报告记录中解析 Agent 执行历史 JSON 数据。"""
        try:
            if self.execution.report:
                history_json = self.execution.report.agent_history
                if history_json:
                    return json.loads(history_json)
        except Exception as e:
            print(f"Error parsing agent history: {e}")

        return []

    def _parse_screenshots(self) -> List[Dict]:
        """从关联的报告记录中解析截图路径列表。"""
        try:
            if self.execution.report:
                screenshots_json = self.execution.report.screenshot_paths
                if screenshots_json:
                    return json.loads(screenshots_json)
        except Exception as e:
            print(f"Error parsing screenshots: {e}")

        return []

    def _format_duration(self) -> str:
        """将执行时长格式化为中文可读字符串（如 '2分30秒'）。"""
        if self.execution.duration_seconds is None:
            return '-'

        duration = self.execution.duration_seconds
        if duration < 60:
            return f'{duration}秒'
        minutes = duration // 60
        seconds = duration % 60
        return f'{minutes}分{seconds}秒'

    def _format_execution_time(self) -> str:
        """格式化执行开始时间为 'YYYY-MM-DD HH:MM:SS' 格式。"""
        if self.execution.started_at:
            return self.execution.started_at.strftime('%Y-%m-%d %H:%M:%S')
        return timezone.now().strftime('%Y-%m-%d %H:%M:%S')

    def generate_html(self) -> str:
        """
        生成完整的 HTML 报告。

        从执行记录和关联的报告数据中提取信息，
        使用 Django 模板引擎渲染为 HTML 字符串。

        Returns:
            渲染后的 HTML 报告字符串
        """
        # 解析数据
        steps = self._parse_agent_history()
        screenshots = self._parse_screenshots()

        # 准备模板上下文
        context = Context({
            'test_case_name': self.execution.test_case.name,
            'project_name': self.execution.project.name,
            'execution_time': self._format_execution_time(),
            'status': self.execution.status,
            'total_steps': self.execution.report.total_steps if self.execution.report else 0,
            'completed_steps': self.execution.report.completed_steps if self.execution.report else 0,
            'failed_steps': self.execution.report.failed_steps if self.execution.report else 0,
            'duration': self._format_duration(),
            'natural_language_task': self.execution.test_case.natural_language_task,
            'expected_result': self.execution.test_case.expected_result or '无',
            'browser_mode': self.execution.get_browser_mode_display(),
            'steps': steps,
            'error_message': self.execution.error_message,
            'screenshots': screenshots,
        })

        # 渲染模板
        template = Template(self.HTML_TEMPLATE)
        return template.render(context)

    def save_to_file(self, file_path: str) -> str:
        """
        生成报告并保存到指定文件路径。

        自动创建所需的目录结构。

        Args:
            file_path: 保存文件的目标路径

        Returns:
            保存成功的文件路径
        """
        html_content = self.generate_html()

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return file_path


def generate_report(execution) -> str:
    """生成 HTML 测试报告的便捷函数。"""
    generator = ReportGenerator(execution)
    return generator.generate_html()


def save_report(execution, file_path: str) -> str:
    """生成并保存 HTML 测试报告的便捷函数。"""
    generator = ReportGenerator(execution)
    return generator.save_to_file(file_path)
