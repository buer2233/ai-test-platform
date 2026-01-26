"""
级联逻辑删除服务
处理项目、集合、测试用例等数据的级联软删除和恢复
"""
from django.db import transaction
from django.utils import timezone
from django.db import DatabaseError
from typing import Dict, List, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)


def retry_on_db_lock(max_retries=3, delay=0.1):
    """
    重试装饰器，用于处理SQLite数据库锁定错误

    Args:
        max_retries: 最大重试次数
        delay: 重试之间的延迟（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    # 检查是否是数据库锁定错误
                    if 'database is locked' in str(e) or 'OperationalError' in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"数据库锁定，第 {attempt + 1} 次重试...")
                            time.sleep(delay * (2 ** attempt))  # 指数退避
                            continue
                    raise
            raise last_exception
        return wrapper
    return decorator


class CascadeDeleteService:
    """级联逻辑删除服务"""

    # 级联关系配置：父模型 -> (子模型, 关联字段)
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

    # 模型名称映射（用于显示）
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
        """初始化服务，导入所有模型"""
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

    def preview_delete(self, obj) -> Dict[str, Any]:
        """
        预览删除操作的影响

        Args:
            obj: 要删除的模型实例

        Returns:
            包含删除预览信息的字典
        """
        model_name = obj.__class__.__name__
        cascade_info = self._get_cascade_info(obj, model_name)

        return {
            'target': {
                'id': obj.id,
                'name': getattr(obj, 'name', str(obj)),
                'type': model_name.lower(),
                'display_type': self.MODEL_DISPLAY_NAMES.get(model_name, model_name)
            },
            'cascade_count': cascade_info['count'],
            'cascade_details': cascade_info['details']
        }

    @retry_on_db_lock(max_retries=5, delay=0.1)
    def cascade_delete(self, obj) -> Dict[str, Any]:
        """
        执行级联逻辑删除

        Args:
            obj: 要删除的模型实例

        Returns:
            删除结果统计
        """
        model_name = obj.__class__.__name__
        preview_info = self.preview_delete(obj)

        try:
            with transaction.atomic():
                # 递归删除所有子数据
                deleted_count = self._cascade_delete_recursive(obj, model_name)

                # 删除对象本身
                if hasattr(obj, 'is_deleted'):
                    obj.is_deleted = True
                    obj.save(update_fields=['is_deleted'])

                logger.info(f"级联删除成功: {model_name}(id={obj.id}), "
                          f"关联删除统计: {deleted_count}")

                return {
                    'deleted': {
                        'id': obj.id,
                        'name': getattr(obj, 'name', str(obj)),
                        'type': model_name.lower()
                    },
                    'cascade_deleted': deleted_count
                }

        except Exception as e:
            logger.error(f"级联删除失败: {model_name}(id={obj.id}), 错误: {str(e)}")
            raise

    def restore(self, model_name: str, obj_id: int) -> Dict[str, Any]:
        """
        恢复已删除的数据及其子数据

        Args:
            model_name: 模型名称
            obj_id: 对象ID

        Returns:
            恢复结果统计
        """
        model_class = self.model_classes.get(model_name)
        if not model_class:
            raise ValueError(f"不支持的模型类型: {model_name}")

        try:
            with transaction.atomic():
                # 获取已删除的对象
                obj = model_class.objects.get(id=obj_id, is_deleted=True)

                # 恢复对象本身
                obj.is_deleted = False
                obj.save(update_fields=['is_deleted'])

                # 递归恢复子数据
                restored_count = self._restore_recursive(obj, model_name)

                logger.info(f"恢复数据成功: {model_name}(id={obj_id}), "
                          f"关联恢复统计: {restored_count}")

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
            logger.error(f"恢复数据失败: {model_name}(id={obj_id}), 错误: {str(e)}")
            raise

    def _get_cascade_info(self, obj, model_name: str, visited: Optional[set] = None) -> Dict[str, Any]:
        """
        获取级联删除的信息

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问的对象集合（避免循环）

        Returns:
            级联删除信息
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {'count': {}, 'details': []}
        visited.add(key)

        cascade_count = {}
        cascade_details = []

        # 获取该模型的级联配置
        cascade_configs = self.CASCADE_MAPPING.get(model_name, [])

        for child_model_name, relation_field in cascade_configs:
            child_model = self.model_classes.get(child_model_name)
            if not child_model or not hasattr(child_model, 'is_deleted'):
                continue

            # 构建过滤条件：关联字段匹配 + 未删除
            filter_kwargs = {
                relation_field: obj,
                'is_deleted': False
            }

            # 对于ApiTestCase，collection可能为空
            if child_model_name == 'ApiTestCase' and relation_field == 'collection':
                children = child_model.objects.filter(
                    **{relation_field: obj}
                ).filter(is_deleted=False)
            else:
                children = child_model.objects.filter(**filter_kwargs)

            count = children.count()

            if count > 0:
                display_name = self.MODEL_DISPLAY_NAMES.get(child_model_name, child_model_name)
                cascade_count[child_model_name.lower()] = count

                # 收集名称（前10个）
                names = list(children.values_list('name', flat=True)[:10])
                if count > 10:
                    names.append(f'...等{count}个')

                cascade_details.append({
                    'type': child_model_name.lower(),
                    'display_type': display_name,
                    'count': count,
                    'names': names
                })

                # 递归获取子数据的级联信息
                for child in children:
                    child_info = self._get_cascade_info(child, child_model_name, visited)
                    for k, v in child_info['count'].items():
                        cascade_count[k] = cascade_count.get(k, 0) + v
                    cascade_details.extend(child_info['details'])

        return {'count': cascade_count, 'details': cascade_details}

    def _cascade_delete_recursive(self, obj, model_name: str, visited: Optional[set] = None) -> Dict[str, int]:
        """
        递归执行级联删除

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问的对象集合

        Returns:
            各模型的删除数量统计
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {}
        visited.add(key)

        deleted_count = {}
        cascade_configs = self.CASCADE_MAPPING.get(model_name, [])

        for child_model_name, relation_field in cascade_configs:
            child_model = self.model_classes.get(child_model_name)
            if not child_model or not hasattr(child_model, 'is_deleted'):
                continue

            # 获取子数据
            filter_kwargs = {
                relation_field: obj,
                'is_deleted': False
            }

            if child_model_name == 'ApiTestCase' and relation_field == 'collection':
                children = child_model.objects.filter(
                    **{relation_field: obj}
                ).filter(is_deleted=False)
            else:
                children = child_model.objects.filter(**filter_kwargs)

            # 递归删除每个子数据
            for child in children:
                child_deleted = self._cascade_delete_recursive(child, child_model_name, visited)
                for k, v in child_deleted.items():
                    deleted_count[k] = deleted_count.get(k, 0) + v

                # 标记为删除（带重试）
                self._save_with_retry(child)

            deleted_count[child_model_name.lower()] = deleted_count.get(child_model_name.lower(), 0) + children.count()

        return deleted_count

    @retry_on_db_lock(max_retries=3, delay=0.05)
    def _save_with_retry(self, obj):
        """保存对象，带有重试逻辑处理数据库锁定"""
        obj.is_deleted = True
        obj.save(update_fields=['is_deleted'])

    def _restore_recursive(self, obj, model_name: str, visited: Optional[set] = None) -> Dict[str, int]:
        """
        递归恢复子数据

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问的对象集合

        Returns:
            各模型的恢复数量统计
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return {}
        visited.add(key)

        restored_count = {}
        cascade_configs = self.CASCADE_MAPPING.get(model_name, [])

        for child_model_name, relation_field in cascade_configs:
            child_model = self.model_classes.get(child_model_name)
            if not child_model or not hasattr(child_model, 'is_deleted'):
                continue

            # 获取已删除的子数据
            filter_kwargs = {
                relation_field: obj,
                'is_deleted': True
            }

            if child_model_name == 'ApiTestCase' and relation_field == 'collection':
                children = child_model.objects.filter(
                    **{relation_field: obj}
                ).filter(is_deleted=True)
            else:
                children = child_model.objects.filter(**filter_kwargs)

            # 递归恢复每个子数据
            for child in children:
                child_restored = self._restore_recursive(child, child_model_name, visited)
                for k, v in child_restored.items():
                    restored_count[k] = restored_count.get(k, 0) + v

                # 恢复（带重试）
                self._restore_with_retry(child)

            restored_count[child_model_name.lower()] = restored_count.get(child_model_name.lower(), 0) + children.count()

        return restored_count

    @retry_on_db_lock(max_retries=3, delay=0.05)
    def _restore_with_retry(self, obj):
        """恢复对象，带有重试逻辑处理数据库锁定"""
        obj.is_deleted = False
        obj.save(update_fields=['is_deleted'])

    def permanent_delete(self, model_name: str, obj_id: int) -> Dict[str, Any]:
        """
        物理删除数据（用于回收站彻底删除）

        Args:
            model_name: 模型名称
            obj_id: 对象ID

        Returns:
            删除结果
        """
        model_class = self.model_classes.get(model_name)
        if not model_class:
            raise ValueError(f"不支持的模型类型: {model_name}")

        try:
            with transaction.atomic():
                # 获取已删除的对象
                obj = model_class.objects.get(id=obj_id, is_deleted=True)

                # 先获取级联信息用于日志
                preview_info = self.preview_delete(obj)

                # 递归物理删除所有子数据
                self._permanent_delete_recursive(obj, model_name)

                # 物理删除对象本身
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
            logger.error(f"物理删除失败: {model_name}(id={obj_id}), 错误: {str(e)}")
            raise

    def _permanent_delete_recursive(self, obj, model_name: str, visited: Optional[set] = None):
        """
        递归物理删除子数据

        Args:
            obj: 模型实例
            model_name: 模型名称
            visited: 已访问的对象集合
        """
        if visited is None:
            visited = set()

        key = f"{model_name}_{obj.id}"
        if key in visited:
            return
        visited.add(key)

        cascade_configs = self.CASCADE_MAPPING.get(model_name, [])

        for child_model_name, relation_field in cascade_configs:
            child_model = self.model_classes.get(child_model_name)
            if not child_model:
                continue

            # 获取已删除的子数据
            filter_kwargs = {
                relation_field: obj,
                'is_deleted': True
            }

            if child_model_name == 'ApiTestCase' and relation_field == 'collection':
                children = child_model.objects.filter(
                    **{relation_field: obj}
                ).filter(is_deleted=True)
            else:
                children = child_model.objects.filter(**filter_kwargs)

            # 递归物理删除每个子数据
            for child in children:
                self._permanent_delete_recursive(child, child_model_name, visited)

            # 批量物理删除
            children.delete()


# 全局服务实例
cascade_delete_service = CascadeDeleteService()
