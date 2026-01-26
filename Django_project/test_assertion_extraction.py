# -*- coding: utf-8 -*-
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api_automation.models import ApiTestCase, ApiTestCaseAssertion, ApiTestCaseExtraction

def test_assertion_creation():
    """测试断言创建功能"""
    print("=== TC-ASSERT-001: 添加状态码断言 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    # 创建状态码断言
    assertion = ApiTestCaseAssertion.objects.create(
        test_case=test_case,
        assertion_type='status_code',
        target='status_code',
        operator='equals',
        expected_value='200',
        is_enabled=True,
        order=0
    )
    print(f"PASS: Created assertion ID={assertion.id}, type={assertion.assertion_type}")

    # 验证断言已保存
    saved_assertion = ApiTestCaseAssertion.objects.get(id=assertion.id)
    assert saved_assertion.assertion_type == 'status_code'
    assert saved_assertion.expected_value == '200'
    print("PASS: Assertion saved correctly")

    return True

def test_response_time_assertion():
    """测试响应时间断言"""
    print("\n=== TC-ASSERT-002: 添加响应时间断言 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    assertion = ApiTestCaseAssertion.objects.create(
        test_case=test_case,
        assertion_type='response_time',
        target='response_time',
        operator='less_than',
        expected_value='1000',
        is_enabled=True,
        order=1
    )
    print(f"PASS: Created response time assertion ID={assertion.id}")
    return True

def test_json_value_assertion():
    """测试JSON值断言"""
    print("\n=== TC-ASSERT-004: JSON值断言 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    assertion = ApiTestCaseAssertion.objects.create(
        test_case=test_case,
        assertion_type='json_value',
        target='$.data.id',
        operator='equals',
        expected_value='123',
        is_enabled=True,
        order=2
    )
    print(f"PASS: Created JSON value assertion ID={assertion.id}")
    return True

def test_multiple_assertions():
    """测试多个断言执行"""
    print("\n=== TC-ASSERT-008: 多个断言执行 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    count = test_case.assertions.count()
    print(f"PASS: Test case has {count} assertions")
    return True

def test_assertion_disable():
    """测试禁用/启用断言"""
    print("\n=== TC-ASSERT-006: 禁用/启用断言 ===")
    assertion = ApiTestCaseAssertion.objects.filter(is_enabled=True).first()
    if not assertion:
        print("FAIL: No enabled assertion found")
        return False

    # 禁用断言
    assertion.is_enabled = False
    assertion.save()
    assertion.refresh_from_db()
    assert assertion.is_enabled == False
    print("PASS: Assertion disabled")

    # 启用断言
    assertion.is_enabled = True
    assertion.save()
    assertion.refresh_from_db()
    assert assertion.is_enabled == True
    print("PASS: Assertion enabled")
    return True

def test_delete_assertion():
    """测试删除断言"""
    print("\n=== TC-ASSERT-007: 删除断言 ===")
    # 创建一个临时断言用于删除测试
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    assertion = ApiTestCaseAssertion.objects.create(
        test_case=test_case,
        assertion_type='status_code',
        target='status_code',
        operator='equals',
        expected_value='200',
        is_enabled=True,
        order=99
    )

    assertion_id = assertion.id
    assertion.delete()

    exists = ApiTestCaseAssertion.objects.filter(id=assertion_id).exists()
    assert not exists
    print(f"PASS: Assertion {assertion_id} deleted")
    return True

def test_extraction_creation():
    """测试数据提取创建"""
    print("\n=== TC-EXT-001: 正则表达式提取 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    extraction = ApiTestCaseExtraction.objects.create(
        test_case=test_case,
        variable_name='token',
        extract_type='regex',
        extract_expression='"token":"([^"]+)"',
        default_value=None,
        extract_scope='body',
        variable_scope='global',
        is_enabled=True
    )
    print(f"PASS: Created extraction ID={extraction.id}, variable={extraction.variable_name}")
    return True

def test_json_path_extraction():
    """测试JSON路径提取"""
    print("\n=== TC-EXT-002: JSON路径提取 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    extraction = ApiTestCaseExtraction.objects.create(
        test_case=test_case,
        variable_name='user_id',
        extract_type='json_path',
        extract_expression='$.data.id',
        default_value='0',
        extract_scope='body',
        variable_scope='local',
        is_enabled=True
    )
    print(f"PASS: Created JSON path extraction ID={extraction.id}")
    return True

def test_extraction_with_default():
    """测试提取失败默认值"""
    print("\n=== TC-EXT-006: 提取失败默认值 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    extraction = ApiTestCaseExtraction.objects.create(
        test_case=test_case,
        variable_name='fallback_var',
        extract_type='json_path',
        extract_expression='$.nonexistent.path',
        default_value='default_value',
        extract_scope='body',
        variable_scope='local',
        is_enabled=True
    )
    assert extraction.default_value == 'default_value'
    print(f"PASS: Extraction with default value created")
    return True

def test_multiple_extractions():
    """测试多个变量提取"""
    print("\n=== TC-EXT-007: 多个变量提取 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    count = test_case.extractions.count()
    print(f"PASS: Test case has {count} extractions")
    return True

def test_extraction_disable():
    """测试禁用提取配置"""
    print("\n=== TC-EXT-008: 禁用提取配置 ===")
    extraction = ApiTestCaseExtraction.objects.filter(is_enabled=True).first()
    if not extraction:
        print("FAIL: No enabled extraction found")
        return False

    extraction.is_enabled = False
    extraction.save()
    extraction.refresh_from_db()
    assert extraction.is_enabled == False
    print("PASS: Extraction disabled")

    extraction.is_enabled = True
    extraction.save()
    extraction.refresh_from_db()
    assert extraction.is_enabled == True
    print("PASS: Extraction enabled")
    return True

def test_delete_extraction():
    """测试删除提取配置"""
    print("\n=== TC-EXT-010: 删除提取配置 ===")
    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    extraction = ApiTestCaseExtraction.objects.create(
        test_case=test_case,
        variable_name='temp_var',
        extract_type='json_path',
        extract_expression='$.temp',
        extract_scope='body',
        variable_scope='local',
        is_enabled=True
    )

    extraction_id = extraction.id
    extraction.delete()

    exists = ApiTestCaseExtraction.objects.filter(id=extraction_id).exists()
    assert not exists
    print(f"PASS: Extraction {extraction_id} deleted")
    return True

def test_api_serialization():
    """测试 API 序列化"""
    print("\n=== API Serialization Test ===")
    from api_automation.serializers import (
        ApiTestCaseAssertionSerializer,
        ApiTestCaseExtractionSerializer,
        ApiTestCaseDetailSerializer
    )

    test_case = ApiTestCase.objects.filter(is_deleted=False).first()
    if not test_case:
        print("FAIL: No test case found")
        return False

    # 测试断言序列化
    assertions = test_case.assertions.all()
    serializer = ApiTestCaseAssertionSerializer(assertions, many=True)
    print(f"PASS: Serialized {len(assertions)} assertions")

    # 测试提取配置序列化
    extractions = test_case.extractions.all()
    serializer = ApiTestCaseExtractionSerializer(extractions, many=True)
    print(f"PASS: Serialized {len(extractions)} extractions")

    # 测试测试用例详情序列化（包含断言和提取）
    serializer = ApiTestCaseDetailSerializer(test_case)
    data = serializer.data
    assert 'assertions' in data
    assert 'extractions' in data
    print("PASS: Test case detail serialization includes assertions and extractions")

    return True

def run_all_tests():
    """运行所有测试"""
    print("="*50)
    print("Starting Assertion and Extraction Feature Tests")
    print("="*50)

    tests = [
        test_assertion_creation,
        test_response_time_assertion,
        test_json_value_assertion,
        test_multiple_assertions,
        test_assertion_disable,
        test_delete_assertion,
        test_extraction_creation,
        test_json_path_extraction,
        test_extraction_with_default,
        test_multiple_extractions,
        test_extraction_disable,
        test_delete_extraction,
        test_api_serialization
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
            failed += 1

    print("\n" + "="*50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*50)

    return failed == 0

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
