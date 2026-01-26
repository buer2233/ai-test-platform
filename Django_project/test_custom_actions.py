"""
测试自定义操作的URL格式
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()
admin = User.objects.get(username='admin')
token = Token.objects.get(user=admin)

BASE_URL = "http://127.0.0.1:8000"
headers = {'Authorization': f'Token {token.key}'}

print("测试自定义操作的URL格式")
print("="*80)

# 测试不同的URL格式
test_urls = [
    ("集合克隆 - 格式1", f"{BASE_URL}/api/v1/api-automation/collections/6/clone/"),
    ("集合克隆 - 格式2", f"{BASE_URL}/api/v1/api-automation/collections/6/clone"),
    ("环境测试连接 - 格式1", f"{BASE_URL}/api/v1/api-automation/environments/8/test_connection/"),
    ("环境测试连接 - 格式2", f"{BASE_URL}/api/v1/api-automation/environments/8/test-connection/"),
    ("项目克隆", f"{BASE_URL}/api/v1/api-automation/projects/9/clone/"),
]

for name, url in test_urls:
    print(f"\n{name}:")
    print(f"  URL: {url}")
    try:
        if 'test' in url.lower():
            response = requests.get(url, headers=headers, timeout=5)
        else:
            response = requests.post(url, headers=headers, timeout=5)

        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"  [成功]")
            try:
                data = response.json()
                print(f"  数据: {str(data)[:100]}")
            except:
                pass
        elif response.status_code == 404:
            print(f"  [不存在]")
        else:
            print(f"  [其他错误] {response.text[:100]}")
    except Exception as e:
        print(f"  [异常] {e}")

print("\n" + "="*80)
