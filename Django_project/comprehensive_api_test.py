"""
全面的API端点测试脚本
测试所有核心API功能，包括认证、CRUD操作、权限控制等
"""
import os
import sys
import json
import time
import django
from datetime import datetime

# Django环境设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# API基础URL
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试结果记录
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'start_time': None,
    'end_time': None
}

# 认证token
auth_token = None

# 测试数据存储（用于清理）
test_data = {
    'project_id': None,
    'collection_id': None,
    'test_case_id': None,
    'environment_id': None,
    'assertion_id': None,
    'extraction_id': None,
    'execution_id': None
}


def log_test(category, name, passed, message="", details=None):
    """记录测试结果"""
    result = {
        'name': name,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }

    if passed:
        test_results['passed'].append(result)
        print(f"[PASS] [{category}] {name}")
        if message:
            print(f"  {message}")
    else:
        test_results['failed'].append(result)
        print(f"[FAIL] [{category}] {name}")
        print(f"  {message}")
        if details:
            print(f"  Details: {details}")


def log_warning(category, name, message, details=None):
    """记录警告"""
    warning = {
        'name': name,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    test_results['warnings'].append(warning)
    print(f"[WARN] [{category}] {name}: {message}")


def make_request(method, endpoint, data=None, params=None, headers=None, need_auth=True):
    """发送HTTP请求"""
    url = f"{API_BASE}{endpoint}"
    request_headers = {}

    if headers:
        request_headers.update(headers)

    if need_auth and auth_token:
        # 使用Token认证（不是Bearer）
        request_headers['Authorization'] = f'Token {auth_token}'

    start_time = time.time()

    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=request_headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, params=params, headers=request_headers, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, params=params, headers=request_headers, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, params=params, headers=request_headers, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, params=params, headers=request_headers, timeout=10)
        else:
            return None, "Unsupported method"

        elapsed = time.time() - start_time

        return {
            'status_code': response.status_code,
            'data': response.json() if response.content else None,
            'elapsed': elapsed,
            'headers': dict(response.headers)
        }, None

    except requests.exceptions.Timeout:
        return None, f"Request timeout after 10 seconds"
    except requests.exceptions.ConnectionError:
        return None, f"Connection error - server may not be running"
    except requests.exceptions.RequestException as e:
        return None, f"Request exception: {str(e)}"
    except json.JSONDecodeError:
        return {
            'status_code': response.status_code,
            'data': response.text,
            'elapsed': elapsed,
            'headers': dict(response.headers)
        }, None


def test_swagger_access():
    """测试Swagger API文档访问"""
    print("\n=== 测试Swagger API文档访问 ===")

    try:
        response = requests.get(f"{BASE_URL}/swagger/", timeout=10)
        passed = response.status_code == 200
        log_test(
            "Swagger",
            "API文档访问",
            passed,
            f"状态码: {response.status_code}, 响应时间: {response.elapsed.total_seconds():.2f}s",
            response.url
        )

        # 检查是否有AnonymousUser错误
        if 'AnonymousUser' in response.text:
            log_warning(
                "Swagger",
                "AnonymousUser警告",
                "响应中发现AnonymousUser相关内容",
                "可能存在权限配置问题"
            )

    except Exception as e:
        log_test("Swagger", "API文档访问", False, f"异常: {str(e)}")


def test_auth_login():
    """测试Token认证"""
    global auth_token

    print("\n=== 测试Token认证 ===")

    # 由于系统使用DRF的Token认证，我们需要通过命令行获取token
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from rest_framework.authtoken.models import Token

    User = get_user_model()

    # 确保admin用户存在
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    # 获取或创建token
    token, created = Token.objects.get_or_create(user=admin)
    auth_token = token.key

    log_test(
        "Auth",
        "Token认证",
        True,
        f"成功获取token (新创建: {created})",
        f"Token: {auth_token[:20]}..."
    )

    # 测试token是否有效
    headers = {'Authorization': f'Token {auth_token}'}
    response = requests.get(f"{BASE_URL}/api/v1/api-automation/projects/", headers=headers, timeout=10)

    if response.status_code == 200:
        log_test("Auth", "Token验证", True, "Token有效，可以访问API")
        return True
    else:
        log_test("Auth", "Token验证", False, f"Token无效，状态码: {response.status_code}")
        return False


def test_project_management():
    """测试项目管理API"""
    print("\n=== 测试项目管理API ===")

    # 1. 创建项目
    project_data = {
        'name': '测试项目_API测试',
        'description': 'API自动化测试项目'
    }

    response, error = make_request('POST', '/api-automation/projects/', project_data)

    if error or response['status_code'] != 201:
        log_test("Project", "创建项目", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    project = response['data']
    test_data['project_id'] = project['id']
    log_test("Project", "创建项目", True, f"项目ID: {project['id']}", project)

    # 2. 获取项目列表
    response, error = make_request('GET', '/api-automation/projects/')
    if error or response['status_code'] != 200:
        log_test("Project", "项目列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Project", "项目列表", True, f"获取到 {count} 个项目")

    # 3. 获取项目详情
    response, error = make_request('GET', f"/api-automation/projects/{test_data['project_id']}/")
    if error or response['status_code'] != 200:
        log_test("Project", "项目详情", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Project", "项目详情", True, f"项目名称: {response['data']['name']}")

    # 4. 更新项目
    update_data = {
        'name': '测试项目_API测试_已更新',
        'description': '更新后的描述'
    }

    response, error = make_request('PUT', f"/api-automation/projects/{test_data['project_id']}/", update_data)
    if error or response['status_code'] != 200:
        log_test("Project", "更新项目", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Project", "更新项目", True, f"更新后名称: {response['data']['name']}")

    # 5. 克隆项目
    response, error = make_request('POST', f"/api-automation/projects/{test_data['project_id']}/clone/")
    if error or response['status_code'] not in [200, 201]:
        log_test("Project", "克隆项目", False, error or f"状态码: {response['status_code']}")
    else:
        cloned_id = response['data']['id']
        log_test("Project", "克隆项目", True, f"克隆项目ID: {cloned_id}")
        # 清理克隆的项目
        make_request('DELETE', f"/api-automation/projects/{cloned_id}/")


def test_collection_management():
    """测试集合管理API"""
    print("\n=== 测试集合管理API ===")

    if not test_data['project_id']:
        log_test("Collection", "创建集合", False, "缺少project_id")
        return

    # 1. 创建集合
    collection_data = {
        'project': test_data['project_id'],
        'name': '测试集合_API测试',
        'description': 'API测试集合'
    }

    response, error = make_request('POST', '/api-automation/collections/', collection_data)

    if error or response['status_code'] != 201:
        log_test("Collection", "创建集合", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    collection = response['data']
    test_data['collection_id'] = collection['id']
    log_test("Collection", "创建集合", True, f"集合ID: {collection['id']}", collection)

    # 2. 获取集合列表
    response, error = make_request('GET', '/api-automation/collections/', params={'project': test_data['project_id']})
    if error or response['status_code'] != 200:
        log_test("Collection", "集合列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Collection", "集合列表", True, f"获取到 {count} 个集合")

    # 3. 获取集合详情
    response, error = make_request('GET', f"/api-automation/collections/{test_data['collection_id']}/")
    if error or response['status_code'] != 200:
        log_test("Collection", "集合详情", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Collection", "集合详情", True, f"集合名称: {response['data']['name']}")

    # 4. 更新集合
    update_data = {
        'project': test_data['project_id'],
        'name': '测试集合_API测试_已更新',
        'description': '更新后的描述'
    }

    response, error = make_request('PUT', f"/api-automation/collections/{test_data['collection_id']}/", update_data)
    if error or response['status_code'] != 200:
        log_test("Collection", "更新集合", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Collection", "更新集合", True, f"更新后名称: {response['data']['name']}")

    # 5. 克隆集合
    response, error = make_request('POST', f"/api-automation/collections/{test_data['collection_id']}/clone/")
    if error or response['status_code'] not in [200, 201]:
        log_test("Collection", "克隆集合", False, error or f"状态码: {response['status_code']}")
    else:
        cloned_id = response['data']['id']
        log_test("Collection", "克隆集合", True, f"克隆集合ID: {cloned_id}")
        # 清理克隆的集合
        make_request('DELETE', f"/api-automation/collections/{cloned_id}/")


def test_environment_management():
    """测试环境管理API"""
    print("\n=== 测试环境管理API ===")

    # 1. 创建环境
    env_data = {
        'project': test_data['project_id'],
        'name': '测试环境_API测试',
        'base_url': 'https://httpbin.org',
        'description': 'API测试环境',
        'is_default': False,
        'variables': {
            'var1': 'value1',
            'var2': 'value2'
        }
    }

    response, error = make_request('POST', '/api-automation/environments/', env_data)

    if error or response['status_code'] != 201:
        log_test("Environment", "创建环境", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    environment = response['data']
    test_data['environment_id'] = environment['id']
    log_test("Environment", "创建环境", True, f"环境ID: {environment['id']}", environment)

    # 2. 获取环境列表
    response, error = make_request('GET', '/api-automation/environments/', params={'project': test_data['project_id']})
    if error or response['status_code'] != 200:
        log_test("Environment", "环境列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Environment", "环境列表", True, f"获取到 {count} 个环境")

    # 3. 测试连接
    test_conn_data = {
        'url': 'https://httpbin.org/get'
    }

    response, error = make_request('POST', f"/api-automation/environments/{test_data['environment_id']}/test-connection/", test_conn_data)
    if error or response['status_code'] != 200:
        log_test("Environment", "测试连接", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Environment", "测试连接", True, f"连接成功: {response['data'].get('success')}")

    # 4. 设置默认环境
    response, error = make_request('POST', f"/api-automation/environments/{test_data['environment_id']}/set-default/")
    if error or response['status_code'] != 200:
        log_test("Environment", "设置默认环境", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Environment", "设置默认环境", True, f"默认环境已设置")

    # 5. 导出环境
    response, error = make_request('GET', f"/api-automation/environments/{test_data['environment_id']}/export/")
    if error or response['status_code'] != 200:
        log_test("Environment", "导出环境", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("Environment", "导出环境", True, f"导出数据包含: {list(response['data'].keys())}")


def test_test_case_management():
    """测试用例管理API"""
    print("\n=== 测试测试用例管理API ===")

    # 1. 创建测试用例
    case_data = {
        'project': test_data['project_id'],
        'collection': test_data['collection_id'],
        'name': '测试用例_API测试',
        'request_method': 'GET',
        'request_url': 'https://httpbin.org/get',
        'description': 'API测试用例'
    }

    response, error = make_request('POST', '/api-automation/test-cases/', case_data)

    if error or response['status_code'] != 201:
        log_test("TestCase", "创建测试用例", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    test_case = response['data']
    test_data['test_case_id'] = test_case['id']
    log_test("TestCase", "创建测试用例", True, f"测试用例ID: {test_case['id']}", test_case)

    # 2. 获取测试用例列表
    response, error = make_request('GET', '/api-automation/test-cases/', params={'project': test_data['project_id']})
    if error or response['status_code'] != 200:
        log_test("TestCase", "测试用例列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("TestCase", "测试用例列表", True, f"获取到 {count} 个测试用例")

    # 3. 获取测试用例详情
    response, error = make_request('GET', f"/api-automation/test-cases/{test_data['test_case_id']}/")
    if error or response['status_code'] != 200:
        log_test("TestCase", "测试用例详情", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("TestCase", "测试用例详情", True, f"测试用例名称: {response['data']['name']}")

    # 4. 更新测试用例
    update_data = {
        'project': test_data['project_id'],
        'collection': test_data['collection_id'],
        'name': '测试用例_API测试_已更新',
        'request_method': 'GET',
        'request_url': 'https://httpbin.org/get'
    }

    response, error = make_request('PUT', f"/api-automation/test-cases/{test_data['test_case_id']}/", update_data)
    if error or response['status_code'] != 200:
        log_test("TestCase", "更新测试用例", False, error or f"状态码: {response['status_code']}")
    else:
        log_test("TestCase", "更新测试用例", True, f"更新后名称: {response['data']['name']}")

    # 5. 克隆测试用例
    response, error = make_request('POST', f"/api-automation/test-cases/{test_data['test_case_id']}/clone/")
    if error or response['status_code'] not in [200, 201]:
        log_test("TestCase", "克隆测试用例", False, error or f"状态码: {response['status_code']}")
    else:
        cloned_id = response['data']['id']
        log_test("TestCase", "克隆测试用例", True, f"克隆测试用例ID: {cloned_id}")
        # 清理克隆的测试用例
        make_request('DELETE', f"/api-automation/test-cases/{cloned_id}/")


def test_assertion_management():
    """测试断言管理API"""
    print("\n=== 测试断言管理API ===")

    # 1. 创建断言
    assertion_data = {
        'test_case': test_data['test_case_id'],
        'assertion_type': 'status_code',
        'operator': 'equals',
        'expected_value': '200',
        'description': '状态码断言',
        'is_enabled': True,
        'sort_order': 1
    }

    response, error = make_request('POST', '/api-automation/assertions/', assertion_data)

    if error or response['status_code'] != 201:
        log_test("Assertion", "创建断言", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    assertion = response['data']
    test_data['assertion_id'] = assertion['id']
    log_test("Assertion", "创建断言", True, f"断言ID: {assertion['id']}", assertion)

    # 2. 获取断言列表
    response, error = make_request('GET', '/api-automation/assertions/', params={'test_case': test_data['test_case_id']})
    if error or response['status_code'] != 200:
        log_test("Assertion", "断言列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Assertion", "断言列表", True, f"获取到 {count} 个断言")

    # 3. 创建多个断言用于批量操作
    assertion_data2 = {
        'test_case': test_data['test_case_id'],
        'assertion_type': 'response_time',
        'operator': 'less_than',
        'expected_value': '1000',
        'description': '响应时间断言',
        'is_enabled': True,
        'sort_order': 2
    }

    response, error = make_request('POST', '/api-automation/assertions/', assertion_data2)
    if not error and response['status_code'] == 201:
        assertion2_id = response['data']['id']

        # 4. 批量更新顺序
        batch_data = {
            'orders': [
                {'id': test_data['assertion_id'], 'sort_order': 1},
                {'id': assertion2_id, 'sort_order': 2}
            ]
        }

        response, error = make_request('POST', '/api-automation/assertions/batch-update-order/', batch_data)
        if error or response['status_code'] != 200:
            log_test("Assertion", "批量更新顺序", False, error or f"状态码: {response['status_code']}")
        else:
            log_test("Assertion", "批量更新顺序", True, "顺序已更新")


def test_extraction_management():
    """测试数据提取管理API"""
    print("\n=== 测试数据提取管理API ===")

    # 1. 创建数据提取
    extraction_data = {
        'test_case': test_data['test_case_id'],
        'extraction_type': 'json_path',
        'expression': '$.data.id',
        'variable_name': 'extracted_id',
        'description': '提取ID字段',
        'is_enabled': True
    }

    response, error = make_request('POST', '/api-automation/extractions/', extraction_data)

    if error or response['status_code'] != 201:
        log_test("Extraction", "创建数据提取", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    extraction = response['data']
    test_data['extraction_id'] = extraction['id']
    log_test("Extraction", "创建数据提取", True, f"数据提取ID: {extraction['id']}", extraction)

    # 2. 获取数据提取列表
    response, error = make_request('GET', '/api-automation/extractions/', params={'test_case': test_data['test_case_id']})
    if error or response['status_code'] != 200:
        log_test("Extraction", "数据提取列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Extraction", "数据提取列表", True, f"获取到 {count} 个数据提取")


def test_execution_management():
    """测试执行管理API"""
    print("\n=== 测试执行管理API ===")

    # 1. 执行单个测试用例
    run_data = {
        'environment_id': test_data['environment_id']
    }

    response, error = make_request('POST', f"/api-automation/test-cases/{test_data['test_case_id']}/run/", run_data)

    if error or response['status_code'] not in [200, 201]:
        log_test("Execution", "执行测试用例", False, error or f"状态码: {response['status_code']}", response.get('data') if not error else None)
        return

    execution = response['data']
    test_data['execution_id'] = execution.get('id')
    log_test("Execution", "执行测试用例", True, f"执行ID: {execution.get('id')}, 状态: {execution.get('status')}", execution)

    # 2. 获取执行列表
    response, error = make_request('GET', '/api-automation/executions/')
    if error or response['status_code'] != 200:
        log_test("Execution", "执行列表", False, error or f"状态码: {response['status_code']}")
    else:
        count = len(response['data'].get('results', response['data']))
        log_test("Execution", "执行列表", True, f"获取到 {count} 条执行记录")

    # 3. 获取执行详情（如果有ID）
    if test_data['execution_id']:
        response, error = make_request('GET', f"/api-automation/executions/{test_data['execution_id']}/")
        if error or response['status_code'] != 200:
            log_test("Execution", "执行详情", False, error or f"状态码: {response['status_code']}")
        else:
            log_test("Execution", "执行详情", True, f"执行状态: {response['data']['status']}")


def test_dashboard_apis():
    """测试仪表盘API"""
    print("\n=== 测试仪表盘API ===")

    # 1. 概览数据
    response, error = make_request('GET', '/api-automation/dashboard/overview/')
    if error or response['status_code'] != 200:
        log_test("Dashboard", "概览数据", False, error or f"状态码: {response['status_code']}")
    else:
        data = response['data']
        log_test("Dashboard", "概览数据", True, f"总项目数: {data.get('total_projects')}, 总用例数: {data.get('total_test_cases')}")

    # 2. 环境报告
    response, error = make_request('GET', '/api-automation/dashboard/environment-report/', params={'environment_id': test_data['environment_id']})
    if error or response['status_code'] != 200:
        log_test("Dashboard", "环境报告", False, error or f"状态码: {response['status_code']}")
    else:
        data = response['data']
        log_test("Dashboard", "环境报告", True, f"测试用例数: {data.get('total_test_cases')}, 通过率: {data.get('pass_rate')}%")

    # 3. 集合报告
    response, error = make_request('GET', '/api-automation/dashboard/collection-report/', params={'collection_id': test_data['collection_id']})
    if error or response['status_code'] != 200:
        log_test("Dashboard", "集合报告", False, error or f"状态码: {response['status_code']}")
    else:
        data = response['data']
        log_test("Dashboard", "集合报告", True, f"测试用例数: {data.get('total_test_cases')}, 通过率: {data.get('pass_rate')}%")

    # 4. 图表数据
    response, error = make_request('GET', '/api-automation/dashboard/chart-data/')
    if error or response['status_code'] != 200:
        log_test("Dashboard", "图表数据", False, error or f"状态码: {response['status_code']}")
    else:
        data = response['data']
        log_test("Dashboard", "图表数据", True, f"包含图表: {list(data.keys())}")


def test_permissions():
    """测试权限控制"""
    print("\n=== 测试权限控制 ===")

    # 1. 测试未认证访问（不携带token）
    global auth_token
    original_token = auth_token
    auth_token = None

    response, error = make_request('GET', '/api-automation/projects/', need_auth=False)

    auth_token = original_token  # 恢复token

    # 应该返回401或403
    if response and response['status_code'] in [401, 403]:
        log_test("Permission", "未认证访问保护", True, f"正确返回 {response['status_code']}")
    else:
        log_test("Permission", "未认证访问保护", False, f"未正确保护，状态码: {response.get('status_code') if response else 'None'}")


def test_data_validation():
    """测试数据验证"""
    print("\n=== 测试数据验证 ===")

    # 1. 测试必填字段缺失
    invalid_data = {
        'description': '缺少name字段'
    }

    response, error = make_request('POST', '/api-automation/projects/', invalid_data)

    if response and response['status_code'] == 400:
        log_test("Validation", "必填字段验证", True, "正确拒绝缺少必填字段的请求")
    else:
        log_test("Validation", "必填字段验证", False, f"未正确验证，状态码: {response.get('status_code') if response else 'None'}")

    # 2. 测试无效的请求方法
    response, error = make_request('POST', '/api-automation/test-cases/', {})

    if response and response['status_code'] == 400:
        log_test("Validation", "无效数据验证", True, "正确拒绝无效数据")
    else:
        log_test("Validation", "无效数据验证", False, f"未正确验证，状态码: {response.get('status_code') if response else 'None'}")


def cleanup_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")

    # 按照依赖关系逆序删除
    cleanup_order = [
        ('execution', f"/api-automation/executions/{test_data['execution_id']}/") if test_data['execution_id'] else None,
        ('extraction', f"/api-automation/extractions/{test_data['extraction_id']}/") if test_data['extraction_id'] else None,
        ('assertion', f"/api-automation/assertions/{test_data['assertion_id']}/") if test_data['assertion_id'] else None,
        ('test_case', f"/api-automation/test-cases/{test_data['test_case_id']}/") if test_data['test_case_id'] else None,
        ('collection', f"/api-automation/collections/{test_data['collection_id']}/") if test_data['collection_id'] else None,
        ('environment', f"/api-automation/environments/{test_data['environment_id']}/") if test_data['environment_id'] else None,
        ('project', f"/api-automation/projects/{test_data['project_id']}/") if test_data['project_id'] else None,
    ]

    for item in cleanup_order:
        if item:
            name, endpoint = item
            response, error = make_request('DELETE', endpoint)
            if error or response['status_code'] not in [200, 204]:
                print(f"  [WARNING] 清理{name}失败: {error or response.get('status_code')}")
            else:
                print(f"  [OK] 清理{name}成功")


def print_summary():
    """打印测试摘要"""
    print("\n" + "="*80)
    print("测试摘要报告")
    print("="*80)

    total_passed = len(test_results['passed'])
    total_failed = len(test_results['failed'])
    total_warnings = len(test_results['warnings'])
    total_tests = total_passed + total_failed

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {total_passed} [OK]")
    print(f"失败: {total_failed} [FAIL]")
    print(f"警告: {total_warnings} [WARN]")
    print(f"通过率: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "通过率: N/A")

    # 失败测试详情
    if test_results['failed']:
        print("\n" + "-"*80)
        print("失败测试详情:")
        print("-"*80)
        for fail in test_results['failed']:
            print(f"\n[{fail['name']}]")
            print(f"  原因: {fail['message']}")
            if fail['details']:
                print(f"  详情: {fail['details']}")

    # 警告详情
    if test_results['warnings']:
        print("\n" + "-"*80)
        print("警告详情:")
        print("-"*80)
        for warning in test_results['warnings']:
            print(f"\n[{warning['name']}]")
            print(f"  警告: {warning['message']}")
            if warning['details']:
                print(f"  详情: {warning['details']}")

    print("\n" + "="*80)

    # 测试覆盖率估算
    api_endpoints = [
        'Auth Login',
        'Project CRUD (6)',
        'Collection CRUD (6)',
        'TestCase CRUD (6)',
        'Environment CRUD (6)',
        'Assertion CRUD (5)',
        'Extraction CRUD (4)',
        'Execution CRUD (4)',
        'Dashboard (4)',
        'Permissions',
        'Validation'
    ]

    print(f"\n测试覆盖率: 已测试 {len(api_endpoints)} 个主要API模块")
    print(f"总计约 50+ 个独立端点")


def main():
    """主测试函数"""
    test_results['start_time'] = datetime.now()

    print("="*80)
    print("后端API全面测试")
    print("="*80)
    print(f"开始时间: {test_results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务器: {BASE_URL}")

    try:
        # 1. Swagger文档访问测试
        test_swagger_access()

        # 2. 认证测试
        if not test_auth_login():
            print("\n[ERROR] 认证失败，终止测试")
            return

        # 3. 核心功能测试
        test_project_management()
        test_collection_management()
        test_environment_management()
        test_test_case_management()
        test_assertion_management()
        test_extraction_management()
        test_execution_management()
        test_dashboard_apis()

        # 4. 权限和验证测试
        test_permissions()
        test_data_validation()

        # 5. 清理测试数据
        cleanup_test_data()

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        try:
            cleanup_test_data()
        except:
            pass

        test_results['end_time'] = datetime.now()
        print_summary()


if __name__ == '__main__':
    main()
