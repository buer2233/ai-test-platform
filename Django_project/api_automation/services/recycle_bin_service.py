"""
回收站管理服务

管理逻辑删除（软删除）的数据，提供以下功能：
- 查询回收站中的已删除数据（支持分页、搜索、类型过滤）
- 恢复已删除的数据（含权限验证）
- 彻底删除数据（物理删除，不可恢复）
- 批量恢复和批量删除
- 回收站统计信息
"""

import logging
from typing import Any, Dict, List, Optional

from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


class RecycleBinService:
    """
    回收站管理服务

    通过 is_deleted 字段实现软删除，回收站中保留所有已软删除的数据，
    用户可以恢复或彻底删除。所有操作都带有权限验证。
    """

    # 支持回收站功能的模型配置
    # key: 类型标识符, model: 模型类名, display_name: 前端显示名, fields: 序列化字段
    RECYCLE_BIN_MODELS = {
        'apiproject': {
            'model': 'ApiProject',
            'display_name': '项目',
            'fields': [
                'id', 'name', 'description', 'owner',
                'created_time', 'updated_time'
            ]
        },
        'apicollection': {
            'model': 'ApiCollection',
            'display_name': '集合',
            'fields': [
                'id', 'name', 'description', 'project',
                'created_time', 'updated_time'
            ]
        },
        'apitestcase': {
            'model': 'ApiTestCase',
            'display_name': '测试用例',
            'fields': [
                'id', 'name', 'description', 'project', 'collection',
                'method', 'url', 'created_time', 'updated_time'
            ]
        },
        'apitestenvironment': {
            'model': 'ApiTestEnvironment',
            'display_name': '测试环境',
            'fields': [
                'id', 'name', 'description', 'project', 'base_url',
                'is_default', 'created_time', 'updated_time'
            ]
        },
        'apidatadriver': {
            'model': 'ApiDataDriver',
            'display_name': '数据驱动',
            'fields': [
                'id', 'name', 'description', 'project', 'test_case',
                'data_type', 'created_time', 'updated_time'
            ]
        },
        'apitestexecution': {
            'model': 'ApiTestExecution',
            'display_name': '测试执行',
            'fields': [
                'id', 'name', 'description', 'project', 'environment',
                'status', 'created_time', 'updated_time'
            ]
        },
    }

    def __init__(self):
        """初始化服务，加载所有模型类和级联删除服务"""
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

    def _apply_permission_filter(self, queryset, model_class, user):
        """
        根据用户权限过滤查询集

        非超级管理员只能看到自己创建/拥有的数据。
        按 owner -> project.owner -> created_by 的优先级查找归属字段。

        Args:
            queryset: 原始查询集
            model_class: 模型类
            user: 当前用户

        Returns:
            过滤后的查询集
        """
        if not user or user.is_superuser:
            return queryset

        if hasattr(model_class, 'owner'):
            return queryset.filter(owner=user)
        elif hasattr(model_class, 'project'):
            return queryset.filter(project__owner=user)
        elif hasattr(model_class, 'created_by'):
            return queryset.filter(created_by=user)

        return queryset

    def _check_permission(self, obj, user):
        """
        验证用户是否有权操作指定对象

        Args:
            obj: 模型实例
            user: 当前用户

        Raises:
            PermissionError: 无权操作时抛出
        """
        if not user or user.is_superuser:
            return

        if hasattr(obj, 'owner') and obj.owner != user:
            raise PermissionError("无权操作此数据")
        if hasattr(obj, 'project') and obj.project.owner != user:
            raise PermissionError("无权操作此数据")
        if hasattr(obj, 'created_by') and obj.created_by != user:
            raise PermissionError("无权操作此数据")

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

        支持两种查询模式：
        - 指定 item_type: 查询单一类型，返回标准分页结果
        - 不指定 item_type: 查询所有类型，每种类型最多返回20条

        Args:
            item_type: 数据类型标识符（如 'apiproject', 'apitestcase'）
            user: 当前用户（用于权限过滤）
            search: 按名称搜索的关键词
            page: 页码
            page_size: 每页数量

        Returns:
            分页的已删除数据列表
        """
        # 单一类型查询，返回标准分页
        if item_type:
            return self._get_single_type_items(
                item_type, user, search, page, page_size
            )

        # 多类型查询，每种类型取前20条
        return self._get_all_type_items(user, search)

    def _get_single_type_items(
        self,
        item_type: str,
        user,
        search: Optional[str],
        page: int,
        page_size: int
    ) -> Dict[str, Any]:
        """
        查询单一类型的回收站数据（带分页）

        Args:
            item_type: 数据类型标识符
            user: 当前用户
            search: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            标准分页结果
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type, {})
        model_name = config.get('model')
        model_class = self.model_classes.get(model_name) if model_name else None

        if not model_class:
            return {'results': [], 'count': 0, 'page': page,
                    'page_size': page_size, 'total_pages': 0}

        queryset = model_class.objects.filter(is_deleted=True)
        queryset = self._apply_permission_filter(queryset, model_class, user)

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

    def _get_all_type_items(
        self,
        user,
        search: Optional[str]
    ) -> Dict[str, Any]:
        """
        查询所有类型的回收站数据（每种类型最多20条）

        Args:
            user: 当前用户
            search: 搜索关键词

        Returns:
            汇总结果
        """
        results = []
        total_count = 0

        for type_key, config in self.RECYCLE_BIN_MODELS.items():
            model_name = config['model']
            model_class = self.model_classes.get(model_name)

            if not model_class or not hasattr(model_class, 'is_deleted'):
                continue

            queryset = model_class.objects.filter(is_deleted=True)
            queryset = self._apply_permission_filter(queryset, model_class, user)

            if search:
                queryset = queryset.filter(name__icontains=search)

            total_count += queryset.count()

            # 每种类型最多返回20条
            for item in queryset[:20]:
                results.append(self._serialize_deleted_item(item, type_key))

        return {'results': results, 'count': total_count}

    def _get_model_and_object(
        self,
        item_type: str,
        item_id: int,
        user=None
    ) -> tuple:
        """
        获取模型类和已删除的对象实例，并验证权限

        这是 restore_item 和 permanent_delete_item 的共用逻辑。

        Args:
            item_type: 数据类型
            item_id: 数据ID
            user: 当前用户

        Returns:
            (model_name, obj) 元组

        Raises:
            ValueError: 类型不支持或对象不存在
            PermissionError: 无权操作
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type.lower())
        if not config:
            raise ValueError(f"不支持的数据类型: {item_type}")

        model_name = config['model']
        model_class = self.model_classes.get(model_name)

        if not model_class:
            raise ValueError(f"模型不存在: {model_name}")

        try:
            obj = model_class.objects.get(id=item_id, is_deleted=True)
        except model_class.DoesNotExist:
            raise ValueError(f"未找到已删除的数据: {item_type}(id={item_id})")

        self._check_permission(obj, user)
        return model_name, obj

    def restore_item(self, item_type: str, item_id: int, user=None) -> Dict[str, Any]:
        """
        恢复回收站中的单条数据

        通过级联删除服务恢复数据及其关联的子数据。

        Args:
            item_type: 数据类型
            item_id: 数据ID
            user: 当前用户

        Returns:
            恢复结果详情
        """
        model_name, obj = self._get_model_and_object(item_type, item_id, user)
        result = self.cascade_service.restore(model_name, item_id)

        logger.info(f"用户 {user} 恢复数据: {item_type}(id={item_id})")
        return result

    def permanent_delete_item(
        self,
        item_type: str,
        item_id: int,
        user=None
    ) -> Dict[str, Any]:
        """
        彻底删除回收站中的单条数据（物理删除，不可恢复）

        通过级联删除服务物理删除数据及其关联的子数据。

        Args:
            item_type: 数据类型
            item_id: 数据ID
            user: 当前用户

        Returns:
            删除结果详情
        """
        model_name, obj = self._get_model_and_object(item_type, item_id, user)
        result = self.cascade_service.permanent_delete(model_name, item_id)

        logger.info(f"用户 {user} 彻底删除数据: {item_type}(id={item_id})")
        return result

    def batch_restore(
        self,
        item_type: str,
        item_ids: List[int],
        user=None
    ) -> Dict[str, Any]:
        """
        批量恢复数据

        逐条调用 restore_item，收集成功和失败的结果。

        Args:
            item_type: 数据类型
            item_ids: 数据ID列表
            user: 当前用户

        Returns:
            批量恢复结果统计
        """
        return self._batch_operation(
            item_ids, lambda item_id: self.restore_item(item_type, item_id, user),
            success_key='restored'
        )

    def batch_permanent_delete(
        self,
        item_type: str,
        item_ids: List[int],
        user=None
    ) -> Dict[str, Any]:
        """
        批量彻底删除数据

        逐条调用 permanent_delete_item，收集成功和失败的结果。

        Args:
            item_type: 数据类型
            item_ids: 数据ID列表
            user: 当前用户

        Returns:
            批量删除结果统计
        """
        return self._batch_operation(
            item_ids,
            lambda item_id: self.permanent_delete_item(item_type, item_id, user),
            success_key='deleted'
        )

    def _batch_operation(
        self,
        item_ids: List[int],
        operation,
        success_key: str
    ) -> Dict[str, Any]:
        """
        批量操作的通用模板方法

        逐条执行操作，记录成功和失败的结果。

        Args:
            item_ids: 数据ID列表
            operation: 对单条数据执行的操作函数
            success_key: 成功结果的键名（'restored' 或 'deleted'）

        Returns:
            包含成功列表、失败列表及计数的字典
        """
        succeeded = []
        failed = []

        for item_id in item_ids:
            try:
                result = operation(item_id)
                succeeded.append(result)
            except Exception as e:
                logger.error(f"批量操作失败: id={item_id}, 错误: {str(e)}")
                failed.append({'id': item_id, 'error': str(e)})

        return {
            success_key: succeeded,
            f'{success_key}_count': len(succeeded),
            'failed': failed,
            'failed_count': len(failed)
        }

    def get_recycle_bin_stats(self, user=None) -> Dict[str, Any]:
        """
        获取回收站各类型的数据统计

        Args:
            user: 当前用户（非管理员只统计自己的数据）

        Returns:
            按类型分组的数量统计和总计
        """
        stats = {}

        for type_key, config in self.RECYCLE_BIN_MODELS.items():
            model_name = config['model']
            model_class = self.model_classes.get(model_name)

            if not model_class or not hasattr(model_class, 'is_deleted'):
                continue

            queryset = model_class.objects.filter(is_deleted=True)
            queryset = self._apply_permission_filter(queryset, model_class, user)

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
        将已删除的模型实例序列化为前端可展示的字典

        对于外键字段（如 project、owner），序列化为 {id, name} 格式。

        Args:
            item: 模型实例
            item_type: 数据类型标识符

        Returns:
            序列化后的字典
        """
        config = self.RECYCLE_BIN_MODELS.get(item_type, {})
        fields = config.get('fields', [])

        data = {
            'type': item_type,
            'display_type': config.get('display_name', item_type),
            'id': item.id,
            'name': getattr(item, 'name', str(item)),
        }

        for field in fields:
            # id 和 name 已在上面处理
            if field in ('id', 'name'):
                continue

            value = getattr(item, field, None)
            if value is None:
                continue

            # 外键字段序列化为 {id, name} 格式
            if hasattr(value, 'id'):
                data[field] = {
                    'id': value.id,
                    'name': getattr(value, 'name', str(value))
                }
            else:
                data[field] = value

        return data


# 全局服务实例，供视图层直接导入使用
recycle_bin_service = RecycleBinService()
