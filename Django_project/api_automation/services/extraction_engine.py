"""
数据提取引擎
负责从HTTP响应中提取变量值
"""

import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from urllib.parse import parse_qs, urlparse
import logging

logger = logging.getLogger(__name__)

# 尝试导入WebSocket服务
try:
    from .websocket_service import websocket_service
    WEBSOCKET_ENABLED = True
except ImportError:
    WEBSOCKET_ENABLED = False
    websocket_service = None


class ExtractionResult:
    """提取结果"""

    def __init__(self, variable_name: str, value: Any, success: bool, message: str = ""):
        self.variable_name = variable_name
        self.value = value
        self.success = success
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'variable_name': self.variable_name,
            'value': self.value,
            'success': self.success,
            'message': self.message
        }


class ExtractionEngine:
    """数据提取引擎"""

    def __init__(self):
        pass

    def extract_variables(
        self,
        extractions: List[Dict[str, Any]],
        http_response: Any,
        response_body: Any = None,
        response_text: str = None,
        execution_id: Optional[int] = None,
        test_case_id: Optional[int] = None
    ) -> Tuple[Dict[str, Any], List[ExtractionResult]]:
        """
        执行变量提取列表

        Args:
            extractions: 提取配置列表
            http_response: HTTP响应对象
            response_body: 响应体数据（已解析）
            response_text: 响应体文本（原始）
            execution_id: 执行ID（用于WebSocket广播）
            test_case_id: 测试用例ID（用于WebSocket广播）

        Returns:
            tuple[Dict[str, Any], List[ExtractionResult]]: 提取的变量字典和提取结果列表
        """
        variables = {}
        results = []

        for extraction in extractions:
            # 检查是否启用
            if not extraction.get('is_enabled', True):
                continue

            try:
                result = self._extract_single_variable(
                    extraction,
                    http_response,
                    response_body,
                    response_text
                )
                results.append(result)

                # WebSocket广播变量提取结果
                if WEBSOCKET_ENABLED and execution_id:
                    self._broadcast_variable_extracted(
                        execution_id,
                        test_case_id,
                        result
                    )

                if result.success:
                    variables[result.variable_name] = result.value
            except Exception as e:
                logger.error(f"Error extracting variable: {extraction} - {str(e)}")
                # 使用默认值
                var_name = extraction.get('variable_name', 'unknown')
                default_value = extraction.get('default_value')
                error_result = ExtractionResult(
                    variable_name=var_name,
                    value=default_value,
                    success=False,
                    message=f"提取失败，使用默认值: {str(e)}"
                )
                results.append(error_result)

                # WebSocket广播提取失败
                if WEBSOCKET_ENABLED and execution_id:
                    self._broadcast_variable_extracted(
                        execution_id,
                        test_case_id,
                        error_result
                    )

                if default_value is not None:
                    variables[var_name] = default_value

        return variables, results

    def _broadcast_variable_extracted(
        self,
        execution_id: int,
        test_case_id: Optional[int],
        result: ExtractionResult
    ):
        """
        广播变量提取结果到WebSocket

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            result: 提取结果
        """
        try:
            websocket_service.broadcast_variable_extracted(
                execution_id=execution_id,
                test_case_id=test_case_id,
                variable_name=result.variable_name,
                value=str(result.value) if result.value is not None else None,
                success=result.success,
                message=result.message
            )
        except Exception as e:
            logger.error(f"Error broadcasting variable extracted: {str(e)}")

    def _extract_single_variable(
        self,
        extraction: Dict[str, Any],
        http_response: Any,
        response_body: Any,
        response_text: str
    ) -> ExtractionResult:
        """
        执行单个变量提取

        Args:
            extraction: 提取配置
            http_response: HTTP响应对象
            response_body: 响应体数据
            response_text: 响应体文本

        Returns:
            ExtractionResult: 提取结果
        """
        variable_name = extraction.get('variable_name', '')
        extract_type = extraction.get('extract_type', '')
        extract_expression = extraction.get('extract_expression', '')
        extract_scope = extraction.get('extract_scope', 'body')
        default_value = extraction.get('default_value')

        # 根据提取范围获取源数据
        source_data = self._get_source_data(extract_scope, http_response, response_body, response_text)

        # 根据提取类型执行提取
        if extract_type == 'regex':
            value = self._extract_regex(source_data, extract_expression)
        elif extract_type == 'json_path':
            value = self._extract_json_path(source_data, extract_expression)
        elif extract_type == 'xpath':
            value = self._extract_xpath(source_data, extract_expression)
        elif extract_type == 'css_selector':
            value = self._extract_css_selector(source_data, extract_expression)
        elif extract_type == 'header':
            value = self._extract_header(http_response, extract_expression)
        elif extract_type == 'cookie':
            value = self._extract_cookie(http_response, extract_expression)
        else:
            return ExtractionResult(
                variable_name=variable_name,
                value=default_value,
                success=False,
                message=f"不支持的提取类型: {extract_type}"
            )

        # 检查提取结果
        if value is None or value == '':
            if default_value is not None:
                return ExtractionResult(
                    variable_name=variable_name,
                    value=default_value,
                    success=True,
                    message=f"提取失败，使用默认值"
                )
            return ExtractionResult(
                variable_name=variable_name,
                value=None,
                success=False,
                message="未匹配到值"
            )

        return ExtractionResult(
            variable_name=variable_name,
            value=value,
            success=True,
            message="提取成功"
        )

    def _get_source_data(
        self,
        scope: str,
        http_response: Any,
        response_body: Any,
        response_text: str
    ) -> Any:
        """根据提取范围获取源数据"""
        if scope == 'headers':
            return dict(http_response.headers) if http_response else {}
        elif scope == 'url':
            return getattr(http_response, 'url', '') if http_response else ''
        else:  # body
            # 如果 response_body 是 dict 或 list，转换为 JSON 字符串
            if response_body is not None:
                if isinstance(response_body, (dict, list)):
                    return json.dumps(response_body, ensure_ascii=False)
                return response_body
            return response_text

    def _extract_regex(self, source: Any, pattern: str) -> Optional[str]:
        """
        使用正则表达式提取数据

        Args:
            source: 源数据
            pattern: 正则表达式模式

        Returns:
            Optional[str]: 提取的值（第一个捕获组）
        """
        if source is None:
            return None

        text = str(source)
        try:
            # 添加 re.IGNORECASE 标志以提高匹配成功率
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 返回第一个捕获组，如果没有捕获组则返回整个匹配
                if match.groups():
                    return match.group(1)
                return match.group(0)
            return None
        except re.error as e:
            logger.error(f"Invalid regex pattern {pattern}: {str(e)}")
            return None

    def _extract_json_path(self, source: Any, json_path: str) -> Optional[Any]:
        """
        使用JSONPath提取数据

        Args:
            source: 源数据（应该是dict或list）
            json_path: JSON路径表达式，如 $.data.user.id

        Returns:
            Optional[Any]: 提取的值
        """
        if source is None:
            return None

        # 确保source是dict
        if isinstance(source, str):
            try:
                source = json.loads(source)
            except json.JSONDecodeError:
                return None

        if not isinstance(source, (dict, list)):
            return None

        # 处理JSONPath表达式
        if json_path.startswith('$.'):
            path = json_path[2:]  # 去掉 $.
        else:
            path = json_path

        return self._navigate_json_path(source, path)

    def _navigate_json_path(self, data: Any, path: str) -> Optional[Any]:
        """
        在JSON数据中导航到指定路径

        Args:
            data: JSON数据
            path: 路径（不含$.前缀）

        Returns:
            Optional[Any]: 路径指向的值
        """
        if not path:
            return data

        try:
            current = data
            parts = self._parse_json_path(path)

            for part in parts:
                if current is None:
                    return None

                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    if part.isdigit():
                        index = int(part)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return None
                    else:
                        return None
                else:
                    return None

            return current
        except Exception as e:
            logger.error(f"Error navigating JSON path {path}: {str(e)}")
            return None

    def _parse_json_path(self, path: str) -> List[str]:
        """
        解析JSON路径

        Args:
            path: JSON路径字符串

        Returns:
            List[str]: 路径部分列表
        """
        parts = []
        current_part = ""
        in_brackets = False

        for char in path:
            if char == '.' and not in_brackets:
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == '[':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                in_brackets = True
            elif char == ']':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                in_brackets = False
            else:
                current_part += char

        if current_part:
            parts.append(current_part)

        return parts

    def _extract_xpath(self, source: Any, xpath: str) -> Optional[str]:
        """
        使用XPath表达式提取数据（需要lxml库）

        Args:
            source: 源数据（HTML/XML字符串）
            xpath: XPath表达式

        Returns:
            Optional[str]: 提取的值
        """
        if source is None:
            return None

        try:
            from lxml import etree
            from io import StringIO

            tree = etree.parse(StringIO(str(source)), etree.HTMLParser())
            nodes = tree.xpath(xpath)

            if nodes:
                if isinstance(nodes[0], str):
                    return ''.join(nodes)
                elif hasattr(nodes[0], 'text'):
                    return nodes[0].text
                else:
                    return etree.tostring(nodes[0], encoding='unicode')
            return None
        except ImportError:
            logger.warning("lxml library not installed, XPath extraction not available")
            return None
        except Exception as e:
            logger.error(f"Error extracting with XPath {xpath}: {str(e)}")
            return None

    def _extract_css_selector(self, source: Any, selector: str) -> Optional[str]:
        """
        使用CSS选择器提取数据（需要BeautifulSoup库）

        Args:
            source: 源数据（HTML字符串）
            selector: CSS选择器

        Returns:
            Optional[str]: 提取的值
        """
        if source is None:
            return None

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(str(source), 'html.parser')
            elements = soup.select(selector)

            if elements:
                return elements[0].get_text(strip=True)
            return None
        except ImportError:
            logger.warning("BeautifulSoup library not installed, CSS selector extraction not available")
            return None
        except Exception as e:
            logger.error(f"Error extracting with CSS selector {selector}: {str(e)}")
            return None

    def _extract_header(self, http_response: Any, header_name: str) -> Optional[str]:
        """
        从响应头中提取数据

        Args:
            http_response: HTTP响应对象
            header_name: Header名称

        Returns:
            Optional[str]: Header值
        """
        if http_response is None:
            return None

        try:
            headers = dict(http_response.headers)
            return headers.get(header_name)
        except Exception as e:
            logger.error(f"Error extracting header {header_name}: {str(e)}")
            return None

    def _extract_cookie(self, http_response: Any, cookie_name: str) -> Optional[str]:
        """
        从Set-Cookie头中提取Cookie值

        Args:
            http_response: HTTP响应对象
            cookie_name: Cookie名称

        Returns:
            Optional[str]: Cookie值
        """
        if http_response is None:
            return None

        try:
            headers = dict(http_response.headers)
            set_cookie = headers.get('Set-Cookie', '')

            if not set_cookie:
                return None

            # 解析Set-Cookie头
            cookies = {}
            for cookie in set_cookie.split(','):
                # 简单解析，处理 name=value; attributes 格式
                parts = cookie.strip().split(';')
                if parts:
                    name_value = parts[0].split('=', 1)
                    if len(name_value) == 2:
                        cookies[name_value[0].strip()] = name_value[1].strip()

            return cookies.get(cookie_name)
        except Exception as e:
            logger.error(f"Error extracting cookie {cookie_name}: {str(e)}")
            return None

    def get_extraction_examples(self) -> Dict[str, List[Dict[str, str]]]:
        """获取提取表达式示例"""
        return {
            'regex': [
                {
                    'description': '提取JSON中的token字段',
                    'expression': '"token":"([^"]+)"',
                    'example': '{"token":"abc123","user":"test"}'
                },
                {
                    'description': '提取HTML中的链接',
                    'expression': 'href="([^"]+)"',
                    'example': '<a href="https://example.com">Link</a>'
                }
            ],
            'json_path': [
                {
                    'description': '提取JSON中的data.id值',
                    'expression': '$.data.id',
                    'example': '{"data":{"id":123,"name":"test"}}'
                },
                {
                    'description': '提取数组第一项',
                    'expression': '$.users[0].name',
                    'example': '{"users":[{"name":"John"},{"name":"Jane"}]}'
                }
            ],
            'xpath': [
                {
                    'description': '提取HTML中div的文本',
                    'expression': '//div[@class="content"]/text()',
                    'example': '<div class="content">Hello</div>'
                }
            ],
            'css_selector': [
                {
                    'description': '提取CSS选择器匹配的元素',
                    'expression': '.user-name',
                    'example': '<div class="user-name">John Doe</div>'
                }
            ],
            'header': [
                {
                    'description': '提取Authorization头',
                    'expression': 'Authorization',
                    'example': 'Authorization: Bearer token123'
                }
            ],
            'cookie': [
                {
                    'description': '提取session_id cookie',
                    'expression': 'session_id',
                    'example': 'Set-Cookie: session_id=abc123; Path=/; HttpOnly'
                }
            ]
        }
