# -*- coding: utf-8 -*-
"""
全面的测试用例API测试
测试创建、更新测试用例时的断言和提取配置
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/api-automation"
AUTH_URL = "http://127.0.0.1:8000"

# 获取认证token
def get_token():
    resp = requests.post(f"{AUTH_URL}/api-token-auth/", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        return resp.json().get('token')
    return None

TOKEN = get_token()
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

print("[INFO] Token obtained:", "YES" if TOKEN else "NO")

def test_1_assertions():
    """测试1: 创建带断言的测试用例"""
    print("\n" + "="*50)
    print("TEST 1: Create test case with assertions")
    print("="*50)

    # 创建测试用例
    case = {
        "name": "TC-With-Assertions",
        "description": "Test with assertions",
        "project": 18,
        "method": "GET",
        "url": "/api/test"
    }
    resp = requests.post(f"{BASE_URL}/test-cases/", json=case, headers=HEADERS)
    print(f"Create case: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Failed: {resp.text}")
        return False

    case_id = resp.json()['id']
    print(f"Case ID: {case_id}")

    # 添加断言
    assertions = [
        {"assertion_type": "status_code", "target": "status_code", "operator": "equals", "expected_value": "200", "is_enabled": True, "order": 0},
        {"assertion_type": "response_time", "target": "response_time", "operator": "less_than", "expected_value": "3000", "is_enabled": True, "order": 1}
    ]

    for idx, ass in enumerate(assertions):
        resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/assertions/", json=ass, headers=HEADERS)
        print(f"Add assertion {idx+1}: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Failed: {resp.text}")
            return False

    # 查询断言
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/assertions/", headers=HEADERS)
    print(f"Query assertions: {resp.status_code}")
    if resp.status_code == 200:
        count = len(resp.json().get('results', resp.json()))
        print(f"Assertion count: {count}")

    return True

def test_2_extractions():
    """测试2: 创建带提取的测试用例"""
    print("\n" + "="*50)
    print("TEST 2: Create test case with extractions")
    print("="*50)

    # 创建测试用例
    case = {
        "name": "TC-With-Extractions",
        "description": "Test with extractions",
        "project": 18,
        "method": "POST",
        "url": "/api/login"
    }
    resp = requests.post(f"{BASE_URL}/test-cases/", json=case, headers=HEADERS)
    print(f"Create case: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Failed: {resp.text}")
        return False

    case_id = resp.json()['id']
    print(f"Case ID: {case_id}")

    # 添加提取
    extractions = [
        {"variable_name": "token", "extract_type": "json_path", "extract_expression": "$.data.token", "is_enabled": True, "scope": "body", "extract_scope": "body", "variable_scope": "local"},
        {"variable_name": "user_id", "extract_type": "json_path", "extract_expression": "$.data.id", "is_enabled": True, "scope": "body", "extract_scope": "body", "variable_scope": "global"}
    ]

    for idx, ext in enumerate(extractions):
        resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/extractions/", json=ext, headers=HEADERS)
        print(f"Add extraction {idx+1}: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Failed: {resp.text}")
            return False

    # 查询提取
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/extractions/", headers=HEADERS)
    print(f"Query extractions: {resp.status_code}")
    if resp.status_code == 200:
        count = len(resp.json().get('results', resp.json()))
        print(f"Extraction count: {count}")

    return True

def test_3_both():
    """测试3: 创建同时带断言和提取的测试用例"""
    print("\n" + "="*50)
    print("TEST 3: Create test case with both")
    print("="*50)

    # 创建测试用例
    case = {
        "name": "TC-Full-Config",
        "description": "Test with all configs",
        "project": 18,
        "method": "POST",
        "url": "/api/user/create"
    }
    resp = requests.post(f"{BASE_URL}/test-cases/", json=case, headers=HEADERS)
    print(f"Create case: {resp.status_code}")
    if resp.status_code != 201:
        print(f"Failed: {resp.text}")
        return False

    case_id = resp.json()['id']
    print(f"Case ID: {case_id}")

    # 添加断言
    ass = {"assertion_type": "status_code", "target": "status_code", "operator": "equals", "expected_value": "201", "is_enabled": True, "order": 0}
    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/assertions/", json=ass, headers=HEADERS)
    print(f"Add assertion: {resp.status_code}")

    # 添加提取
    ext = {"variable_name": "new_id", "extract_type": "json_path", "extract_expression": "$.data.id", "is_enabled": True, "scope": "body", "extract_scope": "body", "variable_scope": "local"}
    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/extractions/", json=ext, headers=HEADERS)
    print(f"Add extraction: {resp.status_code}")

    # 查询完整信息
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/", headers=HEADERS)
    print(f"Query full case: {resp.status_code}")

    return resp.status_code == 200

def test_4_update():
    """测试4: 更新测试用例配置"""
    print("\n" + "="*50)
    print("TEST 4: Update test case configs")
    print("="*50)

    # 获取一个测试用例
    resp = requests.get(f"{BASE_URL}/test-cases/?page=1&page_size=1", headers=HEADERS)
    if resp.status_code != 200:
        print("Failed to get cases")
        return False

    results = resp.json().get('results', [])
    if not results:
        print("No cases found")
        return False

    case_id = results[0]['id']
    print(f"Using case ID: {case_id}")

    # 更新测试用例
    resp = requests.put(f"{BASE_URL}/test-cases/{case_id}/", json={
        "name": f"Updated-{case_id}",
        "method": "PUT",
        "url": "/api/updated"
    }, headers=HEADERS)
    print(f"Update case: {resp.status_code}")

    # 更新断言
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/assertions/", headers=HEADERS)
    if resp.status_code == 200:
        assertions = resp.json().get('results', resp.json())
        if assertions:
            ass_id = assertions[0]['id']
            resp = requests.patch(f"{BASE_URL}/test-cases/{case_id}/assertions/{ass_id}/", json={
                "expected_value": "204"
            }, headers=HEADERS)
            print(f"Update assertion: {resp.status_code}")

    # 更新提取
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/extractions/", headers=HEADERS)
    if resp.status_code == 200:
        extractions = resp.json().get('results', resp.json())
        if extractions:
            ext_id = extractions[0]['id']
            resp = requests.patch(f"{BASE_URL}/test-cases/{case_id}/extractions/{ext_id}/", json={
                "variable_name": "updated_var"
            }, headers=HEADERS)
            print(f"Update extraction: {resp.status_code}")

    return True

def main():
    print("="*50)
    print("API TEST SUITE")
    print("="*50)

    results = {
        "Test 1 (Assertions)": test_1_assertions(),
        "Test 2 (Extractions)": test_2_extractions(),
        "Test 3 (Both)": test_3_both(),
        "Test 4 (Update)": test_4_update()
    }

    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\nAll tests passed!")
    else:
        print(f"\n{total - passed} test(s) failed!")

if __name__ == "__main__":
    main()
