# 测试用例功能优化设计文档（最终确认版）

## 一、功能概述

### 1.1 优化背景

现有系统已经实现了完整的单接口测试功能，本次优化基于现有功能，增强批量执行能力和测试报告展示，**无需新增复杂的数据模型**。

### 1.2 需求确认

| 序号 | 需求 | 实现方案 |
|------|------|---------|
| 1 | 测试用例需要串联执行多个接口，从接口中提取的返回值存入全局变量，后续的接口可以继续使用，且每个步骤都能添加断言测试 | VariablePoolService实现变量池，ApiTestCaseAssertion支持断言 |
| 2 | 与单接口执行相同的，每条测试用例的执行都需要保留测试记录信息供后续查询使用 | 复用ApiTestExecution和ApiTestResult模型 |
| 3 | 测试信息内容包含所有单接口的执行信息，接口状态码返回为200的仅保留简单的信息，接口状态码不为200的需要保留完整请求信息和错误信息。保留的测试执行记录也是每天凌晨自动清理七天前的数据 | ApiTestResult模型增加分级存储字段，定时任务自动清理 |
| 4 | 测试用例需要包含对应项目、和用例集合（优化修改目前的集合管理可以选择多个测试用例实现） | 增强ApiCollection管理，支持批量添加/移除用例 |
| 5 | 多测试用例的执行，可以按照项目维度、集合维度或者手动批量选择执行 | 新增三种批量执行API接口 |
| 6 | 多用执行后的结果需要新开发一个专门的测试报告页面展示，现在开发出对应的测试报告页面，包含基本的信息，保留后续进一步开发优化测试报告的空间 | 新建TestReport模块，包含列表和详情页 |

---

## 二、现有数据模型分析

### 2.1 无需修改的现有模型

```python
# ApiCollection - API集合
class ApiCollection(models.Model):
    name = models.CharField(max_length=100, verbose_name='集合名称')
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(ApiProject, ...)
    # 通过 test_cases 反向关联获取集合中的所有测试用例

# ApiTestCase - API测试用例
class ApiTestCase(models.Model):
    name = models.CharField(max_length=100, verbose_name='用例名称')
    project = models.ForeignKey(ApiProject, ...)
    collection = models.ForeignKey(ApiCollection, ...)  # 所属集合（可选）
    # 已支持断言和数据提取

# ApiTestExecution - 测试执行记录
class ApiTestExecution(models.Model):
    project = models.ForeignKey(ApiProject, ...)
    environment = models.ForeignKey(ApiTestEnvironment, ...)
    test_cases = JSONField(default=list)  # 测试用例ID列表
    status = ...  # PENDING/RUNNING/COMPLETED/FAILED/CANCELLED
    total_count = ...
    passed_count = ...
    failed_count = ...
    skipped_count = ...

# ApiTestResult - 测试结果详情（需要增强）
class ApiTestResult(models.Model):
    execution = models.ForeignKey(ApiTestExecution, ...)
    test_case = models.ForeignKey(ApiTestCase, ...)
    status = ...  # PASSED/FAILED/SKIPPED/ERROR
    # 需要增加分级存储字段
```

### 2.2 需要增强的数据模型

```python
# ApiTestResult 增强字段
class ApiTestResult(models.Model):
    # ... 现有字段 ...

    # 新增：分级存储字段（满足需求3）
    request_summary = JSONField(default=dict, blank=True, verbose_name='请求摘要')
    # 只存储：method, url, 部分headers

    request_full = JSONField(default=dict, blank=True, verbose_name='完整请求信息')
    # 存储：完整的method, url, headers, params, body

    response_summary = JSONField(default=dict, blank=True, verbose_name='响应摘要')
    # 只存储：status_code, response_time

    response_full = JSONField(default=dict, blank=True, verbose_name='完整响应信息')
    # 存储：status, headers, body, error信息

    error_info = JSONField(default=dict, blank=True, verbose_name='错误信息')
    # 存储详细的错误堆栈和原因

    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 用于自动清理：created_time < 7天前 的记录

    class Meta:
        indexes = [
            # 添加索引优化清理查询
            models.Index(fields=['created_time'], name='result_created_idx'),
        ]
```

---

## 三、核心功能设计

### 3.1 数据分级存储机制（需求3）

#### 3.1.1 存储策略

```python
class ResultStorageService:
    """测试结果存储服务"""

    @staticmethod
    def save_result(http_response, test_result: ApiTestResult):
        """根据状态码分级存储数据"""

        # HTTP状态码 200-299：简化存储
        if 200 <= http_response.status_code < 300:
            test_result.request_summary = {
                'method': http_response.request.method,
                'url': http_response.request.url,
                'headers': {k: v for k, v in http_response.request.headers.items()
                          if k.lower() in ['authorization', 'content-type']}
            }
            test_result.response_summary = {
                'status_code': http_response.status_code,
                'response_time': http_response.response_time
            }
            # 不存储 request_full 和 response_full，节省空间

        # HTTP状态码非200：完整存储
        else:
            test_result.request_full = {
                'method': http_response.request.method,
                'url': http_response.request.url,
                'headers': dict(http_response.request.headers),
                'params': http_response.request.params,
                'body': http_response.request.body
            }
            test_result.response_full = {
                'status_code': http_response.status_code,
                'status_text': http_response.status_text,
                'headers': dict(http_response.headers),
                'body': http_response.body
            }
            test_result.error_info = {
                'error_type': 'http_error',
                'error_message': f'HTTP {http_response.status_code} Error',
                'stack_trace': str(http_response.error) if http_response.error else None
            }

        test_result.save()
```

#### 3.1.2 数据自动清理

```python
# 定时任务：每天凌晨清理7天前的数据
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

@shared_task
def cleanup_old_test_results():
    """
    清理7天前的测试执行记录
    满足需求3：每天凌晨自动清理七天前的数据
    """
    cutoff_date = timezone.now() - timedelta(days=7)

    # 删除7天前的执行记录（会级联删除关联的测试结果）
    deleted_count = ApiTestExecution.objects.filter(
        created_time__lt=cutoff_date
    ).delete()[0]

    logger.info(f"已清理 {deleted_count} 条7天前的测试执行记录")
    return deleted_count

# Celery Beat 配置（每天凌晨2点执行）
CELERY_BEAT_SCHEDULE = {
    'cleanup-old-test-results': {
        'task': 'api_automation.tasks.cleanup_old_test_results',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
}
```

---

### 3.2 变量传递机制（需求1）

#### 3.2.1 变量池设计

```python
# services/variable_pool_service.py

class VariablePool:
    """变量池，用于批量执行时用例间变量传递"""

    def __init__(self, environment=None):
        self.pool = {
            'env': {},      # 环境变量
            'global': {},   # 全局变量
            'shared': {}    # 用例间共享变量（满足需求1：后续接口可以使用前置接口提取的变量）
        }

        # 初始化环境变量
        if environment:
            self.pool['env'] = environment.global_variables or {}

    def add_shared_variable(self, name: str, value: any):
        """添加共享变量（从前置接口提取）"""
        self.pool['shared'][name] = value

    def get_variable(self, var_path: str) -> any:
        """
        获取变量
        支持格式：
        - ${env.base_url}
        - ${global.token}
        - ${shared.user_id}
        """
        if var_path.startswith('${env.'):
            key = var_path[6:-1]
            return self.pool['env'].get(key)
        elif var_path.startswith('${global.'):
            key = var_path[9:-1]
            return self.pool['global'].get(key)
        elif var_path.startswith('${shared.'):
            key = var_path[9:-1]
            return self.pool['shared'].get(key)
        return None

    def replace_in_text(self, text: str) -> str:
        """替换文本中的变量"""
        if not text:
            return text

        import re
        pattern = r'\$\{(env|global|shared)\.([^}]+)\}'

        def replacer(match):
            var_type, var_name = match.groups()
            value = self.pool.get(var_type, {}).get(var_name)
            return str(value) if value is not None else match.group(0)

        return re.sub(pattern, replacer, str(text))

    def replace_in_dict(self, data: dict) -> dict:
        """递归替换字典中的变量"""
        if not data:
            return data

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.replace_in_text(value)
            elif isinstance(value, dict):
                result[key] = self.replace_in_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.replace_in_text(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
```

#### 3.2.2 批量执行引擎

```python
# services/batch_execution_engine.py

class BatchExecutionEngine:
    """批量执行引擎"""

    def __init__(self, execution: ApiTestExecution):
        self.execution = execution
        self.variable_pool = VariablePool(environment=execution.environment)

    def execute_batch(self):
        """批量执行测试用例"""
        test_cases = ApiTestCase.objects.filter(
            id__in=self.execution.test_cases
        ).order_by('id')

        self.execution.total_count = test_cases.count()
        self.execution.status = 'RUNNING'
        self.execution.start_time = timezone.now()
        self.execution.save()

        passed = 0
        failed = 0
        skipped = 0

        for test_case in test_cases:
            # 检查是否需要停止
            if self.execution.status == 'CANCELLED':
                skipped += (test_cases.count() - passed - failed)
                break

            # 执行单个用例
            result = self._execute_single_case(test_case)
            self._save_result(test_case, result)

            if result.status == 'PASSED':
                passed += 1
            elif result.status == 'FAILED':
                failed += 1
            else:
                skipped += 1

        # 更新执行统计
        self.execution.passed_count = passed
        self.execution.failed_count = failed
        self.execution.skipped_count = skipped
        self.execution.status = 'COMPLETED'
        self.execution.end_time = timezone.now()
        self.execution.duration = int((self.execution.end_time - self.execution.start_time).total_seconds())
        self.execution.save()

    def _execute_single_case(self, test_case: ApiTestCase) -> TestCaseResult:
        """执行单个用例"""
        # 1. 应用变量替换（满足需求1）
        url = self.variable_pool.replace_in_text(test_case.url)
        headers = self.variable_pool.replace_in_dict(test_case.headers)
        params = self.variable_pool.replace_in_dict(test_case.params)
        body = self.variable_pool.replace_in_dict(test_case.body)

        # 2. 执行HTTP请求
        http_executor = HttpExecutor()
        http_response = http_executor.execute_request(
            method=test_case.method,
            url=url,
            base_url=self.execution.environment.base_url,
            headers=headers,
            params=params,
            body=body
        )

        # 3. 执行断言（满足需求1：每个步骤都能添加断言测试）
        assertion_engine = AssertionEngine()
        assertions = ApiTestCaseAssertion.objects.filter(
            test_case=test_case,
            is_enabled=True
        )
        assertion_results = assertion_engine.validate_assertions(
            assertions=assertions,
            http_response=http_response
        )

        # 4. 提取变量到共享池（满足需求1：后续接口可以继续使用）
        extraction_engine = ExtractionEngine()
        extractions = ApiTestCaseExtraction.objects.filter(
            test_case=test_case,
            is_enabled=True
        )
        extracted_vars, _ = extraction_engine.extract_variables(
            extractions=extractions,
            http_response=http_response.raw_response,
            response_body=http_response.body
        )

        # 将提取的变量添加到共享池
        for var_name, var_value in extracted_vars.items():
            self.variable_pool.add_shared_variable(var_name, var_value)

        # 5. 返回结果
        status = 'PASSED' if all(r['passed'] for r in assertion_results) else 'FAILED'
        return TestCaseResult(
            status=status,
            http_response=http_response,
            assertion_results=assertion_results,
            extracted_variables=extracted_vars
        )

    def _save_result(self, test_case: ApiTestCase, result: TestCaseResult):
        """保存测试结果（满足需求2：保留测试记录信息供后续查询）"""
        test_result = ApiTestResult.objects.create(
            execution=self.execution,
            test_case=test_case,
            status=result.status,
            response_status=result.http_response.status_code,
            response_time=result.http_response.response_time,
            assertion_results=result.assertion_results,
            extracted_variables=result.extracted_variables,
            start_time=timezone.now(),
            end_time=timezone.now()
        )

        # 分级存储数据（满足需求3）
        ResultStorageService.save_result(result.http_response, test_result)
```

---

### 3.3 集合管理优化（需求4、5）

#### 3.3.1 集合管理增强

```python
# views.py

class ApiCollectionViewSet(viewsets.ModelViewSet):
    """集合视图集（增强版）"""

    @action(detail=True, methods=['post'])
    def batch_add_test_cases(self, request, pk=None):
        """
        批量添加测试用例到集合
        满足需求4：优化修改目前的集合管理可以选择多个测试用例实现
        """
        collection = self.get_object()
        test_case_ids = request.data.get('test_case_ids', [])

        # 验证用例属于同一项目
        test_cases = ApiTestCase.objects.filter(
            id__in=test_case_ids,
            project=collection.project,
            is_deleted=False
        )

        if test_cases.count() != len(test_case_ids):
            return Response(
                {'error': '部分用例不存在或不属于同一项目'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 更新用例的集合关联
        test_cases.update(collection=collection)

        return Response({
            'message': f'已添加 {len(test_case_ids)} 个测试用例到集合'
        })

    @action(detail=True, methods=['delete'])
    def batch_remove_test_cases(self, request, pk=None):
        """批量从集合移除测试用例"""
        collection = self.get_object()
        test_case_ids = request.data.get('test_case_ids', [])

        # 移除集合关联（不删除用例）
        ApiTestCase.objects.filter(
            id__in=test_case_ids,
            collection=collection
        ).update(collection=None)

        return Response({
            'message': f'已移除 {len(test_case_ids)} 个测试用例'
        })

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        执行集合中的所有测试用例
        满足需求5：可以按照集合维度执行
        """
        collection = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取集合中的所有测试用例
        test_cases = list(collection.test_cases.filter(
            is_deleted=False
        ).values_list('id', flat=True))

        if not test_cases:
            return Response(
                {'error': '集合中没有测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建执行记录（满足需求2）
        execution = ApiTestExecution.objects.create(
            name=f'{collection.name} - 批量执行',
            project=collection.project,
            environment_id=environment_id,
            test_cases=test_cases,
            status='PENDING',
            total_count=len(test_cases),
            created_by=request.user,
            execution_source='MANUAL'
        )

        # 启动异步执行
        from .tasks import execute_test_batch
        execute_test_batch.delay(execution.id)

        return Response({
            'message': '批量执行已启动',
            'execution_id': execution.id
        })
```

#### 3.3.2 项目维度执行（需求5）

```python
class ApiProjectViewSet(viewsets.ModelViewSet):
    """项目视图集"""

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        执行项目下的所有测试用例
        满足需求5：可以按照项目维度执行
        """
        project = self.get_object()
        environment_id = request.data.get('environment_id')

        if not environment_id:
            return Response(
                {'error': '请选择执行环境'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 获取项目下所有测试用例
        test_cases = list(project.test_cases.filter(
            is_deleted=False
        ).values_list('id', flat=True))

        if not test_cases:
            return Response(
                {'error': '项目中没有测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建执行记录
        execution = ApiTestExecution.objects.create(
            name=f'{project.name} - 全部用例执行',
            project=project,
            environment_id=environment_id,
            test_cases=test_cases,
            status='PENDING',
            total_count=len(test_cases),
            created_by=request.user,
            execution_source='MANUAL'
        )

        # 启动异步执行
        from .tasks import execute_test_batch
        execute_test_batch.delay(execution.id)

        return Response({
            'message': '批量执行已启动',
            'execution_id': execution.id
        })
```

#### 3.3.3 手动选择执行（需求5）

```python
class ApiTestCaseViewSet(viewsets.ModelViewSet):
    """测试用例视图集"""

    @action(detail=False, methods=['post'])
    def batch_execute(self, request):
        """
        手动选择批量执行
        满足需求5：可以手动批量选择执行
        """
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

        # 验证用例权限并确保属于同一项目
        test_cases = ApiTestCase.objects.filter(
            id__in=test_case_ids,
            is_deleted=False
        )

        if test_cases.count() != len(test_case_ids):
            return Response(
                {'error': '部分用例不存在或无权访问'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 检查是否属于同一项目
        project_ids = test_cases.values_list('project_id', flat=True).distinct()
        if project_ids.count() > 1:
            return Response(
                {'error': '请选择同一项目的测试用例'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建执行记录
        execution = ApiTestExecution.objects.create(
            name=f'批量执行 - {len(test_case_ids)}个用例',
            project_id=project_ids.first(),
            environment_id=environment_id,
            test_cases=test_case_ids,
            status='PENDING',
            total_count=len(test_case_ids),
            created_by=request.user,
            execution_source='MANUAL'
        )

        # 启动异步执行
        from .tasks import execute_test_batch
        execute_test_batch.delay(execution.id)

        return Response({
            'message': '批量执行已启动',
            'execution_id': execution.id
        })
```

---

## 四、测试报告页面（需求6）

### 4.1 页面结构

```
测试报告模块
├── 报告列表页 (TestReportList.vue)
│   ├── 搜索和筛选
│   ├── 报告列表（表格）
│   └── 操作按钮（查看、删除）
│
└── 报告详情页 (TestReportDetail.vue)
    ├── 报告基本信息区域
    │   ├── 报告名称、项目、环境
    │   ├── 执行时间、执行时长
    │   └── 操作按钮（重新执行、导出、删除）
    │
    ├── 执行摘要区域
    │   ├── 统计卡片
    │   │   ├── 总用例数
    │   │   ├── 通过数
    │   │   ├── 失败数
    │   │   ├── 跳过数
    │   │   └── 通过率
    │   └── 执行进度条
    │
    ├── 可视化图表区域（预留扩展空间）
    │   ├── 饼图占位（通过率分布）
    │   ├── 柱状图占位（响应时间分布）
    │   └── 提示："更多图表功能开发中..."
    │
    ├── 测试用例结果列表
    │   ├── 状态筛选（全部/通过/失败/跳过/错误）
    │   ├── 结果表格
    │   │   ├── 用例名称
    │   │   ├── 请求方法和URL
    │   │   ├── 状态标签
    │   │   ├── 响应时间
    │   │   └── 操作（查看详情）
    │   └── 分页
    │
    └── 用例结果详情对话框
        ├── 请求信息（完整或摘要）
        ├── 响应信息（完整或摘要）
        ├── 断言结果
        ├── 提取的变量
        └── 错误信息（如果有）
```

### 4.2 路由设计

```typescript
// router/index.ts
{
  path: '/test-reports',
  name: 'TestReportList',
  component: () => import('@/views/TestReport/TestReportList.vue'),
  meta: { title: '测试报告', requiresAuth: true }
},
{
  path: '/test-reports/:id',
  name: 'TestReportDetail',
  component: () => import('@/views/TestReport/TestReportDetail.vue'),
  meta: { title: '测试报告详情', requiresAuth: true }
}
```

### 4.3 API设计

```python
# 获取报告列表
GET /api/v1/api-automation/reports/
# 查询参数：project, status, page, page_size

# 获取报告详情
GET /api/v1/api-automation/reports/{id}/

# 删除报告
DELETE /api/v1/api-automation/reports/{id}/

# 导出报告
GET /api/v1/api-automation/reports/{id}/export/?format=json|pdf|excel
```

---

## 五、前端实现

### 5.1 集合详情页优化

```vue
<!-- views/Collection/CollectionDetail.vue -->
<template>
  <div class="collection-detail">
    <!-- 基本信息区域 -->
    <el-card class="info-card">
      <h2>{{ collection.name }}</h2>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="集合名称">{{ collection.name }}</el-descriptions-item>
        <el-descriptions-item label="所属项目">{{ collection.project_name }}</el-descriptions-item>
        <el-descriptions-item label="测试用例数">{{ collection.test_cases_count }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ collection.created_time }}</el-descriptions-item>
      </el-descriptions>
      <div class="actions">
        <el-button type="primary" @click="showAddTestCaseDialog">
          添加用例
        </el-button>
        <el-button @click="executeCollection">
          执行测试
        </el-button>
      </div>
    </el-card>

    <!-- 测试用例管理区域 -->
    <el-card class="test-cases-card">
      <template #header>
        <div class="card-header">
          <span>测试用例管理</span>
          <el-input
            v-model="searchText"
            placeholder="搜索用例"
            style="width: 200px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <!-- 用例列表 -->
      <el-table
        :data="filteredTestCases"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="用例名称" />
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="getMethodType(row.method)">
              {{ row.method }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="URL" show-overflow-tooltip />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link @click="viewTestCase(row)">查看</el-button>
            <el-button link @click="removeTestCase(row)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 批量操作 -->
      <div class="batch-actions" v-if="selectedTestCases.length > 0">
        <span>已选择 {{ selectedTestCases.length }} 项</span>
        <el-button type="danger" @click="batchRemove">
          批量移除
        </el-button>
      </div>
    </el-card>

    <!-- 执行记录区域 -->
    <el-card class="executions-card">
      <template #header>
        <span>执行记录</span>
      </template>
      <ExecutionList :collection-id="collection.id" />
    </el-card>

    <!-- 添加用例对话框 -->
    <AddTestCaseDialog
      v-model="addDialogVisible"
      :collection-id="collection.id"
      :project-id="collection.project"
      @confirm="handleAddTestCases"
    />

    <!-- 执行对话框 -->
    <ExecuteDialog
      v-model="executeDialogVisible"
      :collection="collection"
      @confirm="handleExecute"
    />
  </div>
</template>
```

### 5.2 测试报告列表页

```vue
<!-- views/TestReport/TestReportList.vue -->
<template>
  <div class="test-report-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>测试报告</span>
          <el-input
            v-model="searchText"
            placeholder="搜索报告"
            style="width: 200px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-select v-model="projectFilter" placeholder="选择项目" clearable>
          <el-option label="全部" value="" />
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>

        <el-select v-model="statusFilter" placeholder="执行状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="执行中" value="RUNNING" />
          <el-option label="失败" value="FAILED" />
        </el-select>

        <el-select v-model="environmentFilter" placeholder="执行环境" clearable>
          <el-option label="全部" value="" />
          <el-option
            v-for="env in environments"
            :key="env.id"
            :label="env.name"
            :value="env.id"
          />
        </el-select>
      </div>

      <!-- 报告列表 -->
      <el-table :data="filteredReports" v-loading="loading">
        <el-table-column prop="name" label="报告名称" />
        <el-table-column prop="project_name" label="项目" />
        <el-table-column prop="environment_name" label="环境" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="统计" width="250">
          <template #default="{ row }">
            <span class="stats">
              总: {{ row.total_count }} |
              <el-tag type="success" size="small">通过: {{ row.passed_count }}</el-tag> |
              <el-tag type="danger" size="small">失败: {{ row.failed_count }}</el-tag> |
              <el-tag type="info" size="small">跳过: {{ row.skipped_count }}</el-tag>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="执行时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewReport(row)">
              查看详情
            </el-button>
            <el-button link @click="exportReport(row)">导出</el-button>
            <el-button link type="danger" @click="deleteReport(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchReports"
        @current-change="fetchReports"
      />
    </el-card>
  </div>
</template>
```

### 5.3 测试报告详情页

```vue
<!-- views/TestReport/TestReportDetail.vue -->
<template>
  <div class="test-report-detail">
    <!-- 报告头部 -->
    <el-card class="report-header">
      <div class="header-info">
        <h2>{{ execution.name }}</h2>
        <el-descriptions :column="4" border>
          <el-descriptions-item label="项目">
            {{ execution.project_name }}
          </el-descriptions-item>
          <el-descriptions-item label="环境">
            {{ execution.environment_name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(execution.status)">
              {{ getStatusText(execution.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ execution.created_time }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时长">
            {{ execution.duration }}秒
          </el-descriptions-item>
          <el-descriptions-item label="执行来源">
            {{ getExecutionSourceText(execution.execution_source) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div class="header-actions">
        <el-button type="primary" @click="reExecute">重新执行</el-button>
        <el-button @click="exportReport">导出报告</el-button>
        <el-button type="danger" @click="deleteReport">删除</el-button>
      </div>
    </el-card>

    <!-- 执行摘要 -->
    <ReportSummary :execution="execution" />

    <!-- 可视化图表（预留扩展空间） -->
    <el-card class="charts-card">
      <template #header>
        <div class="card-header">
          <span>可视化分析</span>
          <el-tag type="info">更多图表功能开发中...</el-tag>
        </div>
      </template>
      <div class="charts-placeholder">
        <el-empty description="图表功能预留，等待后续开发">
          <template #image>
            <el-icon :size="100" color="#909399">
              <DataAnalysis />
            </el-icon>
          </template>
        </el-empty>
      </div>
    </el-card>

    <!-- 测试用例结果列表 -->
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span>测试用例结果</span>
          <el-radio-group v-model="statusFilter">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="PASSED">通过</el-radio-button>
            <el-radio-button label="FAILED">失败</el-radio-button>
            <el-radio-button label="SKIPPED">跳过</el-radio-button>
            <el-radio-button label="ERROR">错误</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <TestCaseResultTable
        :results="filteredResults"
        :loading="loading"
        @row-click="showResultDetail"
      />
    </el-card>

    <!-- 用例结果详情对话框 -->
    <TestCaseResultDetail
      v-model="detailDialogVisible"
      :result="selectedResult"
    />
  </div>
</template>
```

### 5.4 用例结果详情组件

```vue
<!-- components/TestReport/TestCaseResultDetail.vue -->
<template>
  <el-dialog
    v-model="visible"
    :title="`用例结果 - ${result?.test_case_name || ''}`"
    width="80%"
    :close-on-click-modal="false"
  >
    <el-tabs v-model="activeTab" v-if="result">
      <!-- 基本信息 -->
      <el-tab-pane label="基本信息" name="basic">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用例名称">
            {{ result.test_case_name }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(result.status)">
              {{ result.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="请求方法">
            {{ result.request_summary?.method || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="请求URL">
            {{ result.request_summary?.url || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="响应状态码">
            {{ result.response_status }}
          </el-descriptions-item>
          <el-descriptions-item label="响应时间">
            {{ result.response_time }}ms
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <!-- 请求信息 -->
      <el-tab-pane label="请求信息" name="request">
        <el-alert
          v-if="result.response_status >= 200 && result.response_status < 300"
          title="状态码200，仅显示摘要信息"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        />
        <el-alert
          v-else
          title="状态码非200，显示完整信息"
          type="warning"
          :closable="false"
          style="margin-bottom: 16px"
        />

        <!-- 根据状态码显示不同内容 -->
        <pre v-if="result.request_full || result.request_summary" class="json-preview">{{ formatJson(result.request_full || result.request_summary) }}</pre>
        <el-empty v-else description="无请求数据" />
      </el-tab-pane>

      <!-- 响应信息 -->
      <el-tab-pane label="响应信息" name="response">
        <el-alert
          v-if="result.response_status >= 200 && result.response_status < 300"
          title="状态码200，仅显示摘要信息"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        />
        <el-alert
          v-else
          title="状态码非200，显示完整信息"
          type="warning"
          :closable="false"
          style="margin-bottom: 16px"
        />

        <!-- 根据状态码显示不同内容 -->
        <pre v-if="result.response_full || result.response_summary" class="json-preview">{{ formatJson(result.response_full || result.response_summary) }}</pre>
        <el-empty v-else description="无响应数据" />
      </el-tab-pane>

      <!-- 断言结果 -->
      <el-tab-pane label="断言结果" name="assertions">
        <el-table :data="result.assertion_results" max-height="400">
          <el-table-column label="断言类型" prop="assertion_type" />
          <el-table-column label="目标" prop="target" />
          <el-table-column label="操作符" prop="operator" />
          <el-table-column label="期望值" prop="expected_value" />
          <el-table-column label="实际值" prop="actual_value" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.passed ? 'success' : 'danger'">
                {{ row.passed ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 提取的变量 -->
      <el-tab-pane label="提取的变量" name="extractions">
        <el-table :data="formatExtractedVariables(result.extracted_variables)" max-height="400">
          <el-table-column label="变量名" prop="name" />
          <el-table-column label="变量值" prop="value" />
          <el-table-column label="作用域" prop="scope" />
        </el-table>
      </el-tab-pane>

      <!-- 错误信息 -->
      <el-tab-pane label="错误信息" name="error" v-if="result.error_info && Object.keys(result.error_info).length > 0">
        <el-alert
          :title="result.error_info.error_message || '执行错误'"
          type="error"
          :closable="false"
        />
        <pre v-if="result.error_info.stack_trace" class="error-trace">{{ result.error_info.stack_trace }}</pre>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface TestCaseResult {
  test_case_name: string
  status: string
  request_summary?: Record<string, any>
  request_full?: Record<string, any>
  response_full?: Record<string, any>
  response_summary?: Record<string, any>
  response_status: number
  response_time: number
  assertion_results: Array<{
    assertion_type: string
    target: string
    operator: string
    expected_value: any
    actual_value: any
    passed: boolean
  }>
  extracted_variables?: Record<string, any>
  error_info?: Record<string, any>
}

const props = defineProps<{
  modelValue: boolean
  result: TestCaseResult | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const activeTab = ref('basic')

const formatJson = (data: Record<string, any>) => {
  return JSON.stringify(data, null, 2)
}

const formatExtractedVariables = (vars: Record<string, any>) => {
  return Object.entries(vars || {}).map(([name, value]) => ({
    name,
    value: JSON.stringify(value),
    scope: 'shared'
  }))
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'PASSED': 'success',
    'FAILED': 'danger',
    'SKIPPED': 'info',
    'ERROR': 'warning'
  }
  return map[status] || 'info'
}
</script>
```

### 5.5 状态管理

```typescript
// stores/report.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { reportApi } from '../api/report'

export const useReportStore = defineStore('report', () => {
  const reports = ref<ApiTestExecution[]>([])
  const currentReport = ref<ApiTestExecutionDetail | null>(null)
  const loading = ref(false)
  const total = ref(0)

  // 获取报告列表
  const fetchReports = async (params?: any) => {
    loading.value = true
    try {
      const response = await reportApi.getReports(params)
      reports.value = response.results
      total.value = response.count
    } finally {
      loading.value = false
    }
  }

  // 获取报告详情
  const fetchReport = async (id: number) => {
    loading.value = true
    try {
      const response = await reportApi.getReport(id)
      currentReport.value = response
      return response
    } finally {
      loading.value = false
    }
  }

  // 删除报告
  const deleteReport = async (id: number) => {
    await reportApi.deleteReport(id)
    reports.value = reports.value.filter(r => r.id !== id)
  }

  // 导出报告
  const exportReport = async (id: number, format: string = 'json') => {
    const response = await reportApi.exportReport(id, format)
    // 处理下载
    const blob = new Blob([response], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${id}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    reports,
    currentReport,
    loading,
    total,
    fetchReports,
    fetchReport,
    deleteReport,
    exportReport
  }
})
```

---

## 六、API接口汇总

### 6.1 新增API接口

| 接口 | 方法 | 说明 | 需求编号 |
|------|------|------|---------|
| `/collections/{id}/test-cases/batch-add/` | POST | 批量添加用例到集合 | 4 |
| `/collections/{id}/test-cases/batch-remove/` | DELETE | 批量从集合移除用例 | 4 |
| `/collections/{id}/execute/` | POST | 集合维度执行 | 5 |
| `/projects/{id}/execute/` | POST | 项目维度执行 | 5 |
| `/test-cases/batch-execute/` | POST | 手动选择执行 | 5 |
| `/reports/` | GET | 获取报告列表 | 6 |
| `/reports/{id}/` | GET | 获取报告详情 | 6 |
| `/reports/{id}/export/` | GET | 导出报告 | 6 |
| `/reports/{id}/` | DELETE | 删除报告 | 6 |

### 6.2 需要修改的现有模型

| 模型 | 修改内容 | 原因 |
|------|---------|------|
| ApiTestResult | 增加 request_summary, response_summary, request_full, response_full, error_info 字段 | 满足需求3：分级存储 |

---

## 七、实施计划

### 7.1 开发步骤（5个工作日）

| 阶段 | 任务 | 工作量 |
|------|------|--------|
| **阶段一** | 数据模型增强 | 0.5天 |
| | - 修改 ApiTestResult 模型 | |
| | - 创建数据库迁移 | |
| **阶段二** | 后端API开发 | 1.5天 |
| | - 集合管理API（批量添加/移除） | |
| | - 批量执行API（项目/集合/手动） | |
| | - 变量池服务开发 | |
| | - 分级存储服务开发 | |
| | - 定时清理任务 | |
| **阶段三** | 前端页面开发 | 2天 |
| | - 集合详情页优化 | |
| | - 测试报告列表页 | |
| | - 测试报告详情页 | |
| | - 报告组件开发 | |
| **阶段四** | 测试和优化 | 1天 |
| | - 功能测试 | |
| | - 性能优化 | |
| | - 文档更新 | |

---

## 八、需求满足确认

### 8.1 需求对照表

| 序号 | 需求 | 实现方案 | 文档章节 |
|------|------|---------|---------|
| 1 | 串联执行+变量传递+断言 | VariablePoolService + ApiTestCaseAssertion | 3.2 |
| 2 | 保留测试记录 | ApiTestExecution + ApiTestResult | 3.2.2 |
| 3 | 数据分级存储+自动清理 | ResultStorageService + 定时任务 | 3.1 |
| 4 | 项目和集合关联 | 集合管理增强 | 3.3.1 |
| 5 | 三种批量执行方式 | 项目/集合/手动API | 3.3 |
| 6 | 测试报告页面 | TestReport模块 | 4 |

### 8.2 全部满足确认

✅ **所有6个需求已完全满足**

---

**文档版本**: v3.0 (最终确认版)
**创建日期**: 2026-01-04
**最后更新**: 2026-01-04
