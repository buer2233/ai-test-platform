"""
集合详情和批量移除测试用例测试

测试问题：
1. 集合详情接口不应返回已删除的测试用例（is_deleted=True）
2. 批量移除接口应该正确移除测试用例
"""
import requests
import json
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1/api-automation"

# 获取认证token
def get_auth_token():
    """获取认证token"""
    auth_data = {
        "username": "admin",
        "password": "admin123"
    }
    # 使用Django REST Framework的Token认证
    resp = requests.post(f"{BASE_URL.replace('/api/v1/api-automation', '')}/api-token-auth/", data=auth_data)
    if resp.status_code == 200:
        return resp.json().get('token')
    return None

# 获取token
TOKEN = get_auth_token()
if TOKEN:
    HEADERS = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/json"
    }
    print(f"[INFO] 获取认证token成功")
else:
    HEADERS = {"Content-Type": "application/json"}
    print(f"[WARN] 无法获取认证token，尝试无认证访问")


def get_or_create_project():
    """获取或创建测试项目"""
    # 先尝试获取已有项目
    resp = requests.get(f"{BASE_URL}/projects/", headers=HEADERS)
    if resp.status_code == 200 and resp.json().get('results'):
        return resp.json()['results'][0]['id']

    # 创建新项目
    data = {
        "name": "测试项目-集合详情",
        "description": "用于测试集合详情和批量移除功能"
    }
    resp = requests.post(f"{BASE_URL}/projects/", json=data, headers=HEADERS)
    if resp.status_code == 201:
        print(f"[INFO] 创建项目成功，ID: {resp.json()['id']}")
        return resp.json()['id']
    return None


def get_or_create_collection(project_id):
    """获取或创建测试集合"""
    # 先尝试获取已有集合
    resp = requests.get(f"{BASE_URL}/collections/?project={project_id}", headers=HEADERS)
    if resp.status_code == 200 and resp.json().get('results'):
        return resp.json()['results'][0]['id']

    # 创建新集合
    data = {
        "name": "测试集合-详情测试",
        "project": project_id
    }
    resp = requests.post(f"{BASE_URL}/collections/", json=data, headers=HEADERS)
    if resp.status_code == 201:
        print(f"[INFO] 创建集合成功，ID: {resp.json()['id']}")
        return resp.json()['id']
    return None


def test_collection_detail_filters_deleted_test_cases():
    """
    问题2：测试集合详情接口正确过滤已删除的测试用例

    验证：当测试用例被软删除（is_deleted=True）后，
    集合详情接口不应返回这些已删除的测试用例
    """
    print("\n=== 测试1: 集合详情接口过滤已删除的测试用例 ===")

    # 准备测试数据
    project_id = get_or_create_project()
    collection_id = get_or_create_collection(project_id)

    # 创建3个测试用例
    test_case_ids = []
    for i in range(1, 4):
        data = {
            "name": f"测试用例-{i}",
            "project": project_id,
            "collection": collection_id,
            "method": "GET",
            "url": f"/test-{i}",
            "body": {},
            "headers": {},
            "params": {}
        }
        resp = requests.post(f"{BASE_URL}/test-cases/", json=data, headers=HEADERS)
        if resp.status_code == 201:
            test_case_ids.append(resp.json()['id'])
            print(f"[INFO] 创建测试用例-{i}，ID: {resp.json()['id']}")

    # 获取集合详情，验证有3个测试用例
    resp = requests.get(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    assert resp.status_code == 200, f"获取集合详情失败: {resp.status_code}"
    collection_data = resp.json()
    initial_count = len(collection_data.get('test_cases', []))
    print(f"[INFO] 集合详情初始测试用例数量: {initial_count}")
    assert initial_count == 3, f"期望3个测试用例，实际: {initial_count}"

    # 软删除第1个和第3个测试用例
    for test_case_id in [test_case_ids[0], test_case_ids[2]]:
        resp = requests.delete(f"{BASE_URL}/test-cases/{test_case_id}/", headers=HEADERS)
        assert resp.status_code == 204, f"删除测试用例失败: {resp.status_code}"
        print(f"[INFO] 软删除测试用例，ID: {test_case_id}")

    # 再次获取集合详情，验证只返回未删除的测试用例
    resp = requests.get(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    assert resp.status_code == 200, f"获取集合详情失败: {resp.status_code}"
    collection_data = resp.json()
    final_count = len(collection_data.get('test_cases', []))
    print(f"[INFO] 删除后集合详情测试用例数量: {final_count}")

    # 验证：只返回未删除的测试用例（应该只有1个）
    assert final_count == 1, f"删除后期望1个未删除的测试用例，实际: {final_count}"

    # 验证返回的测试用例ID是正确的（未被删除的）
    returned_test_case_ids = [tc['id'] for tc in collection_data.get('test_cases', [])]
    assert test_case_ids[1] in returned_test_case_ids, "未删除的测试用例应该被返回"
    assert test_case_ids[0] not in returned_test_case_ids, "已删除的测试用例不应被返回"
    assert test_case_ids[2] not in returned_test_case_ids, "已删除的测试用例不应被返回"

    print("[PASS] 集合详情接口正确过滤已删除的测试用例")

    # 清理测试数据
    requests.delete(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    requests.delete(f"{BASE_URL}/projects/{project_id}/", headers=HEADERS)


def test_batch_remove_test_cases_from_collection():
    """
    问题3：测试批量移除测试用例接口

    验证：从集合中批量移除测试用例后，
    这些测试用例的collection字段应该被设置为None
    """
    print("\n=== 测试2: 批量移除测试用例接口 ===")

    # 准备测试数据
    project_id = get_or_create_project()
    collection_id = get_or_create_collection(project_id)

    # 创建3个测试用例
    test_case_ids = []
    for i in range(1, 4):
        data = {
            "name": f"待移除用例-{i}",
            "project": project_id,
            "collection": collection_id,
            "method": "GET",
            "url": f"/remove-test-{i}",
            "body": {},
            "headers": {},
            "params": {}
        }
        resp = requests.post(f"{BASE_URL}/test-cases/", json=data, headers=HEADERS)
        if resp.status_code == 201:
            test_case_ids.append(resp.json()['id'])
            print(f"[INFO] 创建测试用例-{i}，ID: {resp.json()['id']}")

    # 获取集合详情，验证有3个测试用例
    resp = requests.get(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    assert resp.status_code == 200
    initial_count = len(resp.json().get('test_cases', []))
    print(f"[INFO] 移除前集合测试用例数量: {initial_count}")
    assert initial_count == 3

    # 批量移除第1个和第2个测试用例
    remove_data = {
        "test_case_ids": [test_case_ids[0], test_case_ids[1]]
    }
    resp = requests.post(
        f"{BASE_URL}/collections/{collection_id}/batch_remove_test_cases/",
        json=remove_data,
        headers=HEADERS
    )
    assert resp.status_code == 200, f"批量移除失败: {resp.status_code}"
    result = resp.json()
    print(f"[INFO] 移除结果: {result}")
    assert result['updated_count'] == 2, f"期望移除2个，实际: {result['updated_count']}"

    # 获取集合详情，验证只剩下1个测试用例
    resp = requests.get(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    assert resp.status_code == 200
    collection_data = resp.json()
    final_count = len(collection_data.get('test_cases', []))
    print(f"[INFO] 移除后集合测试用例数量: {final_count}")
    assert final_count == 1, f"移除后期望1个测试用例，实际: {final_count}"

    # 验证返回的是第3个测试用例（未被移除的）
    returned_test_cases = collection_data.get('test_cases', [])
    assert len(returned_test_cases) == 1
    assert returned_test_cases[0]['id'] == test_case_ids[2], "未被移除的测试用例应该仍在集合中"

    # 验证被移除的测试用例collection字段为None
    for test_case_id in [test_case_ids[0], test_case_ids[1]]:
        resp = requests.get(f"{BASE_URL}/test-cases/{test_case_id}/", headers=HEADERS)
        assert resp.status_code == 200
        test_case_data = resp.json()
        assert test_case_data.get('collection') is None, \
            f"被移除的测试用例collection应该为None，实际: {test_case_data.get('collection')}"
        print(f"[INFO] 验证测试用例 {test_case_id} 的collection为None")

    print("[PASS] 批量移除测试用例接口正确工作")

    # 清理测试数据
    requests.delete(f"{BASE_URL}/test-cases/{test_case_ids[2]}/", headers=HEADERS)
    requests.delete(f"{BASE_URL}/collections/{collection_id}/", headers=HEADERS)
    requests.delete(f"{BASE_URL}/projects/{project_id}/", headers=HEADERS)


if __name__ == "__main__":
    try:
        test_collection_detail_filters_deleted_test_cases()
        test_batch_remove_test_cases_from_collection()
        print("\n=== 所有测试通过 ===")
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
