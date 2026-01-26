"""
全面的测试用例API测试
测试创建、更新测试用例时的断言和提取配置
"""
import requests
import json
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1/api-automation"

# 获取认证token
def get_auth_token():
    """获取认证token"""
    auth_data = {
        "username": "admin",
        "password": "admin123"
    }
    resp = requests.post(f"{BASE_URL}/auth/login/", json=auth_data)
    if resp.status_code == 200:
        return resp.json().get('data', {}).get('token') or resp.json().get('token')
    return None

# 获取token
TOKEN = get_auth_token()
if TOKEN:
    HEADERS = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    print(f"[INFO] 获取认证token成功")
else:
    # 尝试使用session
    session = requests.Session()
    auth_resp = session.post(f"{BASE_URL}/auth/login/", json={"username": "admin", "password": "admin123"})
    if auth_resp.status_code == 200:
        # 使用session cookie
        HEADERS = {"Content-Type": "application/json"}
        print(f"[INFO] 使用session认证")
    else:
        HEADERS = {"Content-Type": "application/json"}
        print(f"[WARN] 无法获取认证token")

def test_create_test_case_with_assertions():
    """测试创建带断言的测试用例"""
    print("\n=== 测试1: 创建带断言的测试用例 ===")

    # 1. 创建测试用例
    case_data = {
        "name": "测试用例-带断言",
        "description": "测试带断言的用例创建",
        "project": 18,
        "collection": None,
        "method": "GET",
        "url": "/api/test",
        "headers": {"Content-Type": "application/json"},
        "params": {},
        "body": {}
    }

    resp = requests.post(f"{BASE_URL}/test-cases/", json=case_data)
    print(f"创建测试用例: {resp.status_code}")
    if resp.status_code == 201:
        case_id = resp.json()['id']
        print(f"✓ 测试用例创建成功，ID: {case_id}")
    else:
        print(f"✗ 创建失败: {resp.text}")
        return False

    # 2. 添加断言配置
    assertion_data = {
        "assertion_type": "status_code",
        "target": "status_code",
        "operator": "equals",
        "expected_value": "200",
        "is_enabled": True,
        "order": 0
    }

    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/assertions/", json=assertion_data, headers=HEADERS)
    print(f"添加断言配置: {resp.status_code}")
    if resp.status_code == 201:
        print(f"✓ 断言配置添加成功: {resp.json()}")
    else:
        print(f"✗ 断言配置添加失败: {resp.text}")
        return False

    # 3. 添加第二个断言
    assertion_data2 = {
        "assertion_type": "response_time",
        "target": "response_time",
        "operator": "less_than",
        "expected_value": "3000",
        "is_enabled": True,
        "order": 1
    }

    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/assertions/", json=assertion_data2)
    print(f"添加第二个断言: {resp.status_code}")
    if resp.status_code == 201:
        print(f"✓ 第二个断言添加成功")
    else:
        print(f"✗ 第二个断言添加失败: {resp.text}")
        return False

    # 4. 查询断言列表
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/assertions/")
    print(f"查询断言列表: {resp.status_code}")
    if resp.status_code == 200:
        assertions = resp.json()['results'] if 'results' in resp.json() else resp.json()
        print(f"✓ 查询成功，断言数量: {len(assertions)}")
    else:
        print(f"✗ 查询失败: {resp.text}")
        return False

    return True, case_id


def test_create_test_case_with_extractions():
    """测试创建带提取配置的测试用例"""
    print("\n=== 测试2: 创建带提取配置的测试用例 ===")

    # 1. 创建测试用例
    case_data = {
        "name": "测试用例-带提取",
        "description": "测试带提取配置的用例创建",
        "project": 18,
        "collection": None,
        "method": "POST",
        "url": "/api/login",
        "headers": {"Content-Type": "application/json"},
        "params": {},
        "body": {"username": "test", "password": "123456"}
    }

    resp = requests.post(f"{BASE_URL}/test-cases/", json=case_data)
    print(f"创建测试用例: {resp.status_code}")
    if resp.status_code == 201:
        case_id = resp.json()['id']
        print(f"✓ 测试用例创建成功，ID: {case_id}")
    else:
        print(f"✗ 创建失败: {resp.text}")
        return False

    # 2. 添加提取配置
    extraction_data = {
        "variable_name": "token",
        "extract_type": "json_path",
        "extract_expression": "$.data.token",
        "default_value": None,
        "is_enabled": True,
        "scope": "body",
        "extract_scope": "body",
        "variable_scope": "local"
    }

    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/extractions/", json=extraction_data)
    print(f"添加提取配置: {resp.status_code}")
    if resp.status_code == 201:
        print(f"✓ 提取配置添加成功: {resp.json()}")
    else:
        print(f"✗ 提取配置添加失败: {resp.text}")
        return False

    # 3. 添加第二个提取配置
    extraction_data2 = {
        "variable_name": "user_id",
        "extract_type": "json_path",
        "extract_expression": "$.data.id",
        "default_value": None,
        "is_enabled": True,
        "scope": "body",
        "extract_scope": "body",
        "variable_scope": "global"
    }

    resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/extractions/", json=extraction_data2)
    print(f"添加第二个提取: {resp.status_code}")
    if resp.status_code == 201:
        print(f"✓ 第二个提取配置添加成功")
    else:
        print(f"✗ 第二个提取配置添加失败: {resp.text}")
        return False

    # 4. 查询提取列表
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/extractions/")
    print(f"查询提取列表: {resp.status_code}")
    if resp.status_code == 200:
        extractions = resp.json()['results'] if 'results' in resp.json() else resp.json()
        print(f"✓ 查询成功，提取配置数量: {len(extractions)}")
    else:
        print(f"✗ 查询失败: {resp.text}")
        return False

    return True, case_id


def test_create_test_case_with_both():
    """测试创建同时带断言和提取的测试用例"""
    print("\n=== 测试3: 创建同时带断言和提取的测试用例 ===")

    # 1. 创建测试用例
    case_data = {
        "name": "测试用例-完整配置",
        "description": "测试完整配置的用例创建",
        "project": 18,
        "collection": None,
        "method": "POST",
        "url": "/api/user/create",
        "headers": {"Content-Type": "application/json"},
        "params": {},
        "body": {"name": "test"}
    }

    resp = requests.post(f"{BASE_URL}/test-cases/", json=case_data)
    print(f"创建测试用例: {resp.status_code}")
    if resp.status_code == 201:
        case_id = resp.json()['id']
        print(f"✓ 测试用例创建成功，ID: {case_id}")
    else:
        print(f"✗ 创建失败: {resp.text}")
        return False

    # 2. 批量添加断言
    assertions = [
        {
            "assertion_type": "status_code",
            "target": "status_code",
            "operator": "equals",
            "expected_value": "201",
            "is_enabled": True,
            "order": 0
        },
        {
            "assertion_type": "json_value",
            "target": "$.code",
            "operator": "equals",
            "expected_value": "0",
            "is_enabled": True,
            "order": 1
        }
    ]

    for idx, assertion in enumerate(assertions):
        resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/assertions/", json=assertion)
        print(f"添加断言{idx + 1}: {resp.status_code}")
        if resp.status_code != 201:
            print(f"✗ 断言{idx + 1}添加失败: {resp.text}")
            return False
    print(f"✓ 所有断言添加成功")

    # 3. 批量添加提取
    extractions = [
        {
            "variable_name": "user_id",
            "extract_type": "json_path",
            "extract_expression": "$.data.id",
            "default_value": None,
            "is_enabled": True,
            "scope": "body",
            "extract_scope": "body",
            "variable_scope": "local"
        },
        {
            "variable_name": "auth_token",
            "extract_type": "regex",
            "extract_expression": '"token":"([^"]+)"',
            "default_value": None,
            "is_enabled": True,
            "scope": "body",
            "extract_scope": "body",
            "variable_scope": "global"
        }
    ]

    for idx, extraction in enumerate(extractions):
        resp = requests.post(f"{BASE_URL}/test-cases/{case_id}/extractions/", json=extraction)
        print(f"添加提取{idx + 1}: {resp.status_code}")
        if resp.status_code != 201:
            print(f"✗ 提取{idx + 1}添加失败: {resp.text}")
            return False
    print(f"✓ 所有提取配置添加成功")

    # 4. 验证完整数据
    resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/")
    print(f"查询完整测试用例: {resp.status_code}")
    if resp.status_code == 200:
        case = resp.json()
        print(f"✓ 测试用例名称: {case['name']}")
    else:
        print(f"✗ 查询失败: {resp.text}")
        return False

    return True, case_id


def test_update_test_case_with_config():
    """测试更新测试用例及其配置"""
    print("\n=== 测试4: 更新测试用例及其配置 ===")

    # 先获取一个测试用例ID
    resp = requests.get(f"{BASE_URL}/test-cases/?page=1&page_size=1")
    if resp.status_code != 200:
        print("✗ 无法获取测试用例列表")
        return False

    results = resp.json().get('results', [])
    if not results:
        print("✗ 没有可用的测试用例")
        return False

    case_id = results[0]['id']
    print(f"使用测试用例ID: {case_id}")

    # 1. 更新测试用例基本信息
    update_data = {
        "name": f"更新后的测试用例-{case_id}",
        "description": "已更新",
        "method": "PUT",
        "url": "/api/updated"
    }

    resp = requests.put(f"{BASE_URL}/test-cases/{case_id}/", json=update_data)
    print(f"更新测试用例: {resp.status_code}")
    if resp.status_code == 200:
        print(f"✓ 测试用例更新成功")
    else:
        print(f"✗ 更新失败: {resp.text}")
        return False

    # 2. 更新断言配置
    assertions_resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/assertions/")
    if assertions_resp.status_code == 200:
        assertions = assertions_resp.json().get('results', assertions_resp.json())
        if assertions:
            assertion_id = assertions[0]['id']
            update_assertion = {
                "expected_value": "204",
                "is_enabled": False
            }
            resp = requests.patch(f"{BASE_URL}/test-cases/{case_id}/assertions/{assertion_id}/", json=update_assertion)
            print(f"更新断言配置: {resp.status_code}")
            if resp.status_code == 200:
                print(f"✓ 断言配置更新成功")
            else:
                print(f"✗ 断言配置更新失败: {resp.text}")

    # 3. 更新提取配置
    extractions_resp = requests.get(f"{BASE_URL}/test-cases/{case_id}/extractions/")
    if extractions_resp.status_code == 200:
        extractions = extractions_resp.json().get('results', extractions_resp.json())
        if extractions:
            extraction_id = extractions[0]['id']
            update_extraction = {
                "variable_name": "updated_token",
                "is_enabled": False
            }
            resp = requests.patch(f"{BASE_URL}/test-cases/{case_id}/extractions/{extraction_id}/", json=update_extraction)
            print(f"更新提取配置: {resp.status_code}")
            if resp.status_code == 200:
                print(f"✓ 提取配置更新成功")
            else:
                print(f"✗ 提取配置更新失败: {resp.text}")

    return True, case_id


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始全面的测试用例API测试")
    print("=" * 60)

    results = {}

    # 测试1: 创建带断言的测试用例
    result = test_create_test_case_with_assertions()
    results['test1'] = result

    # 测试2: 创建带提取配置的测试用例
    result = test_create_test_case_with_extractions()
    results['test2'] = result

    # 测试3: 创建同时带断言和提取的测试用例
    result = test_create_test_case_with_both()
    results['test3'] = result

    # 测试4: 更新测试用例
    result = test_update_test_case_with_config()
    results['test4'] = result

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        if result:
            if isinstance(result, tuple) and result[0]:
                passed += 1
                print(f"✓ {test_name}: 通过")
            elif result is True:
                passed += 1
                print(f"✓ {test_name}: 通过")
            else:
                failed += 1
                print(f"✗ {test_name}: 失败")
        else:
            failed += 1
            print(f"✗ {test_name}: 失败")

    print(f"\n总计: {passed + failed} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed / (passed + failed) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")


if __name__ == "__main__":
    main()
