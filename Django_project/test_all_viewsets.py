"""
全面测试ViewSet的所有操作
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import requests

User = get_user_model()

# 获取admin token
admin = User.objects.get(username='admin')
token = Token.objects.get(user=admin)

BASE_URL = "http://127.0.0.1:8000"
headers = {'Authorization': f'Token {token.key}'}

print("="*80)
print("ViewSet操作全面测试")
print("="*80)

# 1. 测试项目管理 - Projects
print("\n=== Projects ===")
response = requests.get(f"{BASE_URL}/api/v1/api-automation/projects/", headers=headers)
print(f"GET /projects/ : {response.status_code}")

if response.status_code == 200:
    projects = response.json().get('results', response.json())
    if projects:
        project_id = projects[0].get('id')
        print(f"  项目ID: {project_id}")

        # 测试项目详情
        response = requests.get(f"{BASE_URL}/api/v1/api-automation/projects/{project_id}/", headers=headers)
        print(f"GET /projects/{project_id}/ : {response.status_code}")

        # 测试自定义操作
        custom_actions = ['clone', 'statistics', 'export']
        for action in custom_actions:
            response = requests.post(f"{BASE_URL}/api/v1/api-automation/projects/{project_id}/{action}/", headers=headers)
            if response.status_code == 404:
                # 尝试GET方法
                response = requests.get(f"{BASE_URL}/api/v1/api-automation/projects/{project_id}/{action}/", headers=headers)
            print(f"POST /projects/{project_id}/{action}/ : {response.status_code}")

# 2. 测试集合管理 - Collections
print("\n=== Collections ===")
response = requests.get(f"{BASE_URL}/api/v1/api-automation/collections/", headers=headers)
print(f"GET /collections/ : {response.status_code}")

if response.status_code == 200:
    collections = response.json().get('results', response.json())
    if collections:
        collection_id = collections[0].get('id')
        print(f"  集合ID: {collection_id}")

        # 测试集合详情
        response = requests.get(f"{BASE_URL}/api/v1/api-automation/collections/{collection_id}/", headers=headers)
        print(f"GET /collections/{collection_id}/ : {response.status_code}")

        # 测试自定义操作
        custom_actions = ['clone', 'run_test', 'test_cases']
        for action in custom_actions:
            url = f"{BASE_URL}/api/v1/api-automation/collections/{collection_id}/{action}/"
            if action == 'test_cases':
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers)
            if response.status_code == 404 and action != 'test_cases':
                response = requests.get(url, headers=headers)
            print(f"{'POST' if action != 'test_cases' else 'GET'} /collections/{collection_id}/{action}/ : {response.status_code}")

# 3. 测试环境管理 - Environments
print("\n=== Environments ===")
response = requests.get(f"{BASE_URL}/api/v1/api-automation/environments/", headers=headers)
print(f"GET /environments/ : {response.status_code}")

if response.status_code == 200:
    envs = response.json().get('results', response.json())
    if envs:
        env_id = envs[0].get('id')
        print(f"  环境ID: {env_id}")

        # 测试环境详情
        response = requests.get(f"{BASE_URL}/api/v1/api-automation/environments/{env_id}/", headers=headers)
        print(f"GET /environments/{env_id}/ : {response.status_code}")

        # 测试自定义操作
        custom_actions = ['test-connection', 'set-default', 'export', 'import']
        for action in custom_actions:
            url = f"{BASE_URL}/api/v1/api-automation/environments/{env_id}/{action}/"
            if action in ['test-connection', 'set-default']:
                method = 'POST'
            else:
                method = 'GET'

            if method == 'POST':
                response = requests.post(url, headers=headers, json={'url': 'https://httpbin.org'} if action == 'test-connection' else None)
            else:
                response = requests.get(url, headers=headers)

            if response.status_code == 404:
                # 尝试下划线格式
                url_alt = f"{BASE_URL}/api/v1/api-automation/environments/{env_id}/{action.replace('-', '_')}/"
                if method == 'POST':
                    response = requests.post(url_alt, headers=headers, json={'url': 'https://httpbin.org'} if 'test' in action else None)
                else:
                    response = requests.get(url_alt, headers=headers)

            print(f"{method} /environments/{env_id}/{action}/ : {response.status_code}")

# 4. 测试测试用例 - TestCases
print("\n=== TestCases ===")
response = requests.get(f"{BASE_URL}/api/v1/api-automation/test-cases/", headers=headers)
print(f"GET /test-cases/ : {response.status_code}")

if response.status_code == 200:
    test_cases = response.json().get('results', response.json())
    if test_cases:
        case_id = test_cases[0].get('id')
        print(f"  测试用例ID: {case_id}")

        # 测试自定义操作
        custom_actions = ['clone', 'run']
        for action in custom_actions:
            response = requests.post(f"{BASE_URL}/api/v1/api-automation/test-cases/{case_id}/{action}/", headers=headers)
            if response.status_code == 404:
                response = requests.get(f"{BASE_URL}/api/v1/api-automation/test-cases/{case_id}/{action}/", headers=headers)
            print(f"POST /test-cases/{case_id}/{action}/ : {response.status_code}")

# 5. 测试断言 - Assertions
print("\n=== Assertions (嵌套路由) ===")
if test_cases:
    case_id = test_cases[0].get('id')
    response = requests.get(f"{BASE_URL}/api/v1/api-automation/test-cases/{case_id}/assertions/", headers=headers)
    print(f"GET /test-cases/{case_id}/assertions/ : {response.status_code}")

# 6. 测试数据提取 - Extractions
print("\n=== Extractions (嵌套路由) ===")
if test_cases:
    case_id = test_cases[0].get('id')
    response = requests.get(f"{BASE_URL}/api/v1/api-automation/test-cases/{case_id}/extractions/", headers=headers)
    print(f"GET /test-cases/{case_id}/extractions/ : {response.status_code}")

# 7. 测试Dashboard
print("\n=== Dashboard ===")
dashboard_endpoints = [
    'overview/',
    'environment-report/',
    'collection-report/',
    'chart-data/',
    'recent-executions/',
    'failed-test-cases/'
]
for endpoint in dashboard_endpoints:
    response = requests.get(f"{BASE_URL}/api/v1/api-automation/dashboard/{endpoint}", headers=headers)
    print(f"GET /dashboard/{endpoint} : {response.status_code}")

print("\n" + "="*80)
