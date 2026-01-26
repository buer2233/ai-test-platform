"""
api_automation/views.py

Django REST Framework 视图定义
"""
from rest_framework import viewsets, status, permissions, views, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, F
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Case, When, IntegerField
from django.db.models.functions import Coalesce


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

    list:
    获取项目列表

    retrieve:
    获取项目详情

    create:
    创建新项目

    update:
    更新项目

    destroy:
    删除项目（软删除）

    execute:
    按项目执行所有测试用例
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
        """
        按项目执行所有测试用例

        执行指定项目下的所有测试用例
        """
        from .services.batch_execution_service import BatchExecutionService

        project = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            return Response(
                {'error': f'执行失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def collections(self, request, pk=None):
        """
        获取项目的集合列表

        返回指定项目下的所有集合
        """
        project = self.get_object()
        collections = project.api_collections.filter(is_deleted=False)
        page = self.paginate_queryset(collections)
        serializer = ApiCollectionSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'])
    def test_cases(self, request, pk=None):
        """
        获取项目的测试用例列表

        返回指定项目下的所有测试用例
        """
        project = self.get_object()
        test_cases = project.test_cases.filter(is_deleted=False)
        page = self.paginate_queryset(test_cases)
        serializer = ApiTestCaseListSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Collection Management'])
class ApiCollectionViewSet(viewsets.ModelViewSet):
    """
    API集合视图集

    list:
    获取集合列表

    retrieve:
    获取集合详情（包含测试用例）

    create:
    创建新集合

    update:
    更新集合

    destroy:
    删除集合（软删除）

    batch_add_test_cases:
    批量添加测试用例到集合

    batch_remove_test_cases:
    批量从集合移除测试用例

    execute:
    按集合执行测试用例
    """
    serializer_class = ApiCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']
    search_fields = ['name', 'description']
    ordering_fields = ['created_time', 'updated_time', 'name']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的集合列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiCollection.objects.none()

        queryset = ApiCollection.objects.filter(is_deleted=False)

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset

    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'retrieve':
            return ApiCollectionDetailSerializer
        return ApiCollectionSerializer

    def perform_destroy(self, instance):
        """软删除集合"""
        cascade = self.request.query_params.get('cascade', 'true').lower() == 'true'
        if cascade:
            cascade_delete_service.cascade_delete(instance)
        else:
            instance.is_deleted = True
            instance.save()

    @action(detail=True, methods=['post'])
    def batch_add_test_cases(self, request, pk=None):
        """
        批量添加测试用例到集合

        将多个测试用例添加到当前集合
        """
        collection = self.get_object()
        test_case_ids = request.data.get('test_case_ids', [])

        if not test_case_ids:
            return Response(
                {'error': '请选择要添加的测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 批量更新测试用例的集合
            updated_count = ApiTestCase.objects.filter(
                id__in=test_case_ids,
                project=collection.project,
                is_deleted=False
            ).update(collection=collection)

            return Response({
                'message': f'成功添加 {updated_count} 个测试用例到集合',
                'updated_count': updated_count
            })

        except Exception as e:
            return Response(
                {'error': f'添加失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def batch_remove_test_cases(self, request, pk=None):
        """
        批量从集合移除测试用例

        将多个测试用例从当前集合移除（设置为不归属任何集合）
        """
        collection = self.get_object()
        test_case_ids = request.data.get('test_case_ids', [])

        if not test_case_ids:
            return Response(
                {'error': '请选择要移除的测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 批量更新测试用例的集合为NULL
            updated_count = ApiTestCase.objects.filter(
                id__in=test_case_ids,
                collection=collection,
                is_deleted=False
            ).update(collection=None)

            return Response({
                'message': f'成功从集合移除 {updated_count} 个测试用例',
                'updated_count': updated_count
            })

        except Exception as e:
            return Response(
                {'error': f'移除失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        按集合执行测试用例

        执行集合中的所有测试用例
        """
        from .services.batch_execution_service import BatchExecutionService

        collection = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = BatchExecutionService()
            execution = service.execute_by_collection(
                collection_id=collection.id,
                environment_id=environment_id,
                user_id=request.user.id,
                execution_name=request.data.get('execution_name'),
            )

            serializer = ApiTestExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'执行失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Test Case Management'])
class ApiTestCaseViewSet(viewsets.ModelViewSet):
    """
    API测试用例视图集

    list:
    获取测试用例列表

    retrieve:
    获取测试用例详情（包含断言和数据提取配置）

    create:
    创建新测试用例

    update:
    更新测试用例

    destroy:
    删除测试用例（软删除）

    batch_execute:
    批量执行测试用例（手动选择）
    """
    serializer_class = ApiTestCaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'collection', 'method']
    search_fields = ['name', 'description', 'url']
    ordering_fields = ['created_time', 'updated_time', 'name']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的测试用例列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiTestCase.objects.none()

        queryset = ApiTestCase.objects.filter(is_deleted=False)

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset.select_related('project', 'collection', 'created_by')

    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'retrieve':
            return ApiTestCaseDetailSerializer
        elif self.action == 'list':
            return ApiTestCaseListSerializer
        return ApiTestCaseSerializer

    def perform_destroy(self, instance):
        """软删除测试用例"""
        cascade = self.request.query_params.get('cascade', 'true').lower() == 'true'
        if cascade:
            cascade_delete_service.cascade_delete(instance)
        else:
            instance.is_deleted = True
            instance.save()

    @action(detail=False, methods=['post'])
    def batch_execute(self, request):
        """
        批量执行测试用例（手动选择）

        执行用户手动选择的测试用例
        """
        from .services.batch_execution_service import BatchExecutionService

        test_case_ids = request.data.get('test_case_ids', [])
        environment_id = request.data.get('environment_id')

        if not test_case_ids:
            return Response(
                {'error': '请选择要执行的测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = BatchExecutionService()
            execution = service.execute_by_selection(
                test_case_ids=test_case_ids,
                environment_id=environment_id,
                user_id=request.user.id,
                execution_name=request.data.get('execution_name'),
            )

            serializer = ApiTestExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'执行失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def run_test(self, request, pk=None):
        """
        执行单个测试用例

        执行指定的测试用例并返回执行结果
        """
        from .services.batch_execution_service import BatchExecutionService

        test_case = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service = BatchExecutionService()
            execution = service.execute_by_selection(
                test_case_ids=[test_case.id],
                environment_id=environment_id,
                user_id=request.user.id,
                execution_name=f"单用例执行: {test_case.name}",
            )

            serializer = ApiTestExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'执行失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Environment Management'])
class ApiTestEnvironmentViewSet(viewsets.ModelViewSet):
    """
    API测试环境视图集

    list:
    获取环境列表

    retrieve:
    获取环境详情

    create:
    创建新环境

    update:
    更新环境

    destroy:
    删除环境（软删除）

    test_connection:
    测试环境连接
    """
    serializer_class = ApiTestEnvironmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'is_default', 'is_active', 'is_favorite']
    search_fields = ['name', 'description', 'base_url']
    ordering_fields = ['created_time', 'updated_time', 'is_favorite', 'name']
    ordering = ['-is_favorite', '-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的环境列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiTestEnvironment.objects.none()

        queryset = ApiTestEnvironment.objects.filter(is_deleted=False)

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset.select_related('project')

    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'retrieve':
            return ApiTestEnvironmentDetailSerializer
        return ApiTestEnvironmentSerializer

    def perform_destroy(self, instance):
        """软删除环境"""
        instance.is_deleted = True
        instance.save()

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        测试环境连接

        测试环境的base_url是否可访问
        """
        import requests

        environment = self.get_object()

        try:
            # 尝试访问base_url
            response = requests.get(
                environment.base_url,
                headers=environment.global_headers,
                timeout=10
            )

            return Response({
                'status': 'success',
                'message': '环境连接正常',
                'response_status': response.status_code,
                'response_time': response.elapsed.total_seconds() * 1000
            })

        except requests.exceptions.Timeout:
            return Response({
                'status': 'error',
                'message': '连接超时'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)

        except requests.exceptions.ConnectionError:
            return Response({
                'status': 'error',
                'message': '无法连接到服务器'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'连接失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Execution Management'])
class ApiTestExecutionViewSet(viewsets.ModelViewSet):
    """
    API测试执行视图集

    list:
    获取执行记录列表

    retrieve:
    获取执行记录详情

    destroy:
    删除执行记录

    cancel:
    取消执行
    """
    serializer_class = ApiTestExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'environment', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_time', 'start_time', 'end_time']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的执行记录列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiTestExecution.objects.none()

        queryset = ApiTestExecution.objects.all()

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset.select_related(
            'project', 'environment', 'created_by'
        ).prefetch_related('test_results')

    def get_serializer_class(self):
        """根据action选择不同的序列化器"""
        if self.action == 'retrieve':
            return ApiTestExecutionDetailSerializer
        return ApiTestExecutionSerializer

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        取消执行

        取消正在运行的测试执行
        """
        execution = self.get_object()

        if execution.status not in ['PENDING', 'RUNNING']:
            return Response({
                'error': f'无法取消状态为 {execution.status} 的执行'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            execution.status = 'CANCELLED'
            execution.end_time = timezone.now()
            execution.save()

            # 通过WebSocket通知取消
            if WEBSOCKET_ENABLED and websocket_service:
                websocket_service.broadcast_execution_update(
                    execution.id,
                    {'status': 'CANCELLED', 'message': '执行已取消'}
                )

            return Response({
                'message': '执行已取消',
                'execution_id': execution.id
            })

        except Exception as e:
            return Response({
                'error': f'取消失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Test Result Management'])
class ApiTestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API测试结果视图集（只读）

    list:
    获取测试结果列表

    retrieve:
    获取测试结果详情
    """
    serializer_class = ApiTestResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['execution', 'test_case', 'status']
    search_fields = ['test_case__name', 'test_case__url']
    ordering_fields = ['created_time', 'start_time', 'response_time']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的测试结果列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiTestResult.objects.none()

        queryset = ApiTestResult.objects.all()

        # 非超级用户只能查看自己项目的测试结果
        if not user.is_superuser:
            queryset = queryset.filter(execution__project__owner=user)

        return queryset.select_related(
            'execution', 'test_case', 'execution__project', 'execution__environment'
        )


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Report Management'])
class ApiTestReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API测试报告视图集（只读）

    list:
    获取报告列表

    retrieve:
    获取报告详情
    """
    serializer_class = ApiTestReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['execution']
    search_fields = ['name']
    ordering_fields = ['created_time', 'updated_time']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的报告列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiTestReport.objects.none()

        queryset = ApiTestReport.objects.all()

        if not user.is_superuser:
            queryset = queryset.filter(execution__project__owner=user)

        return queryset.select_related('execution', 'execution__project')


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Data Driver Management'])
class ApiDataDriverViewSet(viewsets.ModelViewSet):
    """
    API数据驱动视图集

    list:
    获取数据驱动配置列表

    retrieve:
    获取数据驱动配置详情

    create:
    创建数据驱动配置

    update:
    更新数据驱动配置

    destroy:
    删除数据驱动配置（软删除）
    """
    serializer_class = ApiDataDriverSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'test_case', 'data_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_time', 'updated_time', 'name']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的数据驱动配置列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiDataDriver.objects.none()

        queryset = ApiDataDriver.objects.filter(is_deleted=False)

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset.select_related('project', 'test_case')

    def perform_destroy(self, instance):
        """软删除数据驱动配置"""
        instance.is_deleted = True
        instance.save()


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['HTTP Execution Records'])
class ApiHttpExecutionRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    HTTP执行记录视图集（只读）

    list:
    获取HTTP执行记录列表

    retrieve:
    获取HTTP执行记录详情
    """
    serializer_class = ApiHttpExecutionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'test_case', 'execution', 'project', 'environment',
        'status', 'request_method', 'execution_source', 'is_favorite'
    ]
    search_fields = ['request_url', 'test_case__name']
    ordering_fields = ['created_time', 'request_time', 'response_time', 'duration']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取当前用户有权访问的HTTP执行记录列表"""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ApiHttpExecutionRecord.objects.none()

        queryset = ApiHttpExecutionRecord.objects.all()

        if not user.is_superuser:
            queryset = queryset.filter(project__owner=user)

        return queryset.select_related(
            'test_case', 'execution', 'project', 'environment', 'executed_by'
        )


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Dashboard'])
class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard视图集

    提供仪表盘统计数据和报告
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """
        获取Dashboard统计数据

        返回项目的统计信息，包括：
        - 总项目数
        - 总集合数
        - 总测试用例数
        - 总执行记录数
        - 最近执行记录

        支持筛选参数：
        - project_id: 项目ID
        - collection_id: 集合ID
        - owner_id: 负责人ID
        - module: 模块名称
        - start_date: 开始日期（YYYY-MM-DD）
        - end_date: 结束日期（YYYY-MM-DD）
        """
        user = request.user

        # 获取筛选参数
        project_id = request.query_params.get('project_id')
        collection_id = request.query_params.get('collection_id')
        owner_id = request.query_params.get('owner_id')
        module = request.query_params.get('module')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 基础查询
        if user.is_superuser:
            projects = ApiProject.objects.filter(is_deleted=False)
        else:
            projects = ApiProject.objects.filter(owner=user, is_deleted=False)

        # 应用筛选参数
        if project_id:
            projects = projects.filter(id=project_id)

        # 获取筛选后的项目列表
        project_ids = list(projects.values_list('id', flat=True))

        # 构建基础过滤条件
        base_filters = {'is_deleted': False}
        test_case_filters = {}
        execution_filters = {}

        # 集合筛选
        if collection_id:
            # 如果指定了集合，只显示该集合相关数据
            base_filters['id'] = collection_id
            test_case_filters['collection_id'] = collection_id

        # 负责人筛选
        if owner_id:
            test_case_filters['owner_id'] = owner_id

        # 模块筛选
        if module:
            test_case_filters['module'] = module

        # 时间范围筛选
        date_filters = Q()
        if start_date:
            try:
                start_datetime = timezone.make_aware(
                    timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                )
                date_filters &= Q(created_time__gte=start_datetime)
            except ValueError:
                pass

        if end_date:
            try:
                end_datetime = timezone.make_aware(
                    timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                )
                date_filters &= Q(created_time__lte=end_datetime)
            except ValueError:
                pass

        # 统计数据
        stats = {
            'total_projects': projects.count(),
            'total_collections': ApiCollection.objects.filter(
                project__in=project_ids, is_deleted=False
            ).count(),
            'total_test_cases': ApiTestCase.objects.filter(
                project__in=project_ids, is_deleted=False, **test_case_filters
            ).count(),
            'total_environments': ApiTestEnvironment.objects.filter(
                project__in=project_ids, is_deleted=False
            ).count(),
        }

        # 执行统计（应用时间范围筛选）
        execution_queryset = ApiTestExecution.objects.filter(project__in=project_ids)
        if date_filters:
            execution_queryset = execution_queryset.filter(date_filters)

        stats['total_executions'] = execution_queryset.count()

        # 执行状态统计
        execution_stats = execution_queryset.aggregate(
            total_executions=Count('id'),
            completed_executions=Count('id', filter=Q(status='COMPLETED')),
            running_executions=Count('id', filter=Q(status='RUNNING')),
            failed_executions=Count('id', filter=Q(status='FAILED')),
        )

        stats.update(execution_stats)

        # 测试结果统计（应用筛选条件）
        result_queryset = ApiTestResult.objects.filter(execution__project__in=project_ids)

        # 应用测试用例筛选
        if test_case_filters:
            result_queryset = result_queryset.filter(test_case__in=ApiTestCase.objects.filter(
                project__in=project_ids, is_deleted=False, **test_case_filters
            ))

        result_stats = result_queryset.aggregate(
            total_results=Count('id'),
            passed_results=Count('id', filter=Q(status='PASSED')),
            failed_results=Count('id', filter=Q(status='FAILED')),
            skipped_results=Count('id', filter=Q(status='SKIPPED')),
            error_results=Count('id', filter=Q(status='ERROR')),
        )

        stats.update(result_stats)

        # 计算通过率
        if stats['total_results'] > 0:
            stats['pass_rate'] = round(
                (stats['passed_results'] / stats['total_results']) * 100, 2
            )
        else:
            stats['pass_rate'] = 0.0

        # 最近执行记录（最近10条）
        recent_executions = execution_queryset.select_related(
            'project', 'environment', 'created_by'
        ).order_by('-created_time')[:10]

        execution_serializer = ApiTestExecutionSerializer(
            recent_executions, many=True
        )

        # 构建符合前端期望的响应结构
        # overview: 基础项目统计
        overview = {
            'total_projects': stats['total_projects'],
            'total_collections': stats['total_collections'],
            'total_test_cases': stats['total_test_cases'],
            'total_executions': stats['total_executions']
        }

        # test_stats: 测试结果统计（重命名以匹配前端期望）
        test_stats = {
            'total_cases': stats.get('total_results', 0),
            'passed_cases': stats.get('passed_results', 0),
            'failed_cases': stats.get('failed_results', 0),
            'skipped_cases': stats.get('skipped_results', 0),
            'error_cases': stats.get('error_results', 0),
            'pass_rate': stats.get('pass_rate', 0.0),
            'avg_response_time': 0  # 暂时设为0，可后续计算
        }

        return Response({
            'overview': overview,
            'test_stats': test_stats,
            'recent_results': execution_serializer.data
        })

    @action(detail=False, methods=['get'])
    def environment_reports(self, request):
        """
        按环境维度获取报告

        返回每个环境的测试执行统计
        """
        user = request.user

        # 基础查询
        if user.is_superuser:
            projects = ApiProject.objects.filter(is_deleted=False)
        else:
            projects = ApiProject.objects.filter(owner=user, is_deleted=False)

        # 获取有执行记录的环境
        environments = ApiTestEnvironment.objects.filter(
            project__in=projects,
            is_deleted=False,
            test_executions__isnull=False
        ).distinct().select_related('project')

        # 为每个环境统计执行结果
        environment_data = []
        for env in environments:
            executions = ApiTestExecution.objects.filter(
                environment=env,
                project__in=projects
            )

            # 统计该环境的所有执行结果
            results = ApiTestResult.objects.filter(
                execution__in=executions
            ).aggregate(
                total=Count('id'),
                passed=Count('id', filter=Q(status='PASSED')),
                failed=Count('id', filter=Q(status='FAILED')),
                skipped=Count('id', filter=Q(status='SKIPPED')),
                error=Count('id', filter=Q(status='ERROR')),
            )

            # 计算通过率
            if results['total'] > 0:
                pass_rate = round((results['passed'] / results['total']) * 100, 2)
            else:
                pass_rate = 0.0

            environment_data.append({
                'environment_id': env.id,
                'environment_name': env.name,
                'project_name': env.project.name,
                'base_url': env.base_url,
                'total_executions': executions.count(),
                'total_results': results['total'],
                'passed': results['passed'],
                'failed': results['failed'],
                'skipped': results['skipped'],
                'error': results['error'],
                'pass_rate': pass_rate,
            })

        # 按执行次数降序排序
        environment_data.sort(key=lambda x: x['total_executions'], reverse=True)

        # 构建符合前端期望的响应结构
        formatted_data = []
        for item in environment_data:
            formatted_data.append({
                'environment_id': item['environment_id'],
                'environment_name': item['environment_name'],
                'project_id': 0,  # 需要从project_name获取
                'project_name': item['project_name'],
                'base_url': item['base_url'],
                'execution_id': None,  # 可以从最新的执行记录获取
                'execution_name': None,
                'execution_status': None,
                'stats': {
                    'total': item['total_results'],
                    'passed': item['passed'],
                    'failed': item['failed'],
                    'skipped': item['skipped'],
                    'error': item['error'],
                    'pass_rate': item['pass_rate']
                },
                'avg_response_time': 0,  # 可以计算平均响应时间
                'last_execution_time': None
            })

        return Response({
            'results': formatted_data,
            'count': len(formatted_data)
        })

    @action(detail=False, methods=['get'])
    def collection_reports(self, request):
        """
        按集合维度获取报告

        返回每个集合的测试执行统计
        """
        user = request.user

        # 基础查询
        if user.is_superuser:
            projects = ApiProject.objects.filter(is_deleted=False)
        else:
            projects = ApiProject.objects.filter(owner=user, is_deleted=False)

        # 获取有执行记录的集合
        collection_ids = ApiTestResult.objects.filter(
            execution__project__in=projects
        ).values_list('test_case__collection_id', flat=True).distinct()

        collections = ApiCollection.objects.filter(
            id__in=collection_ids,
            is_deleted=False
        ).select_related('project')

        # 为每个集合统计执行结果
        collection_data = []
        for collection in collections:
            # 获取集合的所有测试用例
            test_cases = ApiTestCase.objects.filter(
                collection=collection,
                is_deleted=False
            )

            # 获取这些测试用例的执行结果
            results = ApiTestResult.objects.filter(
                test_case__in=test_cases,
                execution__project__in=projects
            ).aggregate(
                total=Count('id'),
                passed=Count('id', filter=Q(status='PASSED')),
                failed=Count('id', filter=Q(status='FAILED')),
                skipped=Count('id', filter=Q(status='SKIPPED')),
                error=Count('id', filter=Q(status='ERROR')),
            )

            # 计算通过率
            if results['total'] > 0:
                pass_rate = round((results['passed'] / results['total']) * 100, 2)
            else:
                pass_rate = 0.0

            collection_data.append({
                'collection_id': collection.id,
                'collection_name': collection.name,
                'project_name': collection.project.name,
                'test_cases_count': test_cases.count(),
                'total_results': results['total'],
                'passed': results['passed'],
                'failed': results['failed'],
                'skipped': results['skipped'],
                'error': results['error'],
                'pass_rate': pass_rate,
            })

        # 按结果总数降序排序
        collection_data.sort(key=lambda x: x['total_results'], reverse=True)

        # 构建符合前端期望的响应结构
        formatted_data = []
        for item in collection_data:
            formatted_data.append({
                'collection_id': item['collection_id'],
                'collection_name': item['collection_name'],
                'project_id': 0,  # 需要从project_name获取
                'project_name': item['project_name'],
                'test_case_count': item['test_cases_count'],
                'execution_id': None,
                'execution_name': None,
                'execution_status': None,
                'stats': {
                    'total': item['total_results'],
                    'passed': item['passed'],
                    'failed': item['failed'],
                    'skipped': item['skipped'],
                    'error': item['error'],
                    'pass_rate': item['pass_rate']
                },
                'avg_response_time': 0,
                'last_execution_time': None
            })

        return Response({
            'results': formatted_data,
            'count': len(formatted_data)
        })

    @action(detail=False, methods=['get'])
    def project_reports(self, request):
        """
        按项目维度获取报告

        返回每个项目的测试执行统计

        支持筛选参数：
        - project_id: 项目ID
        - collection_id: 集合ID
        - owner_id: 负责人ID
        - module: 模块名称
        - start_date: 开始日期
        - end_date: 结束日期
        """
        user = request.user

        # 获取筛选参数
        project_id = request.query_params.get('project_id')
        collection_id = request.query_params.get('collection_id')
        owner_id = request.query_params.get('owner_id')
        module = request.query_params.get('module')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 基础查询
        if user.is_superuser:
            projects = ApiProject.objects.filter(is_deleted=False)
        else:
            projects = ApiProject.objects.filter(owner=user, is_deleted=False)

        # 应用筛选参数
        if project_id:
            projects = projects.filter(id=project_id)

        # 获取筛选后的项目列表
        project_ids = list(projects.values_list('id', flat=True))

        # 构建测试用例筛选条件
        test_case_filters = {'is_deleted': False}
        if collection_id:
            test_case_filters['collection_id'] = collection_id
        if owner_id:
            test_case_filters['owner_id'] = owner_id
        if module:
            test_case_filters['module'] = module

        # 时间范围筛选
        date_filters = Q()
        if start_date:
            try:
                start_datetime = timezone.make_aware(
                    timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                )
                date_filters &= Q(created_time__gte=start_datetime)
            except ValueError:
                pass

        if end_date:
            try:
                end_datetime = timezone.make_aware(
                    timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                )
                date_filters &= Q(created_time__lte=end_datetime)
            except ValueError:
                pass

        # 为每个项目统计执行结果
        project_data = []
        for project in projects:
            # 获取该项目的所有测试用例
            test_cases = ApiTestCase.objects.filter(
                project=project,
                **test_case_filters
            )

            if test_cases.count() == 0:
                continue

            # 获取这些测试用例的执行结果
            executions = ApiTestExecution.objects.filter(project=project)
            if date_filters:
                executions = executions.filter(date_filters)

            if executions.count() == 0:
                continue

            # 统计该项目的所有执行结果
            results = ApiTestResult.objects.filter(
                execution__in=executions,
                test_case__in=test_cases
            ).aggregate(
                total=Count('id'),
                passed=Count('id', filter=Q(status='PASSED')),
                failed=Count('id', filter=Q(status='FAILED')),
                skipped=Count('id', filter=Q(status='SKIPPED')),
                error=Count('id', filter=Q(status='ERROR')),
            )

            # 计算通过率
            if results['total'] > 0:
                pass_rate = round((results['passed'] / results['total']) * 100, 2)
            else:
                pass_rate = 0.0

            # 获取最后执行时间
            last_execution = executions.order_by('-created_time').first()
            last_execution_time = last_execution.created_time if last_execution else None

            project_data.append({
                'project_id': project.id,
                'project_name': project.name,
                'owner_id': project.owner_id if project.owner else None,
                'owner_name': project.owner.username if project.owner else None,
                'test_cases_count': test_cases.count(),
                'total_executions': executions.count(),
                'total_results': results['total'],
                'passed': results['passed'],
                'failed': results['failed'],
                'skipped': results['skipped'],
                'error': results['error'],
                'pass_rate': pass_rate,
                'avg_response_time': 0,  # 可后续计算
                'last_execution_time': last_execution_time
            })

        # 按执行次数降序排序
        project_data.sort(key=lambda x: x['total_executions'], reverse=True)

        # 构建符合前端期望的响应结构
        formatted_data = []
        for item in project_data:
            formatted_data.append({
                'project_id': item['project_id'],
                'project_name': item['project_name'],
                'owner_id': item['owner_id'],
                'owner_name': item['owner_name'],
                'stats': {
                    'total': item['total_results'],
                    'passed': item['passed'],
                    'failed': item['failed'],
                    'skipped': item['skipped'],
                    'error': item['error'],
                    'pass_rate': item['pass_rate']
                },
                'avg_response_time': item['avg_response_time'],
                'last_execution_time': item['last_execution_time']
            })

        return Response({
            'results': formatted_data,
            'count': len(formatted_data)
        })

    @action(detail=False, methods=['get'])
    def test_results(self, request):
        """
        获取测试结果详情

        支持筛选参数：
        - environment_id: 环境ID
        - collection_id: 集合ID
        - project_id: 项目ID
        - owner_id: 负责人ID
        - module: 模块名称
        - status: 测试状态
        - start_date: 开始日期
        - end_date: 结束日期
        """
        user = request.user

        # 获取筛选参数
        environment_id = request.query_params.get('environment_id')
        collection_id = request.query_params.get('collection_id')
        project_id = request.query_params.get('project_id')
        owner_id = request.query_params.get('owner_id')
        module = request.query_params.get('module')
        result_status = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # 基础查询
        if user.is_superuser:
            projects = ApiProject.objects.filter(is_deleted=False)
        else:
            projects = ApiProject.objects.filter(owner=user, is_deleted=False)

        # 应用项目筛选
        if project_id:
            projects = projects.filter(id=project_id)

        queryset = ApiTestResult.objects.filter(
            execution__project__in=projects
        ).select_related(
            'execution', 'test_case', 'test_case__collection'
        )

        # 应用筛选参数
        if environment_id:
            queryset = queryset.filter(execution__environment_id=environment_id)

        if collection_id:
            queryset = queryset.filter(test_case__collection_id=collection_id)

        if result_status:
            queryset = queryset.filter(status=result_status)

        # 新增筛选：负责人和模块
        if owner_id or module:
            test_case_filters = {'is_deleted': False}
            if owner_id:
                test_case_filters['owner_id'] = owner_id
            if module:
                test_case_filters['module'] = module
            queryset = queryset.filter(test_case__in=ApiTestCase.objects.filter(**test_case_filters))

        # 时间范围筛选
        if start_date:
            try:
                start_datetime = timezone.make_aware(
                    timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                )
                queryset = queryset.filter(start_time__gte=start_datetime)
            except ValueError:
                pass

        if end_date:
            try:
                end_datetime = timezone.make_aware(
                    timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                )
                queryset = queryset.filter(start_time__lte=end_datetime)
            except ValueError:
                pass

        # 分页
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 20)

        start = (int(page) - 1) * int(page_size)
        end = start + int(page_size)

        results = queryset[start:end]
        total = queryset.count()

        # 序列化结果
        result_serializer = ApiTestResultSerializer(results, many=True)

        # 计算总页数
        page_size_int = int(page_size)
        total_pages = (total + page_size_int - 1) // page_size_int if total > 0 else 0

        return Response({
            'results': result_serializer.data,
            'count': total,
            'page': int(page),
            'page_size': int(page_size),
            'total_pages': total_pages
        })

    @action(detail=False, methods=['post'])
    def retry_failed(self, request):
        """
        重试失败用例

        支持两种模式：
        - scope='all': 重试当前筛选条件下的所有失败用例
        - scope='selected': 重试选中的失败用例

        请求参数：
        - scope: 'all' 或 'selected'
        - test_result_ids: scope='selected'时必填，选中的测试结果ID列表
        - environment_id: 测试环境ID
        - execution_name: 可选，执行名称
        """
        from .services.batch_execution_service import BatchExecutionService

        scope = request.data.get('scope')
        test_result_ids = request.data.get('test_result_ids', [])
        environment_id = request.data.get('environment_id')
        execution_name = request.data.get('execution_name', '重试执行')

        # 验证环境参数
        if not environment_id:
            return Response(
                {'detail': '请选择测试环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取环境
        try:
            environment = ApiTestEnvironment.objects.get(id=environment_id, is_deleted=False)
        except ApiTestEnvironment.DoesNotExist:
            return Response(
                {'detail': '测试环境不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        user = request.user

        # 确定要重试的测试用例
        test_case_ids = []

        if scope == 'all':
            # 重试当前筛选条件下的所有失败用例
            # 获取用户有权访问的项目
            if user.is_superuser:
                projects = ApiProject.objects.filter(is_deleted=False)
            else:
                projects = ApiProject.objects.filter(owner=user, is_deleted=False)

            # 获取失败的测试结果
            failed_results = ApiTestResult.objects.filter(
                execution__project__in=projects,
                status__in=['FAILED', 'ERROR']
            ).values_list('test_case_id', flat=True).distinct()

            test_case_ids = list(failed_results)

        elif scope == 'selected':
            # 重试选中的失败用例
            if not test_result_ids:
                return Response(
                    {'detail': '请选择要重试的测试结果'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 验证测试结果并获取对应的测试用例
            failed_results = ApiTestResult.objects.filter(
                id__in=test_result_ids,
                status__in=['FAILED', 'ERROR']
            ).values_list('test_case_id', flat=True).distinct()

            test_case_ids = list(failed_results)
        else:
            return Response(
                {'detail': '无效的scope参数'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not test_case_ids:
            return Response(
                {'detail': '没有找到需要重试的失败用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建执行记录
        execution = ApiTestExecution.objects.create(
            project=environment.project,
            environment=environment,
            name=execution_name,
            status='PENDING',
            created_by=user
        )

        # 使用批量执行服务
        batch_service = BatchExecutionService()

        try:
            # 异步执行测试
            batch_service.execute_batch(
                execution_id=execution.id,
                test_case_ids=test_case_ids,
                environment_id=environment_id
            )

            execution_serializer = ApiTestExecutionSerializer(execution)

            return Response({
                'id': execution.id,
                'name': execution.name,
                'status': execution.status,
                'message': f'已创建重试任务，共 {len(test_case_ids)} 个用例'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            execution.status = 'FAILED'
            execution.save()
            return Response(
                {'detail': f'创建重试任务失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Test Case Assertions'])
class ApiTestCaseAssertionViewSet(viewsets.ModelViewSet):
    """
    API测试用例断言配置视图集

    list:
    获取测试用例的断言配置列表

    retrieve:
    获取断言配置详情

    create:
    创建断言配置

    update:
    更新断言配置

    destroy:
    删除断言配置

    batch_update:
    批量更新断言配置
    """
    serializer_class = ApiTestCaseAssertionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test_case', 'assertion_type', 'is_enabled']
    search_fields = ['target', 'expected_value']
    ordering_fields = ['order', 'created_time']
    ordering = ['order', 'created_time']

    def get_queryset(self):
        """获取断言配置列表"""
        user = self.request.user

        if getattr(self, 'swagger_fake_view', False):
            return ApiTestCaseAssertion.objects.none()

        queryset = ApiTestCaseAssertion.objects.all()

        # 从URL参数获取test_case_id
        test_case_id = self.kwargs.get('test_case_id')
        if test_case_id:
            queryset = queryset.filter(test_case_id=test_case_id)
        elif not user.is_superuser:
            # 如果没有指定test_case_id，只返回用户有权限的
            queryset = queryset.filter(
                test_case__project__owner=user
            )

        return queryset.select_related('test_case')

    def perform_create(self, serializer):
        """创建时自动设置test_case"""
        test_case_id = self.kwargs.get('test_case_id')
        if test_case_id:
            serializer.save(test_case_id=test_case_id)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        批量更新断言配置

        支持批量启用/禁用、删除、更新排序等操作
        """
        test_case_id = self.kwargs.get('test_case_id')
        action_type = request.data.get('action')  # enable, disable, delete, reorder
        assertion_ids = request.data.get('assertion_ids', [])

        if not assertion_ids:
            return Response({
                'error': '请选择要操作的断言配置'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if action_type == 'enable':
                updated = ApiTestCaseAssertion.objects.filter(
                    id__in=assertion_ids,
                    test_case_id=test_case_id
                ).update(is_enabled=True)

                return Response({
                    'message': f'成功启用 {updated} 个断言配置',
                    'updated_count': updated
                })

            elif action_type == 'disable':
                updated = ApiTestCaseAssertion.objects.filter(
                    id__in=assertion_ids,
                    test_case_id=test_case_id
                ).update(is_enabled=False)

                return Response({
                    'message': f'成功禁用 {updated} 个断言配置',
                    'updated_count': updated
                })

            elif action_type == 'delete':
                deleted, _ = ApiTestCaseAssertion.objects.filter(
                    id__in=assertion_ids,
                    test_case_id=test_case_id
                ).delete()

                return Response({
                    'message': f'成功删除 {deleted} 个断言配置',
                    'deleted_count': deleted
                })

            elif action_type == 'reorder':
                # 批量更新排序
                order_data = request.data.get('order_data', {})
                for assertion_id, new_order in order_data.items():
                    ApiTestCaseAssertion.objects.filter(
                        id=assertion_id,
                        test_case_id=test_case_id
                    ).update(order=new_order)

                return Response({
                    'message': '排序更新成功'
                })

            else:
                return Response({
                    'error': f'不支持的操作: {action_type}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': f'批量操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Test Case Extractions'])
class ApiTestCaseExtractionViewSet(viewsets.ModelViewSet):
    """
    API测试用例数据提取配置视图集

    list:
    获取测试用例的数据提取配置列表

    retrieve:
    获取数据提取配置详情

    create:
    创建数据提取配置

    update:
    更新数据提取配置

    destroy:
    删除数据提取配置

    batch_update:
    批量更新数据提取配置
    """
    serializer_class = ApiTestCaseExtractionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['test_case', 'extract_type', 'extract_scope', 'variable_scope', 'is_enabled']
    search_fields = ['variable_name', 'extract_expression']
    ordering_fields = ['created_time']
    ordering = ['created_time']

    def get_queryset(self):
        """获取数据提取配置列表"""
        user = self.request.user

        if getattr(self, 'swagger_fake_view', False):
            return ApiTestCaseExtraction.objects.none()

        queryset = ApiTestCaseExtraction.objects.all()

        # 从URL参数获取test_case_id
        test_case_id = self.kwargs.get('test_case_id')
        if test_case_id:
            queryset = queryset.filter(test_case_id=test_case_id)
        elif not user.is_superuser:
            # 如果没有指定test_case_id，只返回用户有权限的
            queryset = queryset.filter(
                test_case__project__owner=user
            )

        return queryset.select_related('test_case')

    def perform_create(self, serializer):
        """创建时自动设置test_case"""
        test_case_id = self.kwargs.get('test_case_id')
        if test_case_id:
            serializer.save(test_case_id=test_case_id)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        批量更新数据提取配置

        支持批量启用/禁用、删除等操作
        """
        test_case_id = self.kwargs.get('test_case_id')
        action_type = request.data.get('action')  # enable, disable, delete
        extraction_ids = request.data.get('extraction_ids', [])

        if not extraction_ids:
            return Response({
                'error': '请选择要操作的数据提取配置'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            if action_type == 'enable':
                updated = ApiTestCaseExtraction.objects.filter(
                    id__in=extraction_ids,
                    test_case_id=test_case_id
                ).update(is_enabled=True)

                return Response({
                    'message': f'成功启用 {updated} 个数据提取配置',
                    'updated_count': updated
                })

            elif action_type == 'disable':
                updated = ApiTestCaseExtraction.objects.filter(
                    id__in=extraction_ids,
                    test_case_id=test_case_id
                ).update(is_enabled=False)

                return Response({
                    'message': f'成功禁用 {updated} 个数据提取配置',
                    'updated_count': updated
                })

            elif action_type == 'delete':
                deleted, _ = ApiTestCaseExtraction.objects.filter(
                    id__in=extraction_ids,
                    test_case_id=test_case_id
                ).delete()

                return Response({
                    'message': f'成功删除 {deleted} 个数据提取配置',
                    'deleted_count': deleted
                })

            else:
                return Response({
                    'error': f'不支持的操作: {action_type}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': f'批量操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Users'])
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用户视图集（只读 + 注册）

    list:
    获取用户列表

    retrieve:
    获取用户详情

    register:
    用户注册
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取用户列表"""
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        return User.objects.all().order_by('id')

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        用户注册

        POST /api/v1/api-automation/users/register/
        {
            "username": "newuser",
            "password": "password123",
            "email": "user@example.com"
        }
        """
        from django.contrib.auth.models import User

        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        # 验证必填字段
        if not username or not password:
            return Response({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return Response({
                'code': 400,
                'message': '用户名已存在',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 检查邮箱是否已存在
        if email and User.objects.filter(email=email).exists():
            return Response({
                'code': 400,
                'message': '邮箱已被使用',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建新用户
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            return Response({
                'code': 201,
                'message': '注册成功',
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'注册失败: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
@swagger_auto_schema(tags=['Authentication'])
class CurrentUserView(views.APIView):
    """
    当前用户信息视图

    get:
    获取当前登录用户的信息
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """返回当前用户信息"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
