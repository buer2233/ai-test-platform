"""
测试级联删除和回收站功能
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from api_automation.models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment, ApiDataDriver
)
from api_automation.services.cascade_delete_service import cascade_delete_service
from api_automation.services.recycle_bin_service import recycle_bin_service


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_cascade_delete():
    """测试级联删除功能"""
    print_section("测试级联删除功能")

    # 创建测试用户
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )

    # 创建测试项目
    project = ApiProject.objects.create(
        name='测试项目_级联删除',
        description='用于测试级联删除',
        owner=user
    )
    print(f"[OK] 创建项目: {project.name} (id={project.id})")

    # 创建测试集合
    collection1 = ApiCollection.objects.create(
        name='测试集合1',
        project=project
    )
    collection2 = ApiCollection.objects.create(
        name='测试集合2',
        project=project
    )
    print(f"[OK] 创建集合: {collection1.name}, {collection2.name}")

    # 创建测试用例
    test_case1 = ApiTestCase.objects.create(
        name='测试用例1',
        project=project,
        collection=collection1,
        method='GET',
        url='/api/test1'
    )
    test_case2 = ApiTestCase.objects.create(
        name='测试用例2',
        project=project,
        collection=collection1,
        method='POST',
        url='/api/test2'
    )
    print(f"[OK] 创建测试用例: {test_case1.name}, {test_case2.name}")

    # 创建测试环境
    environment = ApiTestEnvironment.objects.create(
        name='测试环境',
        project=project,
        base_url='http://test.example.com'
    )
    print(f"[OK] 创建环境: {environment.name}")

    # 预览删除
    print_section("预览删除影响")
    preview = cascade_delete_service.preview_delete(project)
    print(f"目标: {preview['target']['display_type']} - {preview['target']['name']}")
    print(f"级联删除统计:")
    for key, count in preview['cascade_count'].items():
        print(f"  - {key}: {count}个")

    # 执行级联删除
    print_section("执行级联删除")
    result = cascade_delete_service.cascade_delete(project)
    print(f"[OK] 删除成功: {result['deleted']['name']}")
    print(f"级联删除统计:")
    for key, count in result['cascade_deleted'].items():
        print(f"  - {key}: {count}个")

    # 验证删除状态
    print_section("验证删除状态")
    project.refresh_from_db()
    collection1.refresh_from_db()
    collection2.refresh_from_db()
    test_case1.refresh_from_db()
    test_case2.refresh_from_db()
    environment.refresh_from_db()

    assert project.is_deleted == True, "项目未标记为删除"
    assert collection1.is_deleted == True, "集合1未标记为删除"
    assert collection2.is_deleted == True, "集合2未标记为删除"
    assert test_case1.is_deleted == True, "测试用例1未标记为删除"
    assert test_case2.is_deleted == True, "测试用例2未标记为删除"
    assert environment.is_deleted == True, "环境未标记为删除"

    print("[OK] 所有数据已标记为删除 (is_deleted=True)")

    return project.id, collection1.id, test_case1.id


def test_recycle_bin():
    """测试回收站功能"""
    print_section("测试回收站功能")

    # 获取回收站统计
    print_section("回收站统计")
    stats = recycle_bin_service.get_recycle_bin_stats()
    print(f"回收站总数据量: {stats['total_count']}")
    for key, value in stats['stats'].items():
        print(f"  - {value['display_name']}: {value['count']}个")

    # 获取回收站列表
    print_section("回收站项目列表")
    items = recycle_bin_service.get_deleted_items(item_type='apiproject')
    print(f"已删除项目数: {items['count']}")
    for item in items['results']:
        print(f"  - {item['name']} (id={item['id']})")

    # 恢复数据
    print_section("恢复数据")
    # 获取第一个已删除的项目
    deleted_project = ApiProject.objects.filter(is_deleted=True).first()
    if deleted_project:
        result = recycle_bin_service.restore_item('apiproject', deleted_project.id)
        print(f"[OK] 恢复项目: {result['restored']['name']}")
        print(f"级联恢复统计:")
        for key, count in result['cascade_restored'].items():
            print(f"  - {key}: {count}个")

        # 验证恢复状态
        deleted_project.refresh_from_db()
        assert deleted_project.is_deleted == False, "项目未恢复"
        print("[OK] 项目已恢复 (is_deleted=False)")


def test_permanent_delete():
    """测试物理删除"""
    print_section("测试物理删除")

    # 创建一个测试项目
    user = User.objects.filter(username='test_user').first()
    if not user:
        user = User.objects.create_user(username='test_user', email='test@example.com')

    project = ApiProject.objects.create(
        name='测试项目_物理删除',
        description='用于测试物理删除',
        owner=user
    )
    print(f"[OK] 创建项目: {project.name} (id={project.id})")

    # 软删除
    project.is_deleted = True
    project.save()
    print(f"[OK] 项目已软删除")

    # 物理删除
    result = recycle_bin_service.permanent_delete_item('apiproject', project.id)
    print(f"[OK] 物理删除成功: {result['permanent_deleted']['name']}")

    # 验证物理删除
    assert not ApiProject.objects.filter(id=project.id).exists(), "项目仍存在于数据库"
    print("[OK] 项目已从数据库彻底删除")


def cleanup_test_data():
    """清理测试数据"""
    print_section("清理测试数据")
    User.objects.filter(username='test_user').delete()
    print("[OK] 清理测试用户完成")


if __name__ == '__main__':
    try:
        # 运行测试
        test_cascade_delete()
        test_recycle_bin()
        test_permanent_delete()

        print_section("所有测试通过 [OK]")

    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理测试数据
        cleanup_test_data()
