"""
断言引擎
负责验证HTTP响应是否符合预期
"""

import json
import re
import operator
from typing import Dict, Any, List, Union, Tuple
import logging

logger = logging.getLogger(__name__)


class AssertionResult:
    """断言结果"""

    def __init__(self, assertion_type: str, expected: Any, actual: Any, passed: bool, message: str = ""):
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
        self.passed = passed
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'type': self.assertion_type,
            'expected': self.expected,
            'actual': self.actual,
            'passed': self.passed,
            'message': self.message
        }


class AssertionEngine:
    """断言引擎"""

    def __init__(self):
        # 支持的断言操作符
        self.operators = {
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
            'is_not_empty': lambda x, y: bool(x)
        }

    def evaluate_assertions(
        self,
        assertions: List[Dict[str, Any]],
        http_response: Any,
        response_body: Any = None
    ) -> Tuple[List[AssertionResult], bool]:
        """
        执行断言列表

        Args:
            assertions: 断言配置列表
            http_response: HTTP响应对象
            response_body: 响应体数据

        Returns:
            Tuple[List[AssertionResult], bool]: 断言结果列表和整体是否通过
        """
        results = []
        all_passed = True

        for assertion in assertions:
            try:
                result = self._evaluate_single_assertion(assertion, http_response, response_body)
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
        执行单个断言

        Args:
            assertion: 断言配置
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

        # 根据断言类型获取实际值
        actual = self._extract_value(assertion_type, http_response, response_body, source, json_path)

        # 执行断言
        if assertion_type == 'status_code':
            result = self._assert_status_code(expected, actual)
        elif assertion_type == 'response_time':
            result = self._assert_response_time(expected, actual, operator_name)
        elif assertion_type == 'response_body':
            result = self._assert_response_body(expected, actual, operator_name, json_path)
        elif assertion_type == 'response_header':
            result = self._assert_response_header(expected, actual, operator_name, source)
        elif assertion_type == 'json_value':
            result = self._assert_json_value(expected, actual, operator_name, json_path)
        elif assertion_type == 'text_contains':
            result = self._assert_text_contains(expected, actual)
        elif assertion_type == 'json_schema':
            result = self._assert_json_schema(expected, actual)
        else:
            result = AssertionResult(
                assertion_type=assertion_type,
                expected=expected,
                actual=actual,
                passed=False,
                message=f"不支持的断言类型: {assertion_type}"
            )

        return result

    def _extract_value(
        self,
        assertion_type: str,
        http_response: Any,
        response_body: Any,
        source: str,
        json_path: str
    ) -> Any:
        """从响应中提取断言所需的值"""
        try:
            if assertion_type in ['status_code']:
                return http_response.status_code
            elif assertion_type in ['response_time']:
                return getattr(http_response, 'response_time', 0)
            elif assertion_type in ['response_body', 'text_contains', 'json_schema']:
                return response_body
            elif assertion_type == 'response_header':
                if source:
                    return http_response.headers.get(source, '')
                return http_response.headers
            elif assertion_type == 'json_value':
                return self._extract_json_value(response_body, json_path)
            else:
                return None
        except Exception as e:
            logger.error(f"Error extracting value for assertion {assertion_type}: {str(e)}")
            return None

    def _extract_json_value(self, data: Any, json_path: str) -> Any:
        """
        从JSON数据中提取指定路径的值

        Args:
            data: JSON数据
            json_path: JSON路径，如 "data.user.name" 或 "users[0].id"

        Returns:
            Any: 提取的值
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
            logger.error(f"Error extracting JSON value from path {json_path}: {str(e)}")
            return None

    def _parse_json_path(self, json_path: str) -> List[str]:
        """
        解析JSON路径

        Args:
            json_path: JSON路径字符串

        Returns:
            List[str]: 路径部分列表
        """
        # 处理 $. 前缀
        if json_path.startswith('$.'):
            json_path = json_path[2:]

        # 简单的JSON路径解析，支持点号分隔的路径和数组索引
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

    def _assert_status_code(self, expected: Union[int, List[int]], actual: int) -> AssertionResult:
        """断言状态码"""
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
        """断言响应时间"""
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
        """断言响应体"""
        if json_path:
            actual = self._extract_json_value(actual, json_path)

        # 处理 contains 操作符，需要将 actual 转换为字符串
        if operator_name == 'contains':
            if isinstance(actual, (dict, list)):
                actual_str = json.dumps(actual, ensure_ascii=False)
            else:
                actual_str = str(actual)
            passed = expected in actual_str
        elif operator_name == 'not_contains':
            if isinstance(actual, (dict, list)):
                actual_str = json.dumps(actual, ensure_ascii=False)
            else:
                actual_str = str(actual)
            passed = expected not in actual_str
        elif operator_name in self.operators:
            passed = self.operators[operator_name](actual, expected)
        else:
            passed = str(actual) == str(expected)

        message = f"响应体路径 {json_path or '根节点'} 的值 {actual} {operator_name} {expected}"

        return AssertionResult('response_body', expected, actual, passed, message)

    def _assert_response_header(
        self,
        expected: Any,
        actual: Any,
        operator_name: str,
        header_name: str
    ) -> AssertionResult:
        """断言响应头"""
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
        """断言JSON值"""
        if operator_name in self.operators:
            passed = self.operators[operator_name](actual, expected)
        else:
            passed = str(actual) == str(expected)

        message = f"JSON路径 {json_path} 的值 {actual} {operator_name} {expected}"

        return AssertionResult('json_value', expected, actual, passed, message)

    def _assert_text_contains(self, expected: str, actual: Any) -> AssertionResult:
        """断言文本包含"""
        actual_text = str(actual) if actual is not None else ""
        passed = expected in actual_text

        message = f"响应文本 '{actual_text}' 包含 '{expected}'"

        return AssertionResult('text_contains', expected, actual, passed, message)

    def _assert_json_schema(self, expected: Dict[str, Any], actual: Any) -> AssertionResult:
        """断言JSON Schema"""
        try:
            # 简单的schema验证，只检查字段是否存在
            passed = True
            missing_fields = []

            def check_schema(schema: Dict[str, Any], data: Any, path: str = ""):
                nonlocal passed, missing_fields

                if not isinstance(data, dict):
                    return

                required_fields = schema.get('required', [])
                properties = schema.get('properties', {})

                # 检查必填字段
                for field in required_fields:
                    if field not in data:
                        passed = False
                        field_path = f"{path}.{field}" if path else field
                        missing_fields.append(field_path)

                # 递归检查嵌套对象
                for field, field_schema in properties.items():
                    if field in data and isinstance(field_schema, dict):
                        if field_schema.get('type') == 'object':
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
        """获取默认断言配置"""
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