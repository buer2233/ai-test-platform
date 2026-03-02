"""
级联逻辑删除服务

处理项目、集合、测试用例等数据的级联软删除（逻辑删除）和恢复。
当删除一个父级对象时（如项目），其所有子级对象（集合、用例、环境等）
也会被级联标记为 is_deleted=True。

主要功能：
- 预览删除影响：展示将被级联删除的所有子数据
- 级联软删除：递归标记父子数据的 is_deleted 字段
- 级联恢复：递归恢复已删除的父子数据
- 物理删除：从数据库中彻底删除数据（用于回收站清空）

包含SQLite数据库锁定的指数退避重试机制。
"""

import logging
import time
from typing import Any, Dict, List, Optional

from django.db import transaction

logger = logging.getLogger(__name__)


def retry_on_db_lock(max_retries=3, delay=0.1):
    """
    数据库锁定重试装饰器

    SQLite在并发写入时可能出现 "database is locked" 错误，
    此装饰器使用指数退避策略自动重试。

    Args:
        max_retries: 最大重试次数
        delay: 首次重试延迟（秒），后续以2的幂递增

    Returns:
        装饰后的函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    is_db_lock = (
                        'database is locked' in str(e)
                        or 'OperationalError' in str(e)
                    )
                    if is_db_lock and attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(
                            f"数据库锁定，第 {attempt + 1} 次重试，"
                            f"等待 {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        continue
                    raise
            raise last_exception
        return wrapper
    return decorator


class CascadeDeleteService:
    """
    级联逻辑删除服务

    通过配置化的级联关系映射表，实现递归的软删除、恢复和物理删除。
    使用 visited 集合防止循环引用导致的无限递归。
    """

    # 级联关系配置：父模型 -> [(子模型名, 关联字段名), ...]
    CASCADE_MAPPING = {
        'ApiProject': [
            ('ApiCollection', 'project'),
            ('ApiTestEnvironment', 'project'),
            ('ApiDataDriver', 'project'),
            ('ApiTestExecution', 'project'),
        ],
        'ApiCollection': [
            ('ApiTestCase', 'collection'),
        ],
        'ApiTestCase': [
            ('ApiTestCaseAssertion', 'test_case'),
            ('ApiTestCaseExtraction', 'test_case'),
            ('ApiDataDriver', 'test_case'),
        ],
        'ApiTestEnvironment': [
            ('ApiTestExecution', 'environment'),
        ],
        'ApiTestExecution': [
            ('ApiTestResult', 'execution'),
            ('ApiTestReport', 'execution'),
        ],
    }

    # 模型名称到中文显示名的映射
    MODEL_DISPLAY_NAMES = {
        'ApiProject': '项目',
        'ApiCollection': '集合',
        'ApiTestCase': '测试用例',
        'ApiTestEnvironment': '测试环境',
        'ApiDataDriver': '数据驱动',
        'ApiTestExecution': '测试执行',
        'ApiTestResult': '测试结果',
        'ApiTestReport': '测试报告',
        'ApiTestCaseAssertion': '断言配置',
        'ApiTestCaseExtraction': '提取配置',
    }

    def __init__(self):
        """初始化服务，加载所有需要的模型类"""
        from ..models import (
            ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
            ApiTestExecution, ApiTestResult, ApiTestReport, ApiDataDriver,
            ApiTestCaseAssertion, ApiTestCaseExtraction
        )
        self.model_classes = {
            'ApiProject': ApiProject,
            'ApiCollection': ApiCollection,
            'ApiTestCase': ApiTestCase,
            'ApiTestEnvironment': ApiTestEnvironment,
            'ApiTestExecution': ApiTestExecution,
            'ApiTestResult': ApiTestResult,
            'ApiTestReport': ApiTestReport,
            'ApiDataDriver': ApiDataDriver,
            'ApiTestCaseAssertion': ApiTestCaseAssertion,
            'ApiTestCaseExtraction': ApiTestCaseExtraction,
        }

    def _get_children(
        self,
        obj,
        child_model_name: str,
        relation_field: str,
        is_deleted: bool
    ):
        """
        获取指定父对象的子数据查询集

        ApiTestCase的collection字段可能为空（未分配到集合的用例），
        需要特殊处理查询方式。

        Args:
            obj: 父对象实例
            child_model_name: 子模型名称
            relation_field: 关联字段名
            is_deleted: 过滤的is_deleted值

        Returns:
            子数据QuerySet，如果模型不存在或无is_deleted字段则返回None
        """
        child_model = self.model_classes.get(child_model_name)
        if not child_model or not hasattr(child_model, 'is_deleted'):
            return None

        # ApiTestCase的collection字段特殊处理
        if child_model_name == 'ApiTestCase' and relation_field == 'collection':
            return child_model.objects.filter(
                **{relation_field: obj}
            ).filter(is_deleted=is_deleted)

        return child_model.objects.filter(
            **{relation_field: obj, 'is_deleted': is_deleted}
        )

    def preview_delete(self, obj) -> Dict[str, Any]:
        """
        预览删除操作的影响范围

        递归统计将被级联删除的所有子数据数量和名称。

        Args:
            obj: 要删除的模型实例

        Returns:
            包含目标对象信息和级联影响详情的字典
        """
        model_name = obj.__class__.__name__
        cascade_info = self._get_cascade_info(obj, model_name)

        return {
            'target': {
                'id': obj.id,
                'name': getattr(obj, 'name', str(obj)),
                'type': model_name.lower(),
                'display_type': self.MODEL_DISPLAY_NAMES.get(
                    model_name, model_name
                )
            },
            'cascade_count': cascade_info['count'],
            'cascade_details': cascade_info['details']
        }

    @retry_on_db_lock(max_retries=5, delay=0.1)
    def cascade_delete(self, obj) -> Dict[str, Any]:
        """
        执行级联逻辑删除

        在数据库事务中递归标记父对象及其所有子对象的 is_deleted=True。

        Args:
            obj: 要删除的模型实例

        Returns:
            删除结果统计（各子类型的删除数量）
        """
        model_name = obj.__class__.__name__

        try:
            with transaction.atomic():
                # 先递归删除所有子数据
                deleted_count = self._cascade_delete_recursive(obj, model_name)

                # 最后标记父对象自身
                if hasattr(obj, 'is_deleted'):
                    obj.is_deleted = True
                    obj.save(update_fields=['is_deleted'])

                logger.info(
                    f"级联删除成功: {model_name}(id={obj.id}), "
                    f"关联删除统计: {deleted_count}"
                )

                return {
                    'deleted': {
                        'id': obj.id,
                        'name': getattr(obj, 'name', str(obj)),
                        'type': model_name.lower()
                    },
                    'cascade_deleted': deleted_count
                }

        except Exception as e:
            logger.error(
                f"级联删除失败: {model_name}(id={obj.id}), 错误: {str(e)}"
            )
            raise

    def restore(self, model_name: str, obj_id: int) -> Dict[str, Any]:
        """
        恢复已删除的数据及其所有子数据

        在数据库事务中递归恢复 is_deleted=True 的父对象及其子对象。

        Args:
            model_name: 模型名称（如 'ApiProject'）
            obj_id: 对象ID

        Returns:
            恢复结果统计

        Raises:
            ValueError: 模型不支持或对象不存在
        """
        model_class = self.model_classes.get(model_name)
        if not model_class:
            raise ValueError(f"不支持的模型类型: {model_name}")

        try:
            with transaction.atomic():
                obj = model_class.objects.get(id=obj_id, is_deleted=True)

                # 先恢复父对象自身
                obj.is_deleted = False
                obj.save(update_fields=['is_deleted'])

                # 再递归恢复所有子数据
                restored_count = self._restore_recursive(obj, model_name)

                logger.info(
                    f"恢复数据成功: {model_name}(id={obj_id}), "
                    f"关联恢复统计: {restored_count}"
                )

                return {
                    'restored': {
                        'id': obj.id,
                        'name': getattr(obj, 'name', str(obj)),
                        'type': model_name.lower()
                    },
                    'cascade_restored': restored_count
                }

        except model_class.DoesNotExist:
            raise ValueError(f"未找到已删除的{model_name}(id={obj_id})")
        except Exception as e:
            logger.error(
                f"恢复数据失败: {model_name}(id={obj_id}), 错误: {str(e)}"
            )
            raise

    def _get_cascade_info(
        self,
        obj,
        model_name: str,
        visited: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        递归收集级联删除的影响信息

        统计每种子类型的数量和名称（最多显示前10个）。

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问对象的唯一标识集合（防止循环）

        Returns:
            {'count': {类型: 数量}, 'details': [详情列表]}
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {'count': {}, 'details': []}
        visited.add(key)

        cascade_count = {}
        cascade_details = []

        for child_model_name, relation_field in self.CASCADE_MAPPING.get(model_name, []):
            children = self._get_children(
                obj, child_model_name, relation_field, is_deleted=False
            )
            if children is None:
                continue

            count = children.count()
            if count == 0:
                continue

            display_name = self.MODEL_DISPLAY_NAMES.get(
                child_model_name, child_model_name
            )
            cascade_count[child_model_name.lower()] = count

            # 收集名称（前10个，超出则显示省略提示）
            names = list(children.values_list('name', flat=True)[:10])
            if count > 10:
                names.append(f'...等{count}个')

            cascade_details.append({
                'type': child_model_name.lower(),
                'display_type': display_name,
                'count': count,
                'names': names
            })

            # 递归收集子数据的级联信息
            for child in children:
                child_info = self._get_cascade_info(
                    child, child_model_name, visited
                )
                for k, v in child_info['count'].items():
                    cascade_count[k] = cascade_count.get(k, 0) + v
                cascade_details.extend(child_info['details'])

        return {'count': cascade_count, 'details': cascade_details}

    def _cascade_delete_recursive(
        self,
        obj,
        model_name: str,
        visited: Optional[set] = None
    ) -> Dict[str, int]:
        """
        递归执行级联软删除

        先深度递归删除所有子孙数据，再标记当前层级的子数据。

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问对象集合

        Returns:
            各模型类型的删除数量统计
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {}
        visited.add(key)

        deleted_count = {}

        for child_model_name, relation_field in self.CASCADE_MAPPING.get(model_name, []):
            children = self._get_children(
                obj, child_model_name, relation_field, is_deleted=False
            )
            if children is None:
                continue

            # 先递归删除子数据的子数据
            for child in children:
                child_deleted = self._cascade_delete_recursive(
                    child, child_model_name, visited
                )
                for k, v in child_deleted.items():
                    deleted_count[k] = deleted_count.get(k, 0) + v

                # 标记当前子数据为删除（带数据库锁定重试）
                self._save_with_retry(child)

            type_key = child_model_name.lower()
            deleted_count[type_key] = (
                deleted_count.get(type_key, 0) + children.count()
            )

        return deleted_count

    @retry_on_db_lock(max_retries=3, delay=0.05)
    def _save_with_retry(self, obj):
        """标记对象为已删除，带数据库锁定重试"""
        obj.is_deleted = True
        obj.save(update_fields=['is_deleted'])

    def _restore_recursive(
        self,
        obj,
        model_name: str,
        visited: Optional[set] = None
    ) -> Dict[str, int]:
        """
        递归恢复已删除的子数据

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问对象集合

        Returns:
            各模型类型的恢复数量统计
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {}
        visited.add(key)

        restored_count = {}

        for child_model_name, relation_field in self.CASCADE_MAPPING.get(model_name, []):
            children = self._get_children(
                obj, child_model_name, relation_field, is_deleted=True
            )
            if children is None:
                continue

            for child in children:
                child_restored = self._restore_recursive(
                    child, child_model_name, visited
                )
                for k, v in child_restored.items():
                    restored_count[k] = restored_count.get(k, 0) + v

                self._restore_with_retry(child)

            type_key = child_model_name.lower()
            restored_count[type_key] = (
                restored_count.get(type_key, 0) + children.count()
            )

        return restored_count

    @retry_on_db_lock(max_retries=3, delay=0.05)
    def _restore_with_retry(self, obj):
        """恢复对象（取消删除标记），带数据库锁定重试"""
        obj.is_deleted = False
        obj.save(update_fields=['is_deleted'])

    def permanent_delete(self, model_name: str, obj_id: int) -> Dict[str, Any]:
        """
        物理删除数据及其所有子数据（不可恢复）

        仅对已软删除的数据执行物理删除，用于回收站的彻底清空功能。

        Args:
            model_name: 模型名称
            obj_id: 对象ID

        Returns:
            删除结果（包含级联删除统计）

        Raises:
            ValueError: 模型不支持或对象不存在
        """
        model_class = self.model_classes.get(model_name)
        if not model_class:
            raise ValueError(f"不支持的模型类型: {model_name}")

        try:
            with transaction.atomic():
                obj = model_class.objects.get(id=obj_id, is_deleted=True)

                # 收集级联信息用于返回结果
                preview_info = self.preview_delete(obj)

                # 递归物理删除所有子数据
                self._permanent_delete_recursive(obj, model_name)

                # 物理删除对象自身
                obj.delete()

                logger.info(f"物理删除成功: {model_name}(id={obj_id})")

                return {
                    'permanent_deleted': {
                        'id': obj_id,
                        'name': getattr(obj, 'name', str(obj)),
                        'type': model_name.lower()
                    },
                    'cascade_permanent_deleted': preview_info['cascade_count']
                }

        except model_class.DoesNotExist:
            raise ValueError(f"未找到已删除的{model_name}(id={obj_id})")
        except Exception as e:
            logger.error(
                f"物理删除失败: {model_name}(id={obj_id}), 错误: {str(e)}"
            )
            raise

    def _permanent_delete_recursive(
        self,
        obj,
        model_name: str,
        visited: Optional[set] = None
    ):
        """
        递归物理删除子数据

        先深度递归处理所有子孙数据，最后批量删除当前层级。

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问对象集合
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return
        visited.add(key)

        for child_model_name, relation_field in self.CASCADE_MAPPING.get(model_name, []):
            child_model = self.model_classes.get(child_model_name)
            if not child_model:
                continue

            # 获取已删除的子数据
            if child_model_name == 'ApiTestCase' and relation_field == 'collection':
                children = child_model.objects.filter(
                    **{relation_field: obj}
                ).filter(is_deleted=True)
            else:
                children = child_model.objects.filter(
                    **{relation_field: obj, 'is_deleted': True}
                )

            # 先递归处理更深层的子数据
            for child in children:
                self._permanent_delete_recursive(
                    child, child_model_name, visited
                )

            # 批量物理删除当前层级
            children.delete()


# 全局服务实例，供其他模块直接导入使用
cascade_delete_service = CascadeDeleteService()
