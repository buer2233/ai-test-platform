"""
api_automation/views_recycle_bin.py

回收站视图层，提供已软删除数据的查看、恢复和彻底删除功能。

主要端点:
    RecycleBinViewSet       -- 回收站列表、统计、单个/批量恢复与彻底删除
    internal_cleanup_view   -- 内部物理删除接口（仅限运维使用，需密钥认证）
"""
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .services.recycle_bin_service import recycle_bin_service


# =============================================================================
# 回收站视图集
# =============================================================================


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Recycle Bin'])
class RecycleBinViewSet(viewsets.ViewSet):
    """
    回收站视图集 -- 管理已软删除数据的查看、恢复和彻底删除。

    所有操作均委托给 recycle_bin_service 处理，视图层仅负责参数校验和响应封装。
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        获取回收站数据列表（支持分页和筛选）。

        查询参数:
            type      -- 数据类型筛选（如 apiproject, apicollection, apitestcase）
            search    -- 搜索关键词
            page      -- 页码（默认 1）
            page_size -- 每页数量（默认 20）
        """
        item_type = request.query_params.get('type', '').lower()
        search = request.query_params.get('search', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        result = recycle_bin_service.get_deleted_items(
            item_type=item_type if item_type else None,
            user=request.user,
            search=search if search else None,
            page=page,
            page_size=page_size
        )

        return Response(result)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取回收站各类型数据的统计信息。"""
        result = recycle_bin_service.get_recycle_bin_stats(user=request.user)
        return Response(result)

    @action(detail=False, methods=['post'], url_path='restore/(?P<item_type>[^/.]+)/(?P<item_id>[^/.]+)')
    def restore_item(self, request, item_type=None, item_id=None):
        """恢复单条已删除数据（将 is_deleted 重新设为 False）。"""
        try:
            item_id = int(item_id)
            result = recycle_bin_service.restore_item(item_type, item_id, request.user)
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': f'恢复失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='permanent-delete/(?P<item_type>[^/.]+)/(?P<item_id>[^/.]+)')
    def permanent_delete_item(self, request, item_type=None, item_id=None):
        """彻底删除单条数据（物理删除，不可恢复）。"""
        try:
            item_id = int(item_id)
            result = recycle_bin_service.permanent_delete_item(item_type, item_id, request.user)
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'error': f'删除失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def batch_restore(self, request):
        """批量恢复已删除数据，需提供 type 和 ids 列表。"""
        item_type = request.data.get('type', '')
        item_ids = request.data.get('ids', [])

        if not item_type or not item_ids:
            return Response({'error': '请提供数据类型和ID列表'}, status=status.HTTP_400_BAD_REQUEST)

        result = recycle_bin_service.batch_restore(item_type, item_ids, request.user)
        return Response(result)

    @action(detail=False, methods=['post'])
    def batch_permanent_delete(self, request):
        """批量彻底删除数据（物理删除），需提供 type 和 ids 列表。"""
        item_type = request.data.get('type', '')
        item_ids = request.data.get('ids', [])

        if not item_type or not item_ids:
            return Response({'error': '请提供数据类型和ID列表'}, status=status.HTTP_400_BAD_REQUEST)

        result = recycle_bin_service.batch_permanent_delete(item_type, item_ids, request.user)
        return Response(result)


# =============================================================================
# 内部运维接口
# =============================================================================


@swagger_auto_schema(method='post', tags=['Internal'], operation_description="内部物理删除接口")
@api_view(['POST'])
@permission_classes([])
def internal_cleanup_view(request):
    """
    内部物理删除接口（仅供研发运维使用）。

    通过 X-Internal-Auth 请求头验证内部密钥，
    支持级联和非级联两种物理删除模式。

    请求体:
        model   -- 模型名称（如 ApiProject, ApiCollection 等）
        ids     -- 要删除的记录 ID 列表
        cascade -- 是否级联删除（默认 true）
    """
    from django.conf import settings
    from .services.cascade_delete_service import cascade_delete_service

    # 验证内部认证密钥
    internal_key = request.headers.get('X-Internal-Auth', '')
    expected_key = getattr(settings, 'INTERNAL_API_KEY', 'your-internal-secret-key-change-in-production')

    if internal_key != expected_key:
        return Response({
            'error': '未授权访问',
            'message': '此接口仅供内部使用，需要正确的认证密钥'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # 获取参数
    model_name = request.data.get('model')
    ids = request.data.get('ids', [])
    cascade = request.data.get('cascade', True)

    if not model_name or not ids:
        return Response({
            'error': '参数不完整',
            'message': '请提供model和ids参数'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 执行物理删除
        if cascade:
            # 级联物理删除
            results = []
            for item_id in ids:
                try:
                    result = cascade_delete_service.permanent_delete(model_name, item_id)
                    results.append({
                        'id': item_id,
                        'status': 'success',
                        'result': result
                    })
                except Exception as e:
                    results.append({
                        'id': item_id,
                        'status': 'failed',
                        'error': str(e)
                    })

            return Response({
                'message': f'批量物理删除完成',
                'model': model_name,
                'results': results,
                'success_count': sum(1 for r in results if r['status'] == 'success'),
                'failed_count': sum(1 for r in results if r['status'] == 'failed')
            })
        else:
            # 直接物理删除（不级联）
            from ..models import (
                ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
                ApiTestExecution, ApiDataDriver
            )

            model_map = {
                'ApiProject': ApiProject,
                'ApiCollection': ApiCollection,
                'ApiTestCase': ApiTestCase,
                'ApiTestEnvironment': ApiTestEnvironment,
                'ApiTestExecution': ApiTestExecution,
                'ApiDataDriver': ApiDataDriver,
            }

            model_class = model_map.get(model_name)
            if not model_class:
                return Response({
                    'error': f'不支持的模型: {model_name}'
                }, status=status.HTTP_400_BAD_REQUEST)

            deleted_count, _ = model_class.objects.filter(id__in=ids).delete()

            return Response({
                'message': '物理删除完成',
                'model': model_name,
                'deleted_count': deleted_count
            })

    except Exception as e:
        return Response({
            'error': f'物理删除失败: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
