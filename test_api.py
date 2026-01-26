# -*- coding: utf-8 -*-
import requests
import json
import sys

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

# 1. 获取 Token
print("=" * 60)
print("1. 测试登录接口")
print("=" * 60)
login_data = {"username": "admin", "password": "admin123456"}
response = requests.post(f"{BASE_URL}/api-token-auth/", json=login_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    token = response.json().get("token")
    print(f"Token: {token[:20]}...")
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    # 2. 测试 API 自动化平台接口
    print("\n" + "=" * 60)
    print("2. API 自动化平台接口测试")
    print("=" * 60)

    api_endpoints = [
        ("GET", "/api/v1/api-automation/projects/", "项目列表"),
        ("POST", "/api/v1/api-automation/projects/", "创建项目"),
        ("GET", "/api/v1/api-automation/environments/", "环境列表"),
        ("GET", "/api/v1/api-automation/collections/", "集合列表"),
        ("GET", "/api/v1/api-automation/test-cases/", "测试用例列表"),
        ("GET", "/api/v1/api-automation/dashboard/", "仪表盘"),
        ("GET", "/api/v1/api-automation/executions/", "执行记录"),
        ("GET", "/api/v1/api-automation/reports/", "测试报告"),
        ("GET", "/api/v1/api-automation/data-drivers/", "数据驱动列表"),
        ("GET", "/api/v1/api-automation/recycle-bin/", "回收站"),
    ]

    results = []
    for method, endpoint, desc in api_endpoints:
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            else:
                resp = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json={"name": "测试项目", "description": "测试"})

            status = "[PASS]" if resp.status_code < 400 else "[FAIL]"
            results.append((desc, resp.status_code, status))
            print(f"{status:7} | {method:4} | {endpoint:55} | {resp.status_code}")
        except Exception as e:
            results.append((desc, 0, "[ERROR]"))
            print(f"[ERROR]  | {method:4} | {endpoint:55} | {e}")

    # 3. 测试 UI 自动化平台接口
    print("\n" + "=" * 60)
    print("3. UI 自动化平台接口测试")
    print("=" * 60)

    ui_endpoints = [
        ("GET", "/api/v1/ui-automation/projects/", "UI项目列表"),
        ("GET", "/api/v1/ui-automation/test-cases/", "UI测试用例列表"),
        ("GET", "/api/v1/ui-automation/executions/", "UI执行记录"),
        ("GET", "/api/v1/ui-automation/reports/", "UI测试报告"),
    ]

    for method, endpoint, desc in ui_endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            status = "[PASS]" if resp.status_code < 400 else "[FAIL]"
            results.append((desc, resp.status_code, status))
            print(f"{status:7} | {method:4} | {endpoint:55} | {resp.status_code}")
        except Exception as e:
            results.append((desc, 0, "[ERROR]"))
            print(f"[ERROR]  | {method:4} | {endpoint:55} | {e}")

    # 4. 汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    passed = sum(1 for r in results if "PASS" in r[2])
    failed = sum(1 for r in results if "FAIL" in r[2])
    error = sum(1 for r in results if "ERROR" in r[2])
    print(f"总计: {len(results)} | 通过: {passed} | 失败: {failed} | 错误: {error}")

    if passed == len(results):
        print("\n[SUCCESS] 所有接口测试通过!")
    else:
        print(f"\n[WARNING] {failed + error} 个接口存在问题")
