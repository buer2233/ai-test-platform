"""
断言引擎

负责验证HTTP响应是否符合预期条件。
支持多种断言类型：状态码、响应时间、响应体、响应头、JSON值、
文本包含、JSON Schema等，以及丰富的比较操作符。
"""

import json
import logging
import operator
import re
from typing import Any, Dict, List, Tuple, Union

logger = logging.getLogger(__name__)


class AssertionResult:
    """
    单条断言的执行结果

    记录断言类型、期望值、实际值、是否通过及描述信息，
    用于汇总展示和存储。
    """

    def __init__(
        self,
        assertion_type: str,
        expected: Any,
        actual: Any,
        passed: bool,
        message: str = ""
    ):
        self.assertion_type = assertion_type  # 断言类型（如 status_code, json_value）
        self.expected = expected              # 期望值
        self.actual = actual                  # 实际值
        self.passed = passed                  # 是否通过
        self.message = message                # 可读的结果描述

    def to_dict(self) -> Dict[str, Any]:
        """将断言结果序列化为字典格式，用于API返回和存储"""
        return {
            'type': self.assertion_type,
            'expected': self.expected,
            'actual': self.actual,
            'passed': self.passed,
            'message': self.message
        }


class AssertionEngine:
    """
    断言引擎

    根据断言配置列表逐条评估HTTP响应，返回每条断言的通过/失败结果。
    支持16种比较操作符和7种断言类型。
    """

    # 支持的比较操作符映射表
    OPERATORS = {
        'equals': operator.eq,
        'not_equals': operator.ne,
        'greater_than': operator.gt,
        'less_than': operator.lt,
        'greater_equal': operator.ge,
        'less_equal': operator.le,
        'contains': lambda x, y: y in x,
        'not_contains': lambda x, y: y not in x,
        'starts_with': lambda x, y: str(x).startswith(str(y)),
        'ends_with': lambda x, y: str(x).endswith(str(y)),
        'matches': lambda x, y: bool(re.search(str(y), str(x))),
        'exists': lambda x, y: x is not None,
        'not_exists': lambda x, y: x is None,
        'is_empty': lambda x, y: not x,
        'is_not_empty': lambda x, y: bool(x),
    }

    def __init__(self):
        self.operators = self.OPERATORS

    def evaluate_assertions(
        self,
        assertions: List[Dict[str, Any]],
        http_response: Any,
        response_body: Any = None
    ) -> Tuple[List[AssertionResult], bool]:
        """
        批量执行断言列表

        遍历所有断言配置，逐条评估并收集结果。
        任意一条断言失败即标记整体不通过。

        Args:
            assertions: 断言配置列表，每项包含 type/expected/operator 等字段
            http_response: HTTP响应对象（包含status_code, headers等属性）
            response_body: 已解析的响应体数据

        Returns:
            (断言结果列表, 是否全部通过)
        """
        results = []
        all_passed = True

        for assertion in assertions:
            try:
                result = self._evaluate_single_assertion(
                    assertion, http_response, response_body
                )
                results.append(result)
                if not result.passed:
                    all_passed = False
            except Exception as e:
                logger.error(f"Error evaluating assertion: {assertion} - {str(e)}")
                results.append(AssertionResult(
                    assertion_type=assertion.get('type', 'unknown'),
                    expected=assertion.get('expected'),
                    actual='ERROR',
                    passed=False,
                    message=f"断言执行错误: {str(e)}"
                ))
                all_passed = False

        return results, all_passed

    def _evaluate_single_assertion(
        self,
        assertion: Dict[str, Any],
        http_response: Any,
        response_body: Any
    ) -> AssertionResult:
        """
        执行单条断言

        根据断言类型提取实际值，再调用对应的断言方法进行比较。

        Args:
            assertion: 断言配置字典
            http_response: HTTP响应对象
            response_body: 响应体数据

        Returns:
            AssertionResult: 断言结果
        """
        assertion_type = assertion.get('type', '')
        expected = assertion.get('expected')
        operator_name = assertion.get('operator', 'equals')
        source = assertion.get('source', '')
        json_path = assertion.get('json_path', '')

        # 从响应中提取断言所需的实际值
        actual = self._extract_value(
            assertion_type, http_response, response_body, source, json_path
        )

        # 根据断言类型分派到具体的断言方法
        assertion_handlers = {
            'status_code': lambda: self._assert_status_code(expected, actual),
            'response_time': lambda: self._assert_response_time(
                expected, actual, operator_name
            ),
            'response_body': lambda: self._assert_response_body(
                expected, actual, operator_name, json_path
            ),
            'response_header': lambda: self._assert_response_header(
                expected, actual, operator_name, source
            ),
            'json_value': lambda: self._assert_json_value(
                expected, actual, operator_name, json_path
            ),
            'text_contains': lambda: self._assert_text_contains(expected, actual),
            'json_schema': lambda: self._assert_json_schema(expected, actual),
        }

        handler = assertion_handlers.get(assertion_type)
        if handler:
            return handler()

        return AssertionResult(
            assertion_type=assertion_type,
            expected=expected,
            actual=actual,
            passed=False,
            message=f"不支持的断言类型: {assertion_type}"
        )

    def _extract_value(
        self,
        assertion_type: str,
        http_response: Any,
        response_body: Any,
        source: str,
        json_path: str
    ) -> Any:
        """
        根据断言类型从HTTP响应中提取实际值

        不同断言类型需要从响应的不同部分提取值：
        - status_code: 从响应对象获取状态码
        - response_time: 从响应对象获取耗时
        - response_body/text_contains/json_schema: 使用完整响应体
        - response_header: 从响应头中按名称提取
        - json_value: 从响应体中按JSON路径提取

        Args:
            assertion_type: 断言类型
            http_response: HTTP响应对象
            response_body: 已解析的响应体
            source: 源字段名（用于响应头断言）
            json_path: JSON路径表达式

        Returns:
            提取到的值，失败时返回None
        """
        try:
            if assertion_type == 'status_code':
                return http_response.status_code
            elif assertion_type == 'response_time':
                return getattr(http_response, 'response_time', 0)
            elif assertion_type in ('response_body', 'text_contains', 'json_schema'):
                return response_body
            elif assertion_type == 'response_header':
                if source:
                    return http_response.headers.get(source, '')
                return http_response.headers
            elif assertion_type == 'json_value':
                return self._extract_json_value(response_body, json_path)
            return None
        except Exception as e:
            logger.error(
                f"Error extracting value for assertion {assertion_type}: {str(e)}"
            )
            return None

    def _extract_json_value(self, data: Any, json_path: str) -> Any:
        """
        从JSON数据中按路径提取指定值

        支持点号分隔的对象属性访问和方括号数组索引访问。
        例如: "data.user.name"、"users[0].id"

        Args:
            data: 已解析的JSON数据（dict或list）
            json_path: JSON路径表达式

        Returns:
            路径指向的值，路径无效时返回None
        """
        if not json_path or not data:
            return data

        try:
            current = data
            path_parts = self._parse_json_path(json_path)

            for part in path_parts:
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

                if current is None:
                    return None

            return current
        except Exception as e:
            logger.error(
                f"Error extracting JSON value from path {json_path}: {str(e)}"
            )
            return None

    def _parse_json_path(self, json_path: str) -> List[str]:
        """
        解析JSON路径表达式为路径片段列表

        处理规则：
        - 去除 "$." 前缀（如果存在）
        - 以点号 "." 分隔对象属性
        - 以方括号 "[n]" 分隔数组索引

        示例: "$.data.users[0].name" -> ["data", "users", "0", "name"]

        Args:
            json_path: JSON路径字符串

        Returns:
            路径片段列表
        """
        # 去除 $. 前缀
        if json_path.startswith('$.'):
            json_path = json_path[2:]

        parts = []
        current_part = ""
        in_brackets = False

        for char in json_path:
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

    def _assert_status_code(
        self,
        expected: Union[int, List[int]],
        actual: int
    ) -> AssertionResult:
        """
        断言HTTP状态码

        支持单个状态码精确匹配和状态码列表范围匹配。

        Args:
            expected: 期望的状态码（单个整数或整数列表）
            actual: 实际的状态码

        Returns:
            AssertionResult: 断言结果
        """
        if isinstance(expected, list):
            passed = actual in expected
            message = f"状态码 {actual} 是否在期望列表 {expected} 中"
        else:
            passed = actual == expected
            message = f"状态码应为 {expected}，实际为 {actual}"

        return AssertionResult('status_code', expected, actual, passed, message)

    def _assert_response_time(
        self,
        expected: Union[int, Dict[str, Any]],
        actual: int,
        operator_name: str
    ) -> AssertionResult:
        """
        断言响应时间

        expected可以是简单整数（毫秒），也可以是包含operator和value的字典。
        默认使用 less_equal 操作符（响应时间不超过阈值）。

        Args:
            expected: 期望的响应时间阈值
            actual: 实际的响应时间（毫秒）
            operator_name: 比较操作符名称

        Returns:
            AssertionResult: 断言结果
        """
        if isinstance(expected, dict):
            operator_name = expected.get('operator', 'less_equal')
            value = expected.get('value', 0)
        else:
            value = expected

        if operator_name in self.operators:
            passed = self.operators[operator_name](actual, value)
        else:
            passed = actual <= value
            operator_name = 'less_equal'

        message = f"响应时间 {actual}ms {operator_name} {value}ms"
        return AssertionResult('response_time', value, actual, passed, message)

    def _assert_response_body(
        self,
        expected: Any,
        actual: Any,
        operator_name: str,
        json_path: str
    ) -> AssertionResult:
        """
        断言响应体内容

        当指定json_path时，先从响应体中提取目标值再进行比较。
        contains/not_contains操作符会将复杂对象序列化为字符串后匹配。

        Args:
            expected: 期望值
            actual: 实际的响应体数据
            operator_name: 比较操作符
            json_path: 可选的JSON路径（进一步定位）

        Returns:
            AssertionResult: 断言结果
        """
        if json_path:
            actual = self._extract_json_value(actual, json_path)

        # contains/not_contains 需要将复杂对象转为字符串后匹配
        if operator_name in ('contains', 'not_contains'):
            if isinstance(actual, (dict, list)):
                actual_str = json.dumps(actual, ensure_ascii=False)
            else:
                actual_str = str(actual)

            if operator_name == 'contains':
                passed = expected in actual_str
            else:
                passed = expected not in actual_str
        elif operator_name in self.operators:
            passed = self.operators[operator_name](actual, expected)
        else:
            passed = str(actual) == str(expected)

        path_display = json_path or '根节点'
        message = f"响应体路径 {path_display} 的值 {actual} {operator_name} {expected}"
        return AssertionResult('response_body', expected, actual, passed, message)

    def _assert_response_header(
        self,
        expected: Any,
        actual: Any,
        operator_name: str,
        header_name: str
    ) -> AssertionResult:
        """
        断言响应头字段值

        Args:
            expected: 期望的响应头值
            actual: 实际的响应头值
            operator_name: 比较操作符
            header_name: 响应头字段名

        Returns:
            AssertionResult: 断言结果
        """
        if operator_name in self.operators:
            passed = self.operators[operator_name](actual, expected)
        else:
            passed = str(actual) == str(expected)

        message = f"响应头 {header_name}: {actual} {operator_name} {expected}"
        return AssertionResult('response_header', expected, actual, passed, message)

    def _assert_json_value(
        self,
        expected: Any,
        actual: Any,
        operator_name: str,
        json_path: str
    ) -> AssertionResult:
        """
        断言JSON路径指向的值

        Args:
            expected: 期望值
            actual: 通过JSON路径提取的实际值
            operator_name: 比较操作符
            json_path: JSON路径表达式

        Returns:
            AssertionResult: 断言结果
        """
        if operator_name in self.operators:
            passed = self.operators[operator_name](actual, expected)
        else:
            passed = str(actual) == str(expected)

        message = f"JSON路径 {json_path} 的值 {actual} {operator_name} {expected}"
        return AssertionResult('json_value', expected, actual, passed, message)

    def _assert_text_contains(self, expected: str, actual: Any) -> AssertionResult:
        """
        断言响应文本是否包含指定内容

        Args:
            expected: 期望包含的文本
            actual: 实际的响应内容

        Returns:
            AssertionResult: 断言结果
        """
        actual_text = str(actual) if actual is not None else ""
        passed = expected in actual_text
        message = f"响应文本 '{actual_text}' 包含 '{expected}'"
        return AssertionResult('text_contains', expected, actual, passed, message)

    def _assert_json_schema(
        self,
        expected: Dict[str, Any],
        actual: Any
    ) -> AssertionResult:
        """
        断言响应体符合JSON Schema规范

        当前实现为简化版Schema验证，仅检查required字段是否存在，
        并递归验证嵌套的object类型属性。

        Args:
            expected: JSON Schema定义（包含required和properties）
            actual: 实际的响应体数据

        Returns:
            AssertionResult: 断言结果
        """
        try:
            passed = True
            missing_fields = []

            def check_schema(schema: Dict[str, Any], data: Any, path: str = ""):
                """递归检查Schema，收集缺失的必填字段"""
                nonlocal passed, missing_fields

                if not isinstance(data, dict):
                    return

                # 检查required中声明的必填字段
                for field in schema.get('required', []):
                    if field not in data:
                        passed = False
                        field_path = f"{path}.{field}" if path else field
                        missing_fields.append(field_path)

                # 递归检查嵌套的object类型属性
                for field, field_schema in schema.get('properties', {}).items():
                    if (
                        field in data
                        and isinstance(field_schema, dict)
                        and field_schema.get('type') == 'object'
                    ):
                        field_path = f"{path}.{field}" if path else field
                        check_schema(field_schema, data[field], field_path)

            check_schema(expected, actual)

            if passed:
                message = "JSON Schema验证通过"
            else:
                message = f"JSON Schema验证失败，缺少字段: {', '.join(missing_fields)}"

        except Exception as e:
            passed = False
            message = f"JSON Schema验证错误: {str(e)}"

        return AssertionResult('json_schema', expected, actual, passed, message)

    def get_default_assertions(self) -> List[Dict[str, Any]]:
        """
        获取默认断言配置

        新建测试用例时可使用此默认配置作为初始断言：
        1. 检查HTTP状态码是否为200
        2. 检查响应时间是否不超过5000ms

        Returns:
            默认断言配置列表
        """
        return [
            {
                'type': 'status_code',
                'expected': 200,
                'operator': 'equals',
                'enabled': True,
                'description': '检查HTTP状态码是否为200'
            },
            {
                'type': 'response_time',
                'expected': {'value': 5000, 'operator': 'less_equal'},
                'operator': 'less_equal',
                'enabled': True,
                'description': '检查响应时间是否小于等于5000ms'
            }
        ]