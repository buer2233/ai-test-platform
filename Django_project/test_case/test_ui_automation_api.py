"""
UI自动化模块API全面测试

测试所有新增的UI自动化相关接口。
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://127.0.0.1:8000"
USERNAME = "ui_test"  # 替换为实际用户名
PASSWORD = "Test123456"  # 替换为实际密码

# 存储测试数据
test_data = {
    "token": None,
    "project_id": None,
    "test_case_id": None,
    "execution_id": None,
}


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {test_name}")
    if message:
        print(f"    {message}")


def login():
    """登录获取token"""
    print_section("1. User Login")
    try:
        # Token auth 需要使用表单数据
        response = requests.post(
            f"{BASE_URL}/api-token-auth/",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code == 200:
            token = response.json().get("token")
            test_data["token"] = token
            print_result("User Login", True, f"Token: {token[:20]}...")
            return True
        else:
            # 尝试使用 Basic Auth 获取 token
            import base64
            credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
            auth_headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            }
            response2 = requests.post(
                f"{BASE_URL}/api-token-auth/",
                headers=auth_headers
            )
            if response2.status_code == 200:
                token = response2.json().get("token")
                test_data["token"] = token
                print_result("User Login (Basic Auth)", True, f"Token: {token[:20]}...")
                return True
            else:
                print_result("User Login", False, f"Status: {response.status_code}, Response: {response.text}")
                print(f"Trying Basic Auth - Status: {response2.status_code}")
                return False
    except Exception as e:
        print_result("User Login", False, f"Exception: {str(e)}")
        return False


def get_headers():
    """获取请求头"""
    return {
        "Authorization": f"Token {test_data['token']}",
        "Content-Type": "application/json"
    }


def test_projects():
    """测试项目相关接口"""
    print_section("2. 测试项目接口")

    # 2.1 创建项目
    print("\n2.1 创建UI测试项目")
    project_data = {
        "name": f"测试项目_{datetime.now().strftime('%H%M%S')}",
        "description": "这是一个UI自动化测试项目",
        "base_url": "https://www.example.com",
        "default_browser_mode": "headless"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ui-automation/projects/",
            headers=get_headers(),
            json=project_data
        )
        if response.status_code in [200, 201]:
            project = response.json()
            test_data["project_id"] = project["id"]
            print_result("创建项目", True, f"项目ID: {project['id']}")
        else:
            print_result("创建项目", False, f"状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print_result("创建项目", False, f"异常: {str(e)}")
        return False

    # 2.2 获取项目列表
    print("\n2.2 获取项目列表")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/projects/",
            headers=get_headers()
        )
        if response.status_code == 200:
            projects = response.json()
            print_result("获取项目列表", True, f"共 {len(projects.get('results', projects))} 个项目")
        else:
            print_result("获取项目列表", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取项目列表", False, f"异常: {str(e)}")

    # 2.3 获取项目详情
    print("\n2.3 获取项目详情")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/projects/{test_data['project_id']}/",
            headers=get_headers()
        )
        if response.status_code == 200:
            project = response.json()
            print_result("获取项目详情", True, f"项目名称: {project['name']}")
        else:
            print_result("获取项目详情", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取项目详情", False, f"异常: {str(e)}")

    # 2.4 获取项目统计
    print("\n2.4 获取项目统计")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/projects/{test_data['project_id']}/statistics/",
            headers=get_headers()
        )
        if response.status_code == 200:
            stats = response.json()
            print_result("获取项目统计", True, f"用例数: {stats.get('test_cases', {}).get('total', 0)}")
        else:
            print_result("获取项目统计", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取项目统计", False, f"异常: {str(e)}")

    # 2.5 更新项目
    print("\n2.5 更新项目")
    update_data = {
        "name": f"更新后的项目_{datetime.now().strftime('%H%M%S')}",
        "description": "更新后的描述"
    }
    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/ui-automation/projects/{test_data['project_id']}/",
            headers=get_headers(),
            json=update_data
        )
        if response.status_code in [200, 201]:
            print_result("更新项目", True)
        else:
            print_result("更新项目", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("更新项目", False, f"异常: {str(e)}")

    return True


def test_test_cases():
    """测试用例相关接口"""
    print_section("3. 测试用例接口")

    # 3.1 创建测试用例
    print("\n3.1 创建测试用例")
    case_data = {
        "project": test_data["project_id"],
        "name": f"登录功能测试_{datetime.now().strftime('%H%M%S')}",
        "natural_language_task": "打开首页，点击登录按钮，输入用户名和密码，验证登录成功",
        "expected_result": "登录成功，显示用户名",
        "tags": ["登录", "冒烟测试"],
        "priority": "high",
        "is_enabled": True
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/",
            headers=get_headers(),
            json=case_data
        )
        if response.status_code in [200, 201]:
            case = response.json()
            test_data["test_case_id"] = case["id"]
            print_result("创建测试用例", True, f"用例ID: {case['id']}")
        else:
            print_result("创建测试用例", False, f"状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print_result("创建测试用例", False, f"异常: {str(e)}")
        return False

    # 3.2 获取用例列表
    print("\n3.2 获取用例列表")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/",
            headers=get_headers()
        )
        if response.status_code == 200:
            cases = response.json()
            count = len(cases.get('results', cases))
            print_result("获取用例列表", True, f"共 {count} 个用例")
        else:
            print_result("获取用例列表", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取用例列表", False, f"异常: {str(e)}")

    # 3.3 获取用例详情
    print("\n3.3 获取用例详情")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/{test_data['test_case_id']}/",
            headers=get_headers()
        )
        if response.status_code == 200:
            case = response.json()
            print_result("获取用例详情", True, f"用例名称: {case['name']}")
        else:
            print_result("获取用例详情", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取用例详情", False, f"异常: {str(e)}")

    # 3.4 更新测试用例
    print("\n3.4 更新测试用例")
    update_data = {
        "name": f"更新后的登录测试_{datetime.now().strftime('%H%M%S')}",
        "priority": "critical"
    }
    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/{test_data['test_case_id']}/",
            headers=get_headers(),
            json=update_data
        )
        if response.status_code in [200, 201]:
            print_result("更新测试用例", True)
        else:
            print_result("更新测试用例", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("更新测试用例", False, f"异常: {str(e)}")

    return True


def test_executions():
    """测试执行相关接口"""
    print_section("4. 测试执行接口")

    # 4.1 创建执行记录
    print("\n4.1 创建执行记录")
    execution_data = {
        "test_case": test_data["test_case_id"],
        "browser_mode": "headless"
    }
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ui-automation/executions/",
            headers=get_headers(),
            json=execution_data
        )
        if response.status_code in [200, 201]:
            execution = response.json()
            test_data["execution_id"] = execution["id"]
            print_result("创建执行记录", True, f"执行ID: {execution['id']}")
        else:
            print_result("创建执行记录", False, f"状态码: {response.status_code}, 响应: {response.text}")
            return False
    except Exception as e:
        print_result("创建执行记录", False, f"异常: {str(e)}")
        return False

    # 4.2 获取执行列表
    print("\n4.2 获取执行列表")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/executions/",
            headers=get_headers()
        )
        if response.status_code == 200:
            executions = response.json()
            count = len(executions.get('results', executions))
            print_result("获取执行列表", True, f"共 {count} 条记录")
        else:
            print_result("获取执行列表", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取执行列表", False, f"异常: {str(e)}")

    # 4.3 获取执行详情
    print("\n4.3 获取执行详情")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/executions/{test_data['execution_id']}/",
            headers=get_headers()
        )
        if response.status_code == 200:
            execution = response.json()
            print_result("获取执行详情", True, f"状态: {execution.get('status_display', execution.get('status'))}")
        else:
            print_result("获取执行详情", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("获取执行详情", False, f"异常: {str(e)}")

    # 4.4 测试运行接口（暂未实现，应返回提示）
    print("\n4.4 测试运行接口（阶段3实现）")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ui-automation/executions/{test_data['execution_id']}/run/",
            headers=get_headers()
        )
        if response.status_code == 200:
            result = response.json()
            print_result("运行接口", True, f"响应: {result.get('message', 'success')}")
        else:
            print_result("运行接口", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("运行接口", False, f"异常: {str(e)}")

    return True


def test_filters_and_search():
    """测试过滤和搜索功能"""
    print_section("5. 测试过滤和搜索功能")

    # 5.1 按项目过滤用例
    print("\n5.1 按项目过滤用例")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/?project={test_data['project_id']}",
            headers=get_headers()
        )
        if response.status_code == 200:
            cases = response.json()
            count = len(cases.get('results', cases))
            print_result("按项目过滤", True, f"找到 {count} 个用例")
        else:
            print_result("按项目过滤", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("按项目过滤", False, f"异常: {str(e)}")

    # 5.2 按优先级过滤用例
    print("\n5.2 按优先级过滤用例")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/?priority=high",
            headers=get_headers()
        )
        if response.status_code == 200:
            print_result("按优先级过滤", True)
        else:
            print_result("按优先级过滤", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("按优先级过滤", False, f"异常: {str(e)}")

    # 5.3 搜索用例
    print("\n5.3 搜索用例")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/?search=登录",
            headers=get_headers()
        )
        if response.status_code == 200:
            print_result("搜索用例", True)
        else:
            print_result("搜索用例", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("搜索用例", False, f"异常: {str(e)}")

    return True


def test_delete_operations():
    """测试删除操作"""
    print_section("6. 测试删除操作")

    # 6.1 删除测试用例（软删除）
    print("\n6.1 删除测试用例")
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/ui-automation/test-cases/{test_data['test_case_id']}/",
            headers=get_headers()
        )
        if response.status_code in [200, 204]:
            print_result("删除测试用例", True)
        else:
            print_result("删除测试用例", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("删除测试用例", False, f"异常: {str(e)}")

    # 6.2 删除项目
    print("\n6.2 删除项目")
    try:
        response = requests.delete(
            f"{BASE_URL}/api/v1/ui-automation/projects/{test_data['project_id']}/",
            headers=get_headers()
        )
        if response.status_code in [200, 204]:
            print_result("删除项目", True)
        else:
            print_result("删除项目", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("删除项目", False, f"异常: {str(e)}")

    return True


def main():
    """主测试函数"""
    print(f"\n开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 登录
    if not login():
        print("\n[ERROR] Login failed, aborting test")
        sys.exit(1)

    # 运行所有测试
    results = []
    results.append(("项目接口", test_projects()))
    results.append(("用例接口", test_test_cases()))
    results.append(("执行接口", test_executions()))
    results.append(("过滤搜索", test_filters_and_search()))
    results.append(("删除操作", test_delete_operations()))

    # 汇总结果
    print_section("测试结果汇总")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n通过: {passed}/{total}")

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    if passed == total:
        print(f"\n[SUCCESS] 所有测试通过！进入阶段 3 开发...")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败，需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
