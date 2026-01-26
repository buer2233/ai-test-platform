"""
调试API失败的原因
"""
import os
import sys
import django
import requests
import json

# Django环境设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

# 获取admin的token
admin = User.objects.get(username='admin')
token = Token.objects.get(user=admin)

BASE_URL = "http://127.0.0.1:8000"
headers = {'Authorization': f'Token {token.key}'}

print("="*80)
print("API失败原因调试")
print("="*80)

# 1. 测试集合克隆
print("\n1. 测试集合克隆:")
try:
    response = requests.post(
        f"{BASE_URL}/api/v1/api-automation/collections/6/clone/",
        headers=headers,
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"异常: {e}")

# 2. 测试环境连接测试
print("\n2. 测试环境连接:")
try:
    test_data = {'url': 'https://httpbin.org/get'}
    response = requests.post(
        f"{BASE_URL}/api/v1/api-automation/environments/8/test-connection/",
        json=test_data,
        headers=headers,
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"响应内容: {response.text[:500]}")
except Exception as e:
    print(f"异常: {e}")

# 3. 测试创建测试用例
print("\n3. 测试创建测试用例:")
try:
    case_data = {
        'project': 9,
        'collection': 6,
        'name': '测试用例',
        'request_method': 'GET',
        'request_url': 'https://httpbin.org/get'
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/api-automation/test-cases/",
        json=case_data,
        headers=headers,
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"响应内容: {response.text[:500]}")
    if response.status_code == 201:
        data = response.json()
        test_case_id = data.get('id')
        print(f"创建的测试用例ID: {test_case_id}")

        # 4. 测试创建断言
        print("\n4. 测试创建断言:")
        assertion_data = {
            'test_case': test_case_id,
            'assertion_type': 'status_code',
            'operator': 'equals',
            'expected_value': '200',
            'description': '状态码断言',
            'is_enabled': True,
            'sort_order': 1
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/api-automation/assertions/",
            json=assertion_data,
            headers=headers,
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"响应内容: {response.text[:500]}")

        # 5. 测试Dashboard
        print("\n5. 测试Dashboard概览:")
        response = requests.get(
            f"{BASE_URL}/api/v1/api-automation/dashboard/overview/",
            headers=headers,
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"响应内容: {response.text[:500]}")

except Exception as e:
    print(f"异常: {e}")

print("\n" + "="*80)
