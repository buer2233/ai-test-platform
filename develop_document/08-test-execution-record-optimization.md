# 测试用例执行记录优化功能文档

## 一、功能概述

本次更新是对测试用例模块的重大优化，参考测试环境模块的优化经验，重点增强测试用例执行过程的详细信息记录和管理功能，为后续支持测试用例串联执行做好准备。

## 二、需求背景

### 2.1 当前问题
1. **执行信息不够详细**：测试用例执行时只记录基本的请求和响应信息，缺少详细的执行过程记录
2. **无历史执行记录**：每次执行后无法查看历史执行记录，无法对比不同时间的执行结果
3. **缺少调试信息**：当测试失败时，缺少足够的调试信息来定位问题
4. **无变量传递机制**：当前是单接口测试，缺少变量传递和响应数据提取机制，无法支持串联测试场景

### 2.2 优化目标
1. 增强执行信息记录，提供完整的请求/响应详情
2. 新建执行记录表，持久化存储每次执行信息
3. 支持按日期、状态筛选和删除执行记录
4. 预留变量传递和响应数据提取接口

## 三、参考优化点（来自测试环境模块）

### 3.1 已实现的测试环境优化
1. **统计卡片**：总数、启用、禁用、默认、收藏
2. **配置预览弹窗**：点击全局参数图标弹出预览和编辑
3. **连接测试详情**：完整的请求头、响应头、响应体、错误详情
4. **收藏功能**：快速访问常用环境
5. **批量操作**：批量启用/禁用/导出
6. **统计数据弹窗**：点击卡片显示对应数据并支持CRUD
7. **导入/导出**：JSON格式导入导出
8. **搜索筛选**：名称模糊搜索

### 3.2 应用到测试用例执行记录
- 执行记录统计卡片（总数、成功、失败、跳过、错误）
- 执行详情弹窗（完整的请求/响应信息）
- 收藏执行记录（标记重要的执行记录）
- 批量删除（按日期/状态批量删除）
- 执行历史弹窗（查看某个测试用例的历史执行记录）
- 导出执行记录（JSON/CSV/Excel格式）

## 四、数据库设计

### 4.1 新建表：api_http_execution_records

用于存储每次HTTP请求执行的完整信息：

```python
class ApiHttpExecutionRecord(models.Model):
    """
    HTTP接口执行记录表
    记录每次HTTP请求的完整执行信息，支持调试和历史查询
    """
    # 关联信息
    test_case = models.ForeignKey(
        'ApiTestCase',
        on_delete=models.CASCADE,
        related_name='execution_records',
        verbose_name='测试用例',
        null=True,
        blank=True
    )
    execution = models.ForeignKey(
        'ApiTestExecution',
        on_delete=models.CASCADE,
        related_name='http_records',
        verbose_name='执行批次',
        null=True,
        blank=True
    )
    project = models.ForeignKey(
        'ApiProject',
        on_delete=models.CASCADE,
        related_name='http_execution_records',
        verbose_name='所属项目'
    )

    # 请求信息
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_url = models.TextField(verbose_name='完整请求URL')
    request_base_url = models.TextField(verbose_name='基础URL')
    request_path = models.TextField(verbose_name='请求路径')
    request_headers = JSONField(default=dict, verbose_name='请求头')
    request_params = JSONField(default=dict, verbose_name='Query参数')
    request_body = JSONField(default=dict, verbose_name='请求体')
    request_body_type = models.CharField(
        max_length=20,
        choices=[('JSON', 'JSON'), ('FORM', '表单'), ('RAW', '原始'), ('NONE', '无')],
        default='NONE',
        verbose_name='请求体类型'
    )
    request_size = models.IntegerField(null=True, blank=True, verbose_name='请求大小(bytes)')

    # 响应信息
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_status_text = models.CharField(max_length=100, blank=True, null=True, verbose_name='响应状态文本')
    response_headers = JSONField(default=dict, verbose_name='响应头')
    response_body = JSONField(default=dict, verbose_name='响应体')
    response_body_text = models.TextField(blank=True, null=True, verbose_name='响应体原文(非JSON)')
    response_size = models.IntegerField(null=True, blank=True, verbose_name='响应大小(bytes)')
    response_encoding = models.CharField(max_length=50, blank=True, null=True, verbose_name='响应编码')

    # 时间信息
    request_time = models.DateTimeField(verbose_name='请求发送时间')
    response_time = models.DateTimeField(null=True, blank=True, verbose_name='响应接收时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='响应时间(ms)')

    # 执行状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('SUCCESS', '成功'),
            ('FAILED', '失败'),
            ('TIMEOUT', '超时'),
            ('ERROR', '错误'),
        ],
        default='ERROR',
        verbose_name='执行状态'
    )

    # 错误信息
    error_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='错误类型')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    stack_trace = models.TextField(blank=True, null=True, verbose_name='错误堆栈')

    # 断言结果
    assertion_results = JSONField(default=list, verbose_name='断言结果列表')
    assertions_passed = models.IntegerField(default=0, verbose_name='断言通过数')
    assertions_failed = models.IntegerField(default=0, verbose_name='断言失败数')

    # 数据提取结果（为串联测试用例预留）
    extraction_results = JSONField(default=dict, verbose_name='数据提取结果')
    extracted_variables = JSONField(default=dict, verbose_name='提取的变量')

    # 环境信息
    environment = models.ForeignKey(
        'ApiTestEnvironment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='http_records',
        verbose_name='执行环境'
    )
    environment_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='环境名称')

    # 执行信息
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='http_executions',
        verbose_name='执行者'
    )
    execution_source = models.CharField(
        max_length=20,
        choices=[
            ('MANUAL', '手动执行'),
            ('BATCH', '批量执行'),
            ('SCHEDULED', '定时执行'),
            ('API', 'API触发'),
        ],
        default='MANUAL',
        verbose_name='执行来源'
    )

    # 收藏标记
    is_favorite = models.BooleanField(default=False, verbose_name='是否收藏')

    # 时间戳
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'api_http_execution_records'
        verbose_name = 'HTTP接口执行记录'
        verbose_name_plural = 'HTTP接口执行记录'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['test_case', 'created_time'], name='record_case_time_idx'),
            models.Index(fields=['execution', 'created_time'], name='record_exec_time_idx'),
            models.Index(fields=['project', 'created_time'], name='record_project_time_idx'),
            models.Index(fields=['status', 'created_time'], name='record_status_time_idx'),
            models.Index(fields=['environment', 'created_time'], name='record_env_time_idx'),
            models.Index(fields=['is_favorite', 'created_time'], name='record_favorite_time_idx'),
            models.Index(fields=['executed_by', 'created_time'], name='record_user_time_idx'),
        ]

    def __str__(self):
        return f"{self.request_method} {self.request_url} - {self.status}"
```

### 4.2 修改现有表：api_test_cases

为支持变量传递，增加预留字段：

```python
# 在ApiTestCase模型中增加以下字段

# 变量输入（前置条件）
input_variables = JSONField(default=dict, verbose_name='输入变量定义')
# 格式示例：
# {
#   "user_id": {"type": "string", "value": "${extract.user_id}", "description": "用户ID"},
#   "token": {"type": "string", "value": "${global.token}", "description": "认证令牌"}
# }

# 变量输出（响应数据提取）
output_variables = JSONField(default=dict, verbose_name='输出变量定义')
# 格式示例：
# {
#   "user_id": {"path": "$.data.user.id", "description": "提取用户ID"},
#   "token": {"path": "$.data.token", "description": "提取认证令牌"}
# }
```

### 4.3 数据表关系图

```
ApiProject (项目)
    ├── ApiTestCase (测试用例)
    │   ├── input_variables (输入变量定义)
    │   ├── output_variables (输出变量定义)
    │   ├── ApiTestCaseAssertion (断言配置)
    │   ├── ApiTestCaseExtraction (数据提取配置)
    │   └── ApiHttpExecutionRecord (HTTP执行记录) [新增]
    │       ├── extraction_results (数据提取结果)
    │       └── extracted_variables (提取的变量)
    └── ApiTestExecution (执行批次)
        └── ApiHttpExecutionRecord (HTTP执行记录) [新增]
```

## 五、后端API设计

### 5.1 HTTP执行记录视图集 (ApiHttpExecutionRecordViewSet)

```python
class ApiHttpExecutionRecordViewSet(viewsets.ModelViewSet):
    """
    HTTP执行记录视图集
    """
    serializer_class = ApiHttpExecutionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'test_case', 'execution', 'project', 'environment',
        'status', 'execution_source', 'is_favorite'
    ]
    search_fields = ['request_url', 'request_method', 'error_message']
    ordering_fields = ['created_time', 'duration', 'response_status']
    ordering = ['-created_time']

    def get_queryset(self):
        """获取查询集，支持日期范围筛选"""
        user = self.request.user
        queryset = ApiHttpExecutionRecord.objects.filter(is_deleted=False)

        # 日期范围筛选
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_time__lte=end_date)

        # 权限控制
        if user.is_superuser:
            return queryset
        else:
            return queryset.filter(
                Q(project__owner=user) | Q(project__is_active=True)
            ).distinct()

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取执行记录统计信息
        """
        queryset = self.get_queryset()
        return Response({
            'total': queryset.count(),
            'success': queryset.filter(status='SUCCESS').count(),
            'failed': queryset.filter(status='FAILED').count(),
            'timeout': queryset.filter(status='TIMEOUT').count(),
            'error': queryset.filter(status='ERROR').count(),
            'favorite': queryset.filter(is_favorite=True).count(),
        })

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        批量删除执行记录
        """
        ids = request.data.get('ids', [])
        filters = request.data.get('filters', {})

        queryset = self.get_queryset()

        if ids:
            queryset = queryset.filter(id__in=ids)
        if filters:
            # 按条件删除
            status = filters.get('status')
            date_before = filters.get('date_before')
            if status:
                queryset = queryset.filter(status=status)
            if date_before:
                queryset = queryset.filter(created_time__lt=date_before)

        count = queryset.count()
        queryset.delete()
        return Response({'message': f'已删除 {count} 条执行记录'})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """切换收藏状态"""
        record = self.get_object()
        record.is_favorite = not record.is_favorite
        record.save()
        return Response({
            'message': '已收藏' if record.is_favorite else '已取消收藏',
            'is_favorite': record.is_favorite
        })

    @action(detail=False, methods=['get'])
    def by_test_case(self, request):
        """获取指定测试用例的执行历史"""
        test_case_id = request.query_params.get('test_case')
        limit = int(request.query_params.get('limit', 20))

        records = self.get_queryset().filter(test_case_id=test_case_id)[:limit]
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
```

### 5.2 URL配置

```python
# 在 api_automation/urls.py 中添加
router.register(r'http-execution-records', ApiHttpExecutionRecordViewSet, basename='http-execution-records')
```

### 5.3 序列化器

```python
class ApiHttpExecutionRecordSerializer(serializers.ModelSerializer):
    """HTTP执行记录序列化器"""

    project_name = serializers.CharField(source='project.name', read_only=True)
    test_case_name = serializers.CharField(source='test_case.name', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    executed_by_username = serializers.CharField(source='executed_by.username', read_only=True)

    # 计算字段
    request_size_formatted = serializers.SerializerMethodField()
    response_size_formatted = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ApiHttpExecutionRecord
        fields = [
            'id', 'test_case', 'test_case_name', 'execution', 'project', 'project_name',
            'request_method', 'request_url', 'request_base_url', 'request_path',
            'request_headers', 'request_params', 'request_body', 'request_body_type', 'request_size',
            'response_status', 'response_status_text', 'response_headers', 'response_body',
            'response_body_text', 'response_size', 'response_encoding',
            'request_time', 'response_time', 'duration',
            'status', 'error_type', 'error_message', 'stack_trace',
            'assertion_results', 'assertions_passed', 'assertions_failed',
            'extraction_results', 'extracted_variables',
            'environment', 'environment_name', 'executed_by', 'executed_by_username',
            'execution_source', 'is_favorite', 'created_time',
            'request_size_formatted', 'response_size_formatted', 'duration_formatted'
        ]

    def get_request_size_formatted(self, obj):
        """格式化请求大小"""
        if obj.request_size:
            return f"{obj.request_size} B"
        return '-'

    def get_response_size_formatted(self, obj):
        """格式化响应大小"""
        if obj.response_size:
            if obj.response_size < 1024:
                return f"{obj.response_size} B"
            elif obj.response_size < 1024 * 1024:
                return f"{obj.response_size / 1024:.2f} KB"
            else:
                return f"{obj.response_size / (1024 * 1024):.2f} MB"
        return '-'

    def get_duration_formatted(self, obj):
        """格式化响应时间"""
        if obj.duration:
            return f"{obj.duration} ms"
        return '-'
```

## 六、前端设计

### 6.1 新增页面/组件

#### 6.1.1 执行记录列表页面 (HttpExecutionRecordList.vue)

**路由**: `/http-execution-records`

**功能**:
- 统计卡片（总数、成功、失败、超时、错误、收藏）
- 筛选器（日期范围、测试用例、状态、执行来源、环境）
- 搜索框（URL、方法、错误信息）
- 记录列表（分页）
- 批量操作（批量删除、导出）

#### 6.1.2 执行记录详情弹窗组件 (HttpExecutionRecordDetail.vue)

**功能**:
- 请求信息展示（方法、URL、请求头、请求体、请求大小）
- 响应信息展示（状态码、响应头、响应体、响应大小）
- 时间信息（请求时间、响应时间、响应时长）
- 断言结果展示
- 错误信息展示
- 数据提取结果展示
- 操作按钮（收藏、导出、复制cURL、重新执行）

#### 6.1.3 测试用例执行历史弹窗 (TestCaseExecutionHistory.vue)

**功能**:
- 显示指定测试用例的历史执行记录
- 按时间倒序排列
- 点击查看详情
- 对比不同次的执行结果

### 6.2 修改现有页面

#### 6.2.1 测试用例列表页 (TestCaseList.vue)

**新增功能**:
- "执行历史"按钮（查看该用例的历史执行记录）
- "最近执行"列（显示最近一次执行状态和结果）

#### 6.2.2 测试用例执行器 (TestCaseRunner.vue)

**增强功能**:
- 执行完成后自动保存到执行记录表
- 显示更详细的执行信息
- 提供"查看详情"链接跳转到执行记录详情

### 6.3 API封装

```typescript
// VUE3/src/modules/api-automation/api/httpExecutionRecord.ts

export const httpExecutionRecordApi = {
  // 获取执行记录列表
  getRecords(params?: any) {
    return http.get<{ results: ApiHttpExecutionRecord[], count: number }>(
      `${API_URL}/http-execution-records/`,
      params
    )
  },

  // 获取单个执行记录
  getRecord(id: number) {
    return http.get<ApiHttpExecutionRecord>(`${API_URL}/http-execution-records/${id}/`)
  },

  // 获取统计信息
  getStatistics(params?: any) {
    return http.get(`${API_URL}/http-execution-records/statistics/`, params)
  },

  // 批量删除
  batchDelete(data: { ids?: number[], filters?: any }) {
    return http.post(`${API_URL}/http-execution-records/batch_delete/`, data)
  },

  // 切换收藏
  toggleFavorite(id: number) {
    return http.post(`${API_URL}/http-execution-records/${id}/toggle_favorite/`)
  },

  // 获取测试用例的执行历史
  getByTestCase(testCaseId: number, limit?: number) {
    return http.get(`${API_URL}/http-execution-records/by_test_case/`, {
      test_case: testCaseId,
      limit: limit || 20
    })
  },

  // 导出执行记录
  exportRecords(format: 'json' | 'csv' | 'excel', ids?: number[]) {
    return http.post(`${API_URL}/http-execution-records/export/`, { format, ids })
  }
}
```

### 6.4 类型定义

```typescript
// VUE3/src/modules/api-automation/types/httpExecutionRecord.ts

export interface ApiHttpExecutionRecord {
  id: number
  test_case: number
  test_case_name: string
  execution?: number
  project: number
  project_name: string

  // 请求信息
  request_method: string
  request_url: string
  request_base_url: string
  request_path: string
  request_headers: Record<string, any>
  request_params: Record<string, any>
  request_body: any
  request_body_type: 'JSON' | 'FORM' | 'RAW' | 'NONE'
  request_size: number

  // 响应信息
  response_status: number
  response_status_text?: string
  response_headers: Record<string, any>
  response_body: any
  response_body_text?: string
  response_size: number
  response_encoding?: string

  // 时间信息
  request_time: string
  response_time?: string
  duration: number

  // 执行状态
  status: 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'ERROR'

  // 错误信息
  error_type?: string
  error_message?: string
  stack_trace?: string

  // 断言结果
  assertion_results: AssertionResult[]
  assertions_passed: number
  assertions_failed: number

  // 数据提取（为串联测试用例预留）
  extraction_results: Record<string, any>
  extracted_variables: Record<string, any>

  // 环境信息
  environment?: number
  environment_name?: string

  // 执行信息
  executed_by?: number
  executed_by_username?: string
  execution_source: 'MANUAL' | 'BATCH' | 'SCHEDULED' | 'API'

  // 收藏
  is_favorite: boolean

  // 时间戳
  created_time: string

  // 格式化字段
  request_size_formatted?: string
  response_size_formatted?: string
  duration_formatted?: string
}

export interface AssertionResult {
  assertion_id: number
  assertion_type: string
  expected: any
  actual: any
  passed: boolean
  error_message?: string
}
```

## 七、变量传递和数据提取（预留接口）

### 7.1 输入变量定义

在测试用例中定义输入变量：

```json
{
  "input_variables": {
    "user_id": {
      "type": "string",
      "value": "${extract.user_id}",
      "description": "从前置用例提取的用户ID",
      "required": true
    },
    "base_url": {
      "type": "string",
      "value": "${env.base_url}",
      "description": "环境基础URL",
      "required": false
    }
  }
}
```

### 7.2 输出变量定义

在测试用例中定义输出变量：

```json
{
  "output_variables": {
    "user_id": {
      "path": "$.data.user.id",
      "description": "提取用户ID",
      "variable_type": "string"
    },
    "auth_token": {
      "path": "$.data.token",
      "description": "提取认证令牌",
      "variable_type": "string"
    }
  }
}
```

### 7.3 数据提取存储格式

执行记录中存储提取的数据：

```json
{
  "extraction_results": {
    "user_id": {
      "path": "$.data.user.id",
      "value": 12345,
      "type": "number"
    },
    "auth_token": {
      "path": "$.data.token",
      "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "type": "string"
    }
  },
  "extracted_variables": {
    "extract.user_id": 12345,
    "extract.token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 7.4 变量引用规则

支持的变量引用格式：
- `${env.base_url}` - 环境变量
- `${global.token}` - 全局变量
- `${extract.user_id}` - 从前置用例提取的变量
- `${local.timestamp}` - 本地/当前用例定义的变量

## 八、开发步骤

### 阶段一：数据库和后端API
1. 创建数据库模型和迁移
2. 实现ViewSet和序列化器
3. 配置URL路由
4. 编写单元测试

### 阶段二：HTTP执行器增强
1. 修改HTTP执行器，记录完整执行信息
2. 实现数据提取逻辑
3. 保存执行记录到数据库

### 阶段三：前端界面
1. 创建执行记录列表页面
2. 创建执行记录详情弹窗
3. 修改测试用例列表，增加执行历史入口
4. 实现筛选、搜索、批量操作功能

### 阶段四：集成和测试
1. 集成前后端功能
2. 执行完整的测试验证
3. 性能优化
4. 文档完善

## 九、注意事项

### 9.1 性能考虑
1. 执行记录表会快速增长，需要考虑定期清理策略
2. 大型响应体可能影响查询性能，考虑分页和索引优化
3. 对于大量历史记录，可考虑归档到历史表

### 9.2 存储优化
1. 响应体大小限制（如最大1MB）
2. 定期清理旧记录（如保留最近90天）
3. 提供归档功能

### 9.3 扩展性设计
1. 预留变量传递接口，为串联测试用例做准备
2. 数据提取结果存储格式要支持后续扩展
3. 支持自定义字段和元数据

### 9.4 安全考虑
1. 执行记录可能包含敏感信息，需要权限控制
2. 支持数据脱敏功能
3. 审计日志记录删除操作

## 十、后续扩展

### 10.1 串联测试用例支持
基于本次优化的变量传递机制，后续可以实现：
1. 测试用例编排（定义用例执行顺序）
2. 变量传递链（前置用例的输出作为后续用例的输入）
3. 条件执行（根据前置结果决定是否执行后续用例）
4. 并行执行（独立的用例分支并行执行）

### 10.2 测试报告增强
1. 基于执行记录生成更详细的测试报告
2. 执行趋势分析（性能、成功率变化）
3. 失败原因分析统计
4. 自动化测试看板

### 10.3 调试功能增强
1. 支持重放历史请求
2. 支持修改参数后重新执行
3. 请求/响应对比工具
4. cURL命令自动生成

## 十一、总结

本次优化是测试用例模块的重大更新，主要完成：
1. ✅ 新建HTTP执行记录表，完整记录每次请求
2. ✅ 增强执行信息详细程度，便于调试
3. ✅ 支持按日期、状态筛选和删除执行记录
4. ✅ 预留变量传递和数据提取接口，为串联测试用例做准备
5. ✅ 参考测试环境模块的优化，提升用户体验

这次优化为后续实现串联测试用例、自动化测试编排等高级功能打下了坚实基础。
