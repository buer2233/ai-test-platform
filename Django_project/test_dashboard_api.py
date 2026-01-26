# -*- coding: utf-8 -*-
"""
仪表盘API端点测试脚本
测试所有仪表盘相关的API接口
"""
import os
import sys
import django
import json

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import override_settings
from rest_framework.test import APIClient
from api_automation.models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
    ApiTestExecution, ApiTestResult
)

# API 基础 URL
BASE_URL = '/api/v1/api-automation'


@override_settings(ALLOWED_HOSTS=['*'])
def test_dashboard_overview(client):
    """测试仪表盘概览API - TC-DASH-001"""
    print("=== TC-DASH-001: 仪表盘概览API ===")

    response = client.get(f'{BASE_URL}/dashboard/')
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        # 验证返回数据结构
        assert 'overview' in data, "缺少overview字段"
        assert 'test_stats' in data, "缺少test_stats字段"
        assert 'recent_results' in data, "缺少recent_results字段"

        print(f"  - 项目数: {data['overview']['total_projects']}")
        print(f"  - 用例总数: {data['test_stats']['total_cases']}")
        print(f"  - 通过率: {data['test_stats']['pass_rate']}%")
        print("PASS: 仪表盘概览API返回数据正确")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_environment_reports_api(client):
    """测试环境维度报告API - TC-DASH-003"""
    print("\n=== TC-DASH-003: 环境维度报告API ===")

    response = client.get(f'{BASE_URL}/dashboard/environment_reports/')
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        print(f"Environment Count: {data.get('count', 0)}")

        assert 'results' in data, "缺少results字段"
        assert 'count' in data, "缺少count字段"

        results = data['results']
        for env_report in results[:3]:  # 只打印前3个
            print(f"  - {env_report.get('environment_name')}: 通过率 {env_report.get('stats', {}).get('pass_rate', 0)}%")
        print(f"PASS: 环境维度报告API返回{len(results)}条记录")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_collection_reports_api(client):
    """测试集合维度报告API - TC-DASH-004"""
    print("\n=== TC-DASH-004: 集合维度报告API ===")

    response = client.get(f'{BASE_URL}/dashboard/collection_reports/')
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")
        print(f"Collection Count: {data.get('count', 0)}")

        assert 'results' in data, "缺少results字段"
        assert 'count' in data, "缺少count字段"

        results = data['results']
        for col_report in results[:3]:  # 只打印前3个
            print(f"  - {col_report.get('collection_name')}: 用例数 {col_report.get('test_case_count', 0)}")
        print(f"PASS: 集合维度报告API返回{len(results)}条记录")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_chart_data_api(client):
    """测试图表数据API - TC-DASH-005"""
    print("\n=== TC-DASH-005: 图表数据API ===")

    response = client.get(f'{BASE_URL}/dashboard/chart_data/')
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        assert 'pass_rate_pie' in data, "缺少pass_rate_pie字段"
        assert 'response_time_trend' in data, "缺少response_time_trend字段"
        assert 'method_distribution' in data, "缺少method_distribution字段"

        print(f"通过率饼图: {data['pass_rate_pie']}")
        print(f"趋势数据点数: {len(data['response_time_trend'])}")
        print(f"HTTP方法分布: {data['method_distribution']}")

        print("PASS: 图表数据API返回数据完整")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_test_results_api(client):
    """测试测试结果列表API - TC-DASH-006"""
    print("\n=== TC-DASH-006: 测试结果列表API ===")

    # 测试分页
    response = client.get(f'{BASE_URL}/dashboard/test_results/', {'page': 1, 'page_size': 10})
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        assert 'results' in data, "缺少results字段"
        assert 'count' in data, "缺少count字段"

        print(f"总记录数: {data['count']}")
        print(f"当前页记录数: {len(data['results'])}")
        print("PASS: 测试结果列表API返回数据正确")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_execute_environment_api(client):
    """测试执行环境API - TC-DASH-013"""
    print("\n=== TC-DASH-013: 执行环境API ===")

    # 获取第一个环境
    environment = ApiTestEnvironment.objects.filter(is_deleted=False).first()
    if not environment:
        print("SKIP: 没有测试环境")
        return True

    response = client.post(f'{BASE_URL}/dashboard/execute_environment/', {
        'environment_id': environment.id
    })
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        assert 'execution_id' in data, "缺少execution_id字段"
        assert 'message' in data, "缺少message字段"

        print(f"执行ID: {data['execution_id']}")
        print(f"消息: {data['message']}")
        print("PASS: 执行环境API返回正常")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_execute_collection_api(client):
    """测试执行集合API - TC-DASH-014"""
    print("\n=== TC-DASH-014: 执行集合API ===")

    # 获取第一个集合和环境
    collection = ApiCollection.objects.filter(is_deleted=False).first()
    environment = ApiTestEnvironment.objects.filter(is_deleted=False).first()

    if not collection or not environment:
        print("SKIP: 没有测试集合或环境")
        return True

    # 确保集合和环境属于同一项目
    if collection.project_id != environment.project_id:
        print("SKIP: 集合和环境不属于同一项目")
        return True

    response = client.post(f'{BASE_URL}/dashboard/execute_collection/', {
        'collection_id': collection.id,
        'environment_id': environment.id
    })
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        assert 'execution_id' in data, "缺少execution_id字段"

        print(f"执行ID: {data['execution_id']}")
        print("PASS: 执行集合API返回正常")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def test_retry_failed_api(client):
    """测试重试失败用例API - TC-DASH-015"""
    print("\n=== TC-DASH-015: 重试失败用例API ===")

    # 获取有失败结果的执行记录
    execution = ApiTestExecution.objects.filter(
        is_deleted=False
    ).order_by('-created_time').first()

    if not execution:
        print("SKIP: 没有执行记录")
        return True

    response = client.post(f'{BASE_URL}/dashboard/retry_failed/', {
        'execution_id': execution.id
    })
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response Keys: {list(data.keys())}")

        assert 'message' in data, "缺少message字段"

        print(f"消息: {data['message']}")
        print("PASS: 重试失败用例API返回正常")
        return True
    else:
        print(f"FAIL: API调用失败 - {response.content}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def run_all_api_tests():
    """运行所有API测试"""
    print("="*60)
    print("开始仪表盘API端点测试")
    print("="*60)

    client = APIClient()

    # 创建或获取测试用户
    from django.contrib.auth.models import User
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('test_pass123')
        user.save()
        print(f"创建测试用户: {user.username}")

    # 强制认证
    client.force_authenticate(user=user)
    print(f"使用用户认证: {user.username}")

    tests = [
        test_dashboard_overview,
        test_environment_reports_api,
        test_collection_reports_api,
        test_chart_data_api,
        test_test_results_api,
        test_execute_environment_api,
        test_execute_collection_api,
        test_retry_failed_api,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test(client):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"API测试结果: {passed} 通过, {failed} 失败")
    print("="*60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_api_tests()
    sys.exit(0 if success else 1)
