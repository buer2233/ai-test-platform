"""
生成完整的API测试报告
"""
import os
import django
import requests
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()
admin = User.objects.get(username='admin')
token = Token.objects.get(user=admin)

BASE_URL = "http://127.0.0.1:8000"
headers = {'Authorization': f'Token {token.key}'}

report = {
    'timestamp': datetime.now().isoformat(),
    'base_url': BASE_URL,
    'tests': []
}

def test_endpoint(category, name, url, method='GET', data=None, params=None):
    """测试单个端点"""
    full_url = f"{BASE_URL}/api/v1/api-automation/{url}"
    try:
        if method == 'GET':
            response = requests.get(full_url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(full_url, headers=headers, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(full_url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(full_url, headers=headers, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(full_url, headers=headers, json=data, timeout=10)

        result = {
            'category': category,
            'name': name,
            'url': url,
            'method': method,
            'status_code': response.status_code,
            'success': 200 <= response.status_code < 300,
            'response_time': response.elapsed.total_seconds()
        }

        # 尝试解析响应
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                result['response_data'] = response.json()
            else:
                result['response_text'] = response.text[:200]
        except:
            pass

        report['tests'].append(result)
        return result

    except Exception as e:
        report['tests'].append({
            'category': category,
            'name': name,
            'url': url,
            'method': method,
            'error': str(e),
            'success': False
        })
        return None

print("正在执行完整的API测试...")

# 1. 认证相关
print("\n1. 认证相关...")
test_endpoint('Auth', '当前用户信息', 'auth/user/')

# 2. 项目管理
print("\n2. 项目管理...")
test_endpoint('Project', '项目列表', 'projects/')
test_endpoint('Project', '项目详情', 'projects/1/')
test_endpoint('Project', '项目克隆', 'projects/1/clone/', 'POST')

# 3. 集合管理
print("\n3. 集合管理...")
test_endpoint('Collection', '集合列表', 'collections/')
test_endpoint('Collection', '集合详情', 'collections/1/')
test_endpoint('Collection', '集合的测试用例', 'collections/1/test_cases/')

# 4. 测试用例管理
print("\n4. 测试用例管理...")
test_endpoint('TestCase', '测试用例列表', 'test-cases/')
test_endpoint('TestCase', '测试用例详情', 'test-cases/1/')
test_endpoint('TestCase', '测试用例克隆', 'test-cases/1/clone/', 'POST')

# 5. 环境管理
print("\n5. 环境管理...")
test_endpoint('Environment', '环境列表', 'environments/')
test_endpoint('Environment', '环境详情', 'environments/1/')
test_endpoint('Environment', '环境连接测试', 'environments/1/test_connection/', 'GET')
test_endpoint('Environment', '设置默认环境', 'environments/1/set-default/', 'POST')

# 6. 执行管理
print("\n6. 执行管理...")
test_endpoint('Execution', '执行列表', 'executions/')
test_endpoint('Execution', '执行详情', 'executions/1/')

# 7. 报告管理
print("\n7. 报告管理...")
test_endpoint('Report', '报告列表', 'reports/')

# 8. Dashboard
print("\n8. Dashboard...")
test_endpoint('Dashboard', 'Dashboard列表', 'dashboard/')
test_endpoint('Dashboard', '环境报告', 'dashboard/environment_reports/')
test_endpoint('Dashboard', '集合报告', 'dashboard/collection_reports/')

# 9. 断言（嵌套）
print("\n9. 断言配置...")
test_endpoint('Assertion', '测试用例断言列表', 'test-cases/1/assertions/')

# 10. 数据提取（嵌套）
print("\n10. 数据提取...")
test_endpoint('Extraction', '测试用例数据提取列表', 'test-cases/1/extractions/')

# 11. HTTP执行器
print("\n11. HTTP执行器...")
test_endpoint('HttpExecutor', '执行历史', 'test-execute/history/')

# 生成统计
total_tests = len(report['tests'])
successful_tests = len([t for t in report['tests'] if t.get('success', False)])
failed_tests = total_tests - successful_tests

# 按类别分组
categories = {}
for test in report['tests']:
    cat = test['category']
    if cat not in categories:
        categories[cat] = {'total': 0, 'success': 0, 'failed': 0}
    categories[cat]['total'] += 1
    if test.get('success', False):
        categories[cat]['success'] += 1
    else:
        categories[cat]['failed'] += 1

# 打印报告
print("\n" + "="*80)
print("API测试完整报告")
print("="*80)
print(f"测试时间: {report['timestamp']}")
print(f"服务器地址: {report['base_url']}")
print(f"\n总体统计:")
print(f"  总测试数: {total_tests}")
print(f"  成功: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
print(f"  失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")

print(f"\n分类统计:")
for cat, stats in sorted(categories.items()):
    print(f"  {cat}:")
    print(f"    总数: {stats['total']}, 成功: {stats['success']}, 失败: {stats['failed']}")

print(f"\n失败的端点详情:")
failed_tests_list = [t for t in report['tests'] if not t.get('success', False)]
if failed_tests_list:
    for test in failed_tests_list:
        print(f"\n  [{test['category']}] {test['name']}")
        print(f"    URL: {test['url']}")
        print(f"    方法: {test['method']}")
        print(f"    状态码: {test.get('status_code', 'N/A')}")
        if 'error' in test:
            print(f"    错误: {test['error']}")
else:
    print("  无失败测试")

# 保存报告到文件
import json
with open('D:\\AI\\AI-test-project\\Django_project\\api_test_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n完整报告已保存到: D:\\AI\\AI-test-project\\Django_project\\api_test_report.json")
print("="*80)
