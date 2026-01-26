"""
api_automation/views.py

Django REST Framework 视图定义

注意：此文件需要重建。这是一个临时备份，包含原始文件的结构。
"""
from rest_framework import viewsets, status, permissions, views, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


def format_datetime(dt):
    """
    格式化日期时间为字符串
    输入: datetime 对象
    输出: 'YYYY-MM-DD HH:mm:ss' 格式字符串
    """
    if dt is None:
        return None
    # 如果是字符串，先转换为 datetime
    if isinstance(dt, str):
        try:
            dt = timezone.now().fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    # 格式化为 YYYY-MM-DD HH:mm:ss
    return dt.strftime('%Y-%m-%d %H:%M:%S')


from .models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
    ApiTestExecution, ApiTestReport, ApiTestResult, ApiDataDriver,
    ApiTestCaseAssertion, ApiTestCaseExtraction, ApiHttpExecutionRecord
)
from .serializers import (
    ApiProjectSerializer, ApiProjectDetailSerializer,
    ApiCollectionSerializer, ApiCollectionDetailSerializer,
    ApiTestCaseSerializer, ApiTestCaseListSerializer, ApiTestCaseDetailSerializer,
    ApiTestEnvironmentSerializer, ApiTestEnvironmentDetailSerializer,
    ApiTestExecutionSerializer, ApiTestExecutionDetailSerializer,
    ApiTestResultSerializer, ApiTestReportSerializer,
    ApiDataDriverSerializer, UserSerializer,
    ApiTestCaseAssertionSerializer, ApiTestCaseExtractionSerializer,
    ApiHttpExecutionRecordSerializer
)
from .services.cascade_delete_service import cascade_delete_service

# WebSocket服务导入
try:
    from .services.websocket_service import websocket_service
    WEBSOCKET_ENABLED = True
except ImportError:
    WEBSOCKET_ENABLED = False
    websocket_service = None


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Project Management'])
class ApiProjectViewSet(viewsets.ModelViewSet):
    """
    API项目视图集
    """
    serializer_class = ApiProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_time', 'updated_time', 'name']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的项目列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiProject.objects.none()
        queryset = ApiProject.objects.filter(is_deleted=False)
        if not user.is_superuser:
            queryset = queryset.filter(owner=user)
        return queryset

    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'retrieve':
            return ApiProjectDetailSerializer
        return ApiProjectSerializer

    def perform_destroy(self, instance):
        """软删除项目"""
        cascade = self.request.query_params.get('cascade', 'true').lower() == 'true'
        if cascade:
            cascade_delete_service.cascade_delete(instance)
        else:
            instance.is_deleted = True
            instance.save()

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """按项目执行所有测试用例"""
        from .services.batch_execution_service import BatchExecutionService
        project = self.get_object()
        environment_id = request.data.get('environment_id')
        if not environment_id:
            return Response({'error': '请选择执行环境'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            service = BatchExecutionService()
            execution = service.execute_by_project(
                project_id=project.id,
                environment_id=environment_id,
                user_id=request.user.id,
                execution_name=request.data.get('execution_name'),
            )
            serializer = ApiTestExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'执行失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# TODO: 继续添加其他ViewSet...
# 由于文件较长，先保存基本结构，然后继续添加其他ViewSet
