"""
数据提取引擎

负责从HTTP响应中提取变量值，供后续测试用例使用。
支持6种提取方式：正则表达式、JSONPath、XPath、CSS选择器、响应头、Cookie。
提取的变量会通过WebSocket实时广播给前端。
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

# 尝试导入WebSocket服务（非必须依赖，不可用时静默降级）
try:
    from .websocket_service import websocket_service
    WEBSOCKET_ENABLED = True
except ImportError:
    WEBSOCKET_ENABLED = False
    websocket_service = None


class ExtractionResult:
    """
    单次变量提取的结果

    记录变量名、提取到的值、是否成功及描述信息。
    """

    def __init__(
        self,
        variable_name: str,
        value: Any,
        success: bool,
        message: str = ""
    ):
        self.variable_name = variable_name  # 变量名
        self.value = value                  # 提取到的值
        self.success = success              # 是否提取成功
        self.message = message              # 结果描述

    def to_dict(self) -> Dict[str, Any]:
        """将提取结果序列化为字典格式"""
        return {
            'variable_name': self.variable_name,
            'value': self.value,
            'success': self.success,
            'message': self.message
        }


class ExtractionEngine:
    """
    数据提取引擎

    根据提取配置列表，从HTTP响应的不同部分（响应体、响应头、URL等）
    中提取变量值。支持6种提取方式，提取结果可通过WebSocket实时推送。
    """

    # 支持的提取方式到处理方法的映射（在_extract_single_variable中使用）
    EXTRACT_TYPE_HANDLERS = {
        'regex', 'json_path', 'xpath', 'css_selector', 'header', 'cookie'
    }

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
        批量执行变量提取

        遍历提取配置列表，逐条执行提取操作并收集结果。
        提取成功的变量会加入返回的变量字典，失败时使用默认值（如果有）。
        每次提取结果都会通过WebSocket广播（如果可用）。

        Args:
            extractions: 提取配置列表
            http_response: HTTP响应对象
            response_body: 已解析的响应体数据
            response_text: 原始响应文本
            execution_id: 执行ID（用于WebSocket广播标识）
            test_case_id: 测试用例ID（用于WebSocket广播标识）

        Returns:
            (提取到的变量字典, 提取结果列表)
        """
        variables = {}
        results = []

        for extraction in extractions:
            # 跳过已禁用的提取配置
            if not extraction.get('is_enabled', True):
                continue

            try:
                result = self._extract_single_variable(
                    extraction, http_response, response_body, response_text
                )
                results.append(result)

                # 通过WebSocket广播提取结果
                if WEBSOCKET_ENABLED and execution_id:
                    self._broadcast_variable_extracted(
                        execution_id, test_case_id, result
                    )

                if result.success:
                    variables[result.variable_name] = result.value

            except Exception as e:
                logger.error(
                    f"Error extracting variable: {extraction} - {str(e)}"
                )
                # 提取异常时使用默认值
                var_name = extraction.get('variable_name', 'unknown')
                default_value = extraction.get('default_value')
                error_result = ExtractionResult(
                    variable_name=var_name,
                    value=default_value,
                    success=False,
                    message=f"提取失败，使用默认值: {str(e)}"
                )
                results.append(error_result)

                if WEBSOCKET_ENABLED and execution_id:
                    self._broadcast_variable_extracted(
                        execution_id, test_case_id, error_result
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
        通过WebSocket广播变量提取结果

        Args:
            execution_id: 执行ID
            test_case_id: 测试用例ID
            result: 提取结果对象
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

        根据提取类型（regex/json_path/xpath/css_selector/header/cookie）
        调用对应的提取方法。提取失败时尝试使用默认值。

        Args:
            extraction: 提取配置字典
            http_response: HTTP响应对象
            response_body: 已解析的响应体
            response_text: 原始响应文本

        Returns:
            ExtractionResult: 提取结果
        """
        variable_name = extraction.get('variable_name', '')
        extract_type = extraction.get('extract_type', '')
        extract_expression = extraction.get('extract_expression', '')
        extract_scope = extraction.get('extract_scope', 'body')
        default_value = extraction.get('default_value')

        # 根据提取范围确定数据源
        source_data = self._get_source_data(
            extract_scope, http_response, response_body, response_text
        )

        # 根据提取类型分派到对应方法
        type_to_handler = {
            'regex': lambda: self._extract_regex(source_data, extract_expression),
            'json_path': lambda: self._extract_json_path(source_data, extract_expression),
            'xpath': lambda: self._extract_xpath(source_data, extract_expression),
            'css_selector': lambda: self._extract_css_selector(source_data, extract_expression),
            'header': lambda: self._extract_header(http_response, extract_expression),
            'cookie': lambda: self._extract_cookie(http_response, extract_expression),
        }

        handler = type_to_handler.get(extract_type)
        if not handler:
            return ExtractionResult(
                variable_name=variable_name,
                value=default_value,
                success=False,
                message=f"不支持的提取类型: {extract_type}"
            )

        value = handler()

        # 提取结果为空时尝试使用默认值
        if value is None or value == '':
            if default_value is not None:
                return ExtractionResult(
                    variable_name=variable_name,
                    value=default_value,
                    success=True,
                    message="提取失败，使用默认值"
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
        """
        根据提取范围获取数据源

        - headers: 返回响应头字典
        - url: 返回请求URL字符串
        - body(默认): 返回响应体（优先使用已解析的数据）

        Args:
            scope: 提取范围（headers/url/body）
            http_response: HTTP响应对象
            response_body: 已解析的响应体
            response_text: 原始响应文本

        Returns:
            对应范围的数据
        """
        if scope == 'headers':
            return dict(http_response.headers) if http_response else {}
        elif scope == 'url':
            return getattr(http_response, 'url', '') if http_response else ''
        # 默认为body范围
        if response_body is not None:
            if isinstance(response_body, (dict, list)):
                return json.dumps(response_body, ensure_ascii=False)
            return response_body
        return response_text

    def _extract_regex(self, source: Any, pattern: str) -> Optional[str]:
        """
        使用正则表达式从文本中提取数据

        如果正则包含捕获组，返回第一个捕获组的内容；
        否则返回整个匹配的内容。使用 IGNORECASE 标志提高匹配成功率。

        Args:
            source: 源数据（将被转为字符串）
            pattern: 正则表达式模式

        Returns:
            匹配到的字符串，无匹配时返回None
        """
        if source is None:
            return None

        text = str(source)
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # 优先返回第一个捕获组
                return match.group(1) if match.groups() else match.group(0)
            return None
        except re.error as e:
            logger.error(f"Invalid regex pattern {pattern}: {str(e)}")
            return None

    def _extract_json_path(self, source: Any, json_path: str) -> Optional[Any]:
        """
        使用JSONPath表达式从数据中提取值

        支持 $.key.subkey[0].field 格式的路径表达式。
        source可以是dict/list或JSON字符串（会自动解析）。

        Args:
            source: 源数据
            json_path: JSONPath表达式（如 $.data.user.id）

        Returns:
            提取到的值，路径无效时返回None
        """
        if source is None:
            return None

        # 如果source是字符串，先尝试解析为JSON
        if isinstance(source, str):
            try:
                source = json.loads(source)
            except json.JSONDecodeError:
                return None

        if not isinstance(source, (dict, list)):
            return None

        # 去除 $. 前缀
        path = json_path[2:] if json_path.startswith('$.') else json_path
        return self._navigate_json_path(source, path)

    def _navigate_json_path(self, data: Any, path: str) -> Optional[Any]:
        """
        沿JSON路径逐级导航到目标值

        Args:
            data: JSON数据（dict或list）
            path: 路径字符串（不含$.前缀）

        Returns:
            路径指向的值
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
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
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
        解析JSON路径为路径片段列表

        将 "data.users[0].name" 解析为 ["data", "users", "0", "name"]

        Args:
            path: JSON路径字符串

        Returns:
            路径片段列表
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
        使用XPath表达式从HTML/XML中提取数据

        依赖lxml库，如未安装则返回None并记录警告。

        Args:
            source: HTML/XML源文本
            xpath: XPath表达式

        Returns:
            提取到的文本内容
        """
        if source is None:
            return None

        try:
            from lxml import etree
            from io import StringIO

            tree = etree.parse(StringIO(str(source)), etree.HTMLParser())
            nodes = tree.xpath(xpath)

            if not nodes:
                return None

            if isinstance(nodes[0], str):
                return ''.join(nodes)
            elif hasattr(nodes[0], 'text'):
                return nodes[0].text
            return etree.tostring(nodes[0], encoding='unicode')

        except ImportError:
            logger.warning("lxml库未安装，XPath提取不可用")
            return None
        except Exception as e:
            logger.error(f"Error extracting with XPath {xpath}: {str(e)}")
            return None

    def _extract_css_selector(self, source: Any, selector: str) -> Optional[str]:
        """
        使用CSS选择器从HTML中提取数据

        依赖BeautifulSoup库，如未安装则返回None并记录警告。

        Args:
            source: HTML源文本
            selector: CSS选择器表达式

        Returns:
            匹配元素的文本内容
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
            logger.warning("BeautifulSoup库未安装，CSS选择器提取不可用")
            return None
        except Exception as e:
            logger.error(
                f"Error extracting with CSS selector {selector}: {str(e)}"
            )
            return None

    def _extract_header(self, http_response: Any, header_name: str) -> Optional[str]:
        """
        从HTTP响应头中提取指定字段的值

        Args:
            http_response: HTTP响应对象
            header_name: 响应头字段名

        Returns:
            对应响应头的值
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
        从Set-Cookie响应头中提取指定Cookie的值

        简单解析Set-Cookie头，提取 name=value 部分。
        注意：仅支持基本格式，复杂Cookie场景可能需要扩展。

        Args:
            http_response: HTTP响应对象
            cookie_name: Cookie名称

        Returns:
            对应Cookie的值
        """
        if http_response is None:
            return None

        try:
            headers = dict(http_response.headers)
            set_cookie = headers.get('Set-Cookie', '')

            if not set_cookie:
                return None

            # 解析 "name=value; attr1; attr2" 格式的Cookie
            cookies = {}
            for cookie in set_cookie.split(','):
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
        """
        获取各提取方式的表达式示例

        为前端用户提供参考，展示每种提取方式的用法和预期效果。

        Returns:
            按提取类型分组的示例列表
        """
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
