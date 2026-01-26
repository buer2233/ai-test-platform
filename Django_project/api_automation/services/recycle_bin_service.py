"""
回收站管理服务
管理逻辑删除的数据，提供查看、恢复、彻底删除等功能
"""
from django.db.models import Q
from django.core.paginator import Paginator
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RecycleBinService:
    """回收站管理服务"""

    # 支持回收站的模型配置
    RECYCLE_BIN_MODELS = {
        'apiproject': {
            'model': 'ApiProject',
            'display_name': '项目',
            'fields': ['id', 'name', 'description', 'owner', 'created_time', 'updated_time']
        },
        'apicollection': {
            'model': 'ApiCollection',
            'display_name': '集合',
            'fields': ['id', 'name', 'description', 'project', 'created_time', 'updated_time']
        },
        'apitestcase': {
            'model': 'ApiTestCase',
            'display_name': '测试用例',
            'fields': ['id', 'name', 'description', 'project', 'collection', 'method', 'url', 'created_time', 'updated_time']
        },
        'apitestenvironment': {
            'model': 'ApiTestEnvironment',
            'display_name': '测试环境',
            'fields': ['id', 'name', 'description', 'project', 'base_url', 'is_default', 'created_time', 'updated_time']
        },
        'apidatadriver': {
            'model': 'ApiDataDriver',
            'display_name': '数据驱动',
            'fields': ['id', 'name', 'description', 'project', 'test_case', 'data_type', 'created_time', 'updated_time']
        },
        'apitestexecution': {
            'model': 'ApiTestExecution',
            'display_name': '测试执行',
            'fields': ['id', 'name', 'description', 'project', 'environment', 'status', 'created_time', 'updated_time']
        },
    }

    def __init__(self):
        """初始化服务，导入所有模型和级联删除服务"""
        from ..models import (
            ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
            ApiTestExecution, ApiDataDriver
        )
        from .cascade_delete_service import cascade_delete_service

        self.model_classes = {
            'ApiProject': ApiProject,
            'ApiCollection': ApiCollection,
            'ApiTestCase': ApiTestCase,
            'ApiTestEnvironment': ApiTestEnvironment,
            'ApiTestExecution': ApiTestExecution,
            'ApiDataDriver': ApiDataDriver,
        }
        self.cascade_service = cascade_delete_service

    def get_deleted_items(
        self,
        item_type: Optional[str] = None,
        user=None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取回收站中的已删除数据

        Args:
            item_type: 数据类型筛选
            user: 当前用户（用于权限过滤）
            search: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            分页的已删除数据列表
        """
        results = []
        total_count = 0

        # 确定要查询的模型
        if item_type:
            models_to_query = [item_type] if item_type in self.RECYCLE_BIN_MODELS else []
        else:
            models_to_query = list(self.RECYCLE_BIN_MODELS.keys())

        for type_key in models_to_query:
            config = self.RECYCLE_BIN_MODELS[type_key]
            model_name = config['model']
            model_class = self.model_classes.get(model_name)

            if not model_class or not hasattr(model_class, 'is_deleted'):
                continue

            # 构建查询
            queryset = model_class.objects.filter(is_deleted=True)

            # 权限过滤
            if user and not user.is_superuser:
                # 只返回用户自己的数据
                if hasattr(model_class, 'owner'):
                    queryset = queryset.filter(owner=user)
                elif hasattr(model_class, 'project'):
                    queryset = queryset.filter(project__owner=user)
                elif hasattr(model_class, 'created_by'):
                    queryset = queryset.filter(created_by=user)

            # 搜索过滤
            if search:
                queryset = queryset.filter(name__icontains=search)

            # 统计
            total_count += queryset.count()

            # 分页
            if item_type:  # 单一类型查询时使用分页
                paginator = Paginator(queryset, page_size)
                page_obj = paginator.get_page(page)
                items = page_obj.object_list
            else:  # 多类型查询时不分页
                items = list(queryset[:20])  # 每种类型最多返回20条

            # 序列化数据
            for item in items:
                results.append(self._serialize_deleted_item(item, type_key))

        # 如果是单一类型查询，使用标准分页
        if item_type:
            config = self.RECYCLE_BIN_MODELS.get(item_type, {})
            model_name = config.get('model')
            model_class = self.model_classes.get(model_name) if model_name else None

            if model_class:
                queryset = model_class.objects.filter(is_deleted=True)

                if user and not user.is_superuser:
                    if hasattr(model_class, 'owner'):
                        queryset = queryset.filter(owner=user)
                    elif hasattr(model_class, 'project'):
                        queryset = queryset.filter(project__owner=user)
                    elif hasattr(model_class, 'created_by'):
                        queryset = queryset.filter(created_by=user)

                if search:
                    queryset = queryset.filter(name__icontains=search)

                total_count = queryset.count()
                paginator = Paginator(queryset, page_size)
                page_obj = paginator.get_page(page)

                results = [
                    self._serialize_deleted_item(item, item_type)
                    for item in page_obj.object_list
                ]

                return {
                    'results': results,
                    'count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': paginator.num_pages
                }

        return {
            'results': results,
            'count': total_count
        }

    def restore_item(self, item_type: str, item_id: int, user=None) -> Dict[str, Any]:
        """
        恢复回收站中的数据

        Args:
            item_type: 数据类型
            item_id: 数据ID
            user: 当前用户（用于权限验证）

        Returns:
            恢复结果
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type.lower())
        if not config:
            raise ValueError(f"不支持的数据类型: {item_type}")

        model_name = config['model']
        model_class = self.model_classes.get(model_name)

        if not model_class:
            raise ValueError(f"模型不存在: {model_name}")

        # 获取对象并验证权限
        try:
            obj = model_class.objects.get(id=item_id, is_deleted=True)
        except model_class.DoesNotExist:
            raise ValueError(f"未找到已删除的数据: {item_type}(id={item_id})")

        # 权限验证
        if user and not user.is_superuser:
            if hasattr(obj, 'owner') and obj.owner != user:
                raise PermissionError(f"无权恢复此数据")
            if hasattr(obj, 'project') and obj.project.owner != user:
                raise PermissionError(f"无权恢复此数据")
            if hasattr(obj, 'created_by') and obj.created_by != user:
                raise PermissionError(f"无权恢复此数据")

        # 调用级联删除服务进行恢复
        result = self.cascade_service.restore(model_name, item_id)

        logger.info(f"用户 {user} 恢复数据: {item_type}(id={item_id})")

        return result

    def permanent_delete_item(self, item_type: str, item_id: int, user=None) -> Dict[str, Any]:
        """
        彻底删除回收站中的数据

        Args:
            item_type: 数据类型
            item_id: 数据ID
            user: 当前用户（用于权限验证）

        Returns:
            删除结果
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type.lower())
        if not config:
            raise ValueError(f"不支持的数据类型: {item_type}")

        model_name = config['model']
        model_class = self.model_classes.get(model_name)

        if not model_class:
            raise ValueError(f"模型不存在: {model_name}")

        # 获取对象并验证权限
        try:
            obj = model_class.objects.get(id=item_id, is_deleted=True)
        except model_class.DoesNotExist:
            raise ValueError(f"未找到已删除的数据: {item_type}(id={item_id})")

        # 权限验证
        if user and not user.is_superuser:
            if hasattr(obj, 'owner') and obj.owner != user:
                raise PermissionError(f"无权删除此数据")
            if hasattr(obj, 'project') and obj.project.owner != user:
                raise PermissionError(f"无权删除此数据")
            if hasattr(obj, 'created_by') and obj.created_by != user:
                raise PermissionError(f"无权删除此数据")

        # 调用级联删除服务进行物理删除
        result = self.cascade_service.permanent_delete(model_name, item_id)

        logger.info(f"用户 {user} 彻底删除数据: {item_type}(id={item_id})")

        return result

    def batch_restore(self, item_type: str, item_ids: List[int], user=None) -> Dict[str, Any]:
        """
        批量恢复数据

        Args:
            item_type: 数据类型
            item_ids: 数据ID列表
            user: 当前用户

        Returns:
            批量恢复结果
        """
        restored = []
        failed = []

        for item_id in item_ids:
            try:
                result = self.restore_item(item_type, item_id, user)
                restored.append(result)
            except Exception as e:
                logger.error(f"批量恢复失败: {item_type}(id={item_id}), 错误: {str(e)}")
                failed.append({
                    'id': item_id,
                    'error': str(e)
                })

        return {
            'restored': restored,
            'restored_count': len(restored),
            'failed': failed,
            'failed_count': len(failed)
        }

    def batch_permanent_delete(self, item_type: str, item_ids: List[int], user=None) -> Dict[str, Any]:
        """
        批量彻底删除数据

        Args:
            item_type: 数据类型
            item_ids: 数据ID列表
            user: 当前用户

        Returns:
            批量删除结果
        """
        deleted = []
        failed = []

        for item_id in item_ids:
            try:
                result = self.permanent_delete_item(item_type, item_id, user)
                deleted.append(result)
            except Exception as e:
                logger.error(f"批量删除失败: {item_type}(id={item_id}), 错误: {str(e)}")
                failed.append({
                    'id': item_id,
                    'error': str(e)
                })

        return {
            'deleted': deleted,
            'deleted_count': len(deleted),
            'failed': failed,
            'failed_count': len(failed)
        }

    def get_recycle_bin_stats(self, user=None) -> Dict[str, Any]:
        """
        获取回收站统计信息

        Args:
            user: 当前用户

        Returns:
            统计信息
        """
        stats = {}

        for type_key, config in self.RECYCLE_BIN_MODELS.items():
            model_name = config['model']
            model_class = self.model_classes.get(model_name)

            if not model_class or not hasattr(model_class, 'is_deleted'):
                continue

            queryset = model_class.objects.filter(is_deleted=True)

            # 权限过滤
            if user and not user.is_superuser:
                if hasattr(model_class, 'owner'):
                    queryset = queryset.filter(owner=user)
                elif hasattr(model_class, 'project'):
                    queryset = queryset.filter(project__owner=user)
                elif hasattr(model_class, 'created_by'):
                    queryset = queryset.filter(created_by=user)

            stats[type_key] = {
                'display_name': config['display_name'],
                'count': queryset.count()
            }

        total_count = sum(s['count'] for s in stats.values())

        return {
            'stats': stats,
            'total_count': total_count
        }

    def _serialize_deleted_item(self, item, item_type: str) -> Dict[str, Any]:
        """
        序列化已删除的数据

        Args:
            item: 模型实例
            item_type: 数据类型

        Returns:
            序列化后的数据
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type, {})
        fields = config.get('fields', [])

        data = {
            'type': item_type,
            'display_type': config.get('display_name', item_type),
            'id': item.id,
            'name': getattr(item, 'name', str(item)),
        }

        # 添加配置的字段
        for field in fields:
            if field in ['id', 'name']:
                continue

            value = getattr(item, field, None)
            if value is not None:
                # 处理外键字段
                if hasattr(value, 'id'):
                    data[field] = {
                        'id': value.id,
                        'name': getattr(value, 'name', str(value))
                    }
                else:
                    data[field] = value

        return data


# 全局服务实例
recycle_bin_service = RecycleBinService()
