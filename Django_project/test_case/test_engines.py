# -*- coding: utf-8 -*-
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api_automation.services.assertion_engine import AssertionEngine, AssertionResult
from api_automation.services.extraction_engine import ExtractionEngine, ExtractionResult

class MockResponse:
    """模拟HTTP响应"""
    def __init__(self, status_code=200, headers=None, response_time=500):
        self.status_code = status_code
        self.headers = headers or {}
        self.response_time = response_time

def test_assertion_engine():
    """测试断言引擎"""
    print("=" * 50)
    print("Testing Assertion Engine")
    print("=" * 50)

    engine = AssertionEngine()

    # 模拟HTTP响应
    mock_response = MockResponse(
        status_code=200,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer token123'},
        response_time=500
    )

    # 模拟响应体
    response_body = {
        'code': 200,
        'message': 'success',
        'data': {
            'id': 123,
            'name': 'Test User',
            'token': 'abc123def456'
        }
    }

    # 测试状态码断言
    print("\n=== Test Status Code Assertion ===")
    assertions = [
        {'type': 'status_code', 'expected': 200, 'operator': 'equals'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Message: {results[0].message}")
    assert all_passed == True

    # 测试响应时间断言
    print("\n=== Test Response Time Assertion ===")
    assertions = [
        {'type': 'response_time', 'expected': 1000, 'operator': 'less_than'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Message: {results[0].message}")
    assert all_passed == True

    # 测试响应体断言
    print("\n=== Test Response Body Assertion ===")
    assertions = [
        {'type': 'response_body', 'expected': 'success', 'operator': 'contains'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Message: {results[0].message}")
    assert all_passed == True

    # 测试JSON值断言
    print("\n=== Test JSON Value Assertion ===")
    assertions = [
        {'type': 'json_value', 'json_path': '$.data.id', 'expected': 123, 'operator': 'equals'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Actual: {results[0].actual}, Expected: {results[0].expected}")
    assert all_passed == True

    # 测试响应头断言
    print("\n=== Test Response Header Assertion ===")
    assertions = [
        {'type': 'response_header', 'source': 'Content-Type', 'expected': 'application/json', 'operator': 'contains'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Message: {results[0].message}")
    assert all_passed == True

    # 测试断言失败场景
    print("\n=== Test Assertion Failure ===")
    assertions = [
        {'type': 'status_code', 'expected': 404, 'operator': 'equals'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"Results: {results[0].passed}, Actual: {results[0].actual}, Expected: {results[0].expected}")
    assert all_passed == False

    # 测试多个断言
    print("\n=== Test Multiple Assertions ===")
    assertions = [
        {'type': 'status_code', 'expected': 200, 'operator': 'equals'},
        {'type': 'response_time', 'expected': 1000, 'operator': 'less_than'},
        {'type': 'json_value', 'json_path': '$.data.id', 'expected': 123, 'operator': 'equals'}
    ]
    results, all_passed = engine.evaluate_assertions(assertions, mock_response, response_body)
    print(f"All passed: {all_passed}, Count: {len(results)}")
    assert all_passed == True
    assert len(results) == 3

    print("\n=== Assertion Engine Tests PASSED ===")
    return True

def test_extraction_engine():
    """测试数据提取引擎"""
    print("\n" + "=" * 50)
    print("Testing Extraction Engine")
    print("=" * 50)

    engine = ExtractionEngine()

    # 模拟HTTP响应
    mock_response = MockResponse(
        status_code=200,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer token123'},
        response_time=500
    )

    # 模拟响应体
    response_body = {
        'code': 200,
        'message': 'success',
        'data': {
            'id': 123,
            'name': 'Test User',
            'token': 'abc123def456'
        }
    }

    response_text = '{"code":200,"message":"success","data":{"id":123,"name":"Test User","token":"abc123def456"}}'

    # 测试正则表达式提取
    print("\n=== Test Regex Extraction ===")
    extractions = [
        {'variable_name': 'token', 'extract_type': 'regex', 'extract_expression': '"token"\\s*:\\s*"([^"]+)"',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True}
    ]
    variables, results = engine.extract_variables(extractions, mock_response, response_body, response_text)
    print(f"Extracted: token={variables.get('token')}, Result: {results[0].success}")
    assert variables.get('token') == 'abc123def456'

    # 测试JSON路径提取
    print("\n=== Test JSON Path Extraction ===")
    extractions = [
        {'variable_name': 'user_id', 'extract_type': 'json_path', 'extract_expression': '$.data.id',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True}
    ]
    variables, results = engine.extract_variables(extractions, mock_response, response_body, response_text)
    print(f"Extracted: user_id={variables.get('user_id')}, Result: {results[0].success}")
    assert variables.get('user_id') == 123

    # 测试Header提取
    print("\n=== Test Header Extraction ===")
    extractions = [
        {'variable_name': 'auth_token', 'extract_type': 'header', 'extract_expression': 'Authorization',
         'default_value': None, 'extract_scope': 'headers', 'is_enabled': True}
    ]
    variables, results = engine.extract_variables(extractions, mock_response, response_body, response_text)
    print(f"Extracted: auth_token={variables.get('auth_token')}, Result: {results[0].success}")
    assert variables.get('auth_token') == 'Bearer token123'

    # 测试提取失败使用默认值
    print("\n=== Test Extraction with Default Value ===")
    extractions = [
        {'variable_name': 'fallback', 'extract_type': 'json_path', 'extract_expression': '$.nonexistent',
         'default_value': 'default_value', 'extract_scope': 'body', 'is_enabled': True}
    ]
    variables, results = engine.extract_variables(extractions, mock_response, response_body, response_text)
    print(f"Extracted: fallback={variables.get('fallback')}, Result: {results[0].success}")
    assert variables.get('fallback') == 'default_value'

    # 测试多个变量提取
    print("\n=== Test Multiple Extractions ===")
    extractions = [
        {'variable_name': 'user_id', 'extract_type': 'json_path', 'extract_expression': '$.data.id',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True},
        {'variable_name': 'token', 'extract_type': 'regex', 'extract_expression': '"token"\\s*:\\s*"([^"]+)"',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True},
        {'variable_name': 'content_type', 'extract_type': 'header', 'extract_expression': 'Content-Type',
         'default_value': None, 'extract_scope': 'headers', 'is_enabled': True}
    ]
    variables, results = engine.extract_variables(extractions, mock_response, response_body, response_text)
    print(f"Extracted {len(variables)} variables: {list(variables.keys())}")
    assert len(variables) == 3
    assert variables.get('user_id') == 123
    assert variables.get('token') == 'abc123def456'
    assert variables.get('content_type') == 'application/json'

    print("\n=== Extraction Engine Tests PASSED ===")
    return True

def test_integration_scenario():
    """测试综合场景：登录接口完整测试"""
    print("\n" + "=" * 50)
    print("Testing Integration Scenario - Login API")
    print("=" * 50)

    assertion_engine = AssertionEngine()
    extraction_engine = ExtractionEngine()

    # 模拟登录API响应
    mock_response = MockResponse(
        status_code=200,
        headers={'Content-Type': 'application/json'},
        response_time=300
    )

    response_body = {
        'code': 200,
        'message': 'success',
        'data': {
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123',
            'user': {
                'id': 456,
                'username': 'testuser'
            }
        }
    }

    response_text = '{"code":200,"message":"success","data":{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123","user":{"id":456,"username":"testuser"}}}'

    # 配置断言
    assertions = [
        {'type': 'status_code', 'expected': 200, 'operator': 'equals'},
        {'type': 'response_time', 'expected': 1000, 'operator': 'less_than'},
        {'type': 'response_body', 'expected': 'token', 'operator': 'contains'}
    ]

    # 配置数据提取
    extractions = [
        {'variable_name': 'token', 'extract_type': 'json_path', 'extract_expression': '$.data.token',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True},
        {'variable_name': 'user_id', 'extract_type': 'json_path', 'extract_expression': '$.data.user.id',
         'default_value': None, 'extract_scope': 'body', 'is_enabled': True}
    ]

    # 执行断言验证
    print("\n=== Executing Assertions ===")
    assertion_results, all_assertions_passed = assertion_engine.evaluate_assertions(
        assertions, mock_response, response_body
    )

    for result in assertion_results:
        print(f"  {result.assertion_type}: {result.passed} - {result.message}")

    assert all_assertions_passed == True

    # 执行数据提取
    print("\n=== Executing Extractions ===")
    extracted_vars, extraction_results = extraction_engine.extract_variables(
        extractions, mock_response, response_body, response_text
    )

    for result in extraction_results:
        print(f"  {result.variable_name}: {result.value} ({'success' if result.success else 'failed'})")

    assert extracted_vars.get('token') == 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123'
    assert extracted_vars.get('user_id') == 456

    print("\n=== Integration Scenario Test PASSED ===")
    print("Summary:")
    print(f"  - All {len(assertion_results)} assertions passed")
    print(f"  - {len(extracted_vars)} variables extracted successfully")
    print("  - Can use extracted variables in subsequent requests")

    return True

def run_all_engine_tests():
    """运行所有引擎测试"""
    print("\n" + "=" * 50)
    print("Starting Engine Integration Tests")
    print("=" * 50)

    tests = [
        test_assertion_engine,
        test_extraction_engine,
        test_integration_scenario
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"Engine Test Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0

if __name__ == '__main__':
    success = run_all_engine_tests()
    sys.exit(0 if success else 1)
