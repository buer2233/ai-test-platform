"""
测试登录API的响应内容
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

# 测试登录
login_data = {
    'username': 'admin',
    'password': 'admin123'
}

print("测试登录API...")
print(f"URL: {BASE_URL}/api/v1/auth/login/")
print(f"数据: {login_data}")
print("-" * 80)

response = requests.post(
    f"{BASE_URL}/api/v1/auth/login/",
    json=login_data,
    timeout=10
)

print(f"状态码: {response.status_code}")
print(f"响应头:")
for key, value in response.headers.items():
    print(f"  {key}: {value}")

print(f"\n响应内容类型: {response.headers.get('content-type')}")
print(f"\n原始响应文本:")
print(response.text)
print("-" * 80)

if response.headers.get('content-type', '').startswith('application/json'):
    try:
        data = response.json()
        print(f"\n解析后的JSON:")
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print("JSON解析失败")
