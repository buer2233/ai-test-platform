"""
检查认证设置和获取token
"""
import os
import sys
import django

# Django环境设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

print("=" * 80)
print("检查认证设置")
print("=" * 80)

# 1. 检查现有用户
print("\n1. 现有用户:")
users = User.objects.all()
for user in users:
    print(f"   - {user.username} (ID: {user.id}, 活跃: {user.is_active})")

# 2. 检查或创建admin用户
print("\n2. 检查admin用户:")
try:
    admin = User.objects.get(username='admin')
    print(f"   Admin用户存在 (ID: {admin.id})")
except User.DoesNotExist:
    print("   Admin用户不存在，正在创建...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print(f"   Admin用户已创建 (ID: {admin.id})")

# 3. 获取或创建admin的token
print("\n3. Token信息:")
token, created = Token.objects.get_or_create(user=admin)
print(f"   Token: {token.key}")
print(f"   新创建: {created}")

# 4. 测试API认证
import requests

BASE_URL = "http://127.0.0.1:8000"

print("\n4. 测试API端点:")

# 测试使用token访问项目列表
headers = {
    'Authorization': f'Token {token.key}'
}

response = requests.get(
    f"{BASE_URL}/api/v1/api-automation/projects/",
    headers=headers,
    timeout=5
)

print(f"   GET /api/v1/api-automation/projects/")
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ 认证成功!")
    data = response.json()
    print(f"   返回数据: {data}")
else:
    print(f"   ✗ 认证失败")
    print(f"   响应: {response.text[:200]}")

print("\n" + "=" * 80)
