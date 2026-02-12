# Design: API自动化测试平台增强

## 架构概览

### 当前架构问题

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                         │
│  问题: 大组件(2089行)、无缓存、无虚拟滚动                     │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ API
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 (Django)                             │
│  问题: views.py(1963行)、无索引、N+1查询、无缓存             │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据库 (MySQL)                            │
│  问题: 缺少索引、无查询优化                                  │
└─────────────────────────────────────────────────────────────┘
```

### 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                  前端 (Vue 3)                                │
│  ✓ 小组件(<300行)  ✓ 虚拟滚动  ✓ 前端缓存  ✓ 代码分割       │
│  ✓ 离线支持        ✓ PWA能力   ✓ 性能监控                   │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ API + WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端 (Django)                              │
│  ✓ 模块化views(<500行/文件)  ✓ Redis缓存  ✓ 并发执行        │
│  ✓ 查询优化  ✓ 细粒度权限  ✓ 审计日志                        │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   数据层 (MySQL + Redis)                     │
│  ✓ 完整索引  ✓ 分区表  ✓ 读写分离准备                       │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   集成层                                      │
│  ✓ CLI工具  ✓ CI/CD集成  ✓ Webhook  ✓ Mock服务             │
└─────────────────────────────────────────────────────────────┘
```

## 技术决策

### 1. 测试执行引擎增强

#### 1.1 嵌套变量支持

**决策**：实现基于点号的嵌套变量访问

**技术选型**：
- 解析器：自定义递归下降解析器
- 变量语法：`${path.to.variable}`
- 默认值：`${path.to.variable|default}`

**实现方案**：
```python
class VariableResolver:
    def resolve(self, template: str, context: Dict) -> str:
        """
        支持嵌套变量解析
        ${user.profile.id} -> context['user']['profile']['id']
        """
        import re
        pattern = r'\$\{([^}|]+)(?:\|([^}]*))?\}'

        def replace_var(match):
            path = match.group(1)
            default = match.group(2)
            try:
                value = self._get_nested_value(context, path)
                return str(value) if value is not None else (default or '')
            except (KeyError, TypeError):
                return default or match.group(0)

        return re.sub(pattern, replace_var, template)

    def _get_nested_value(self, data: Dict, path: str):
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                raise KeyError(f"Cannot access {key} in {type(value)}")
            if value is None:
                break
        return value
```

**权衡**：
- ✅ 灵活性高，支持复杂嵌套
- ✅ 语法简洁，易于理解
- ⚠️ 性能略低于简单替换（可接受）
- ❌ 增加解析复杂度

#### 1.2 前置后置钩子

**决策**：实现测试用例级别的生命周期钩子

**钩子类型**：
1. `before_test_case` - 测试用例执行前
2. `after_test_case` - 测试用例执行后
3. `before_suite` - 测试套件执行前
4. `after_suite` - 测试套件执行后

**实现方案**：
```python
class TestHook(models.Model):
    """测试钩子配置"""
    HOOK_TYPE_CHOICES = [
        ('before_test_case', '测试用例执行前'),
        ('after_test_case', '测试用例执行后'),
        ('before_suite', '测试套件执行前'),
        ('after_suite', '测试套件执行后'),
    ]

    ACTION_TYPE_CHOICES = [
        ('sql', '执行SQL'),
        ('http', '发送HTTP请求'),
        ('shell', '执行Shell脚本'),
        ('delay', '延迟等待'),
        ('variable', '设置变量'),
    ]

    test_case = models.ForeignKey(
        'ApiTestCase',
        on_delete=models.CASCADE,
        related_name='hooks',
        null=True,
        blank=True
    )
    hook_type = models.CharField(max_length=20, choices=HOOK_TYPE_CHOICES)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    action_config = JSONField(default=dict)
    is_enabled = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
```

**权衡**：
- ✅ 灵活性高，支持多种操作
- ✅ 可组合，支持复杂场景
- ⚠️ 需要额外的安全检查（Shell执行）
- ❌ 增加执行复杂度

#### 1.3 条件分支支持

**决策**：实现基于响应的条件判断

**语法设计**：
```yaml
conditions:
  - if: "${response.status} == 200"
    then:
      - extract: user_id from $.data.id
      - execute: verify_email
  - elif: "${response.status} == 401"
    then:
      - execute: login_retry
  - else:
      - execute: report_error
```

**实现方案**：
```python
class ConditionalExecutor:
    def evaluate(self, condition: str, context: Dict) -> bool:
        """
        安全的条件表达式求值
        支持的操作符: ==, !=, >, <, >=, <=, contains, matches, in
        """
        # 使用ast模块进行安全的表达式解析
        # 限制可用的操作和函数
        pass

    def execute_branches(
        self,
        branches: List[Dict],
        context: Dict
    ) -> Any:
        for branch in branches:
            if self.evaluate(branch['if'], context):
                return self.execute_actions(branch['then'], context)
        return None
```

**权衡**：
- ✅ 支持复杂测试流程
- ✅ 可读性好
- ⚠️ 需要安全审查（表达式注入）
- ❌ 调试复杂度增加

#### 1.4 并发执行

**决策**：使用线程池实现并发执行

**技术选型**：
- 并发模型：线程池（`concurrent.futures.ThreadPoolExecutor`）
- 并发度：可配置（默认4）
- 依赖解析：DAG（有向无环图）

**实现方案**：
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set
import networkx as nx

class ConcurrentTestExecutor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute_tests(
        self,
        test_cases: List[ApiTestCase],
        dependencies: Dict[int, Set[int]]
    ) -> List[TestResult]:
        """
        并发执行测试用例

        Args:
            test_cases: 测试用例列表
            dependencies: 依赖关系 {case_id: {dependent_case_ids}}
        """
        # 构建DAG
        dag = self._build_dag(test_cases, dependencies)

        # 拓扑排序，分层执行
        execution_layers = nx.topological_generations(dag)

        results = []
        for layer in execution_layers:
            # 并发执行当前层的所有用例
            futures = {
                self.executor.submit(self._execute_single, tc): tc
                for tc in layer
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        return results
```

**权衡**：
- ✅ 执行效率显著提升
- ✅ 充分利用系统资源
- ⚠️ 需要管理共享状态
- ⚠️ 调试难度增加

### 2. 性能优化

#### 2.1 后端查询优化

**决策**：全面优化数据库查询

**优化策略**：

1. **索引优化**
```python
# 为高频查询字段添加索引
class Meta:
    indexes = [
        # 组合索引
        models.Index(fields=['project', 'is_deleted'], name='project_deleted_idx'),
        models.Index(fields=['execution', 'status'], name='exec_status_idx'),

        # 单字段索引
        models.Index(fields=['created_time'], name='created_idx'),

        # 覆盖索引
        models.Index(fields=['status', 'response_time'], name='status_time_idx'),
    ]
```

2. **查询优化**
```python
# 使用select_related减少外键查询
queryset = ApiTestCase.objects.select_related(
    'project',
    'collection',
    'owner'
).prefetch_related(
    'assertions',
    'extractions'
)

# 使用only限制查询字段
queryset = queryset.only('id', 'name', 'method', 'url')
```

3. **Redis缓存**
```python
from django.core.cache import cache

class CachedQuerySet:
    def get_with_cache(self, key, timeout=300):
        """带缓存的查询"""
        cached = cache.get(key)
        if cached is not None:
            return cached

        result = self.get()
        cache.set(key, result, timeout)
        return result
```

**权衡**：
- ✅ 查询性能提升5-10倍
- ✅ 数据库负载降低
- ⚠️ 索引增加写入开销
- ⚠️ 缓存一致性需要处理

#### 2.2 前端性能优化

**决策**：多维度优化前端性能

**优化策略**：

1. **大组件拆分**
```vue
<!-- 拆分前: RealtimeExecutionStatus.vue (2089行) -->
<!-- 拆分后: -->
<!-- components/RealtimeExecutionStatus/ -->
<!--   - index.vue (主容器, 200行) -->
<!--   - ExecutionHeader.vue (头部, 100行) -->
<!--   - StatisticsPanel.vue (统计, 150行) -->
<!--   - TestCaseList.vue (用例列表, 300行) -->
<!--   - ResponseChart.vue (响应图表, 250行) -->
```

2. **虚拟滚动**
```vue
<template>
  <VirtualList
    :items="testCases"
    :item-size="80"
    :buffer="10"
  >
    <template #default="{ item }">
      <TestCaseItem :case="item" />
    </template>
  </VirtualList>
</template>
```

3. **前端缓存**
```typescript
// api-cache.ts
class ApiCache {
  private cache = new Map<string, { data: any; expiry: number }>();

  get(key: string, ttl: number = 300000) {
    const item = this.cache.get(key);
    if (item && item.expiry > Date.now()) {
      return item.data;
    }
    this.cache.delete(key);
    return null;
  }

  set(key: string, data: any, ttl: number = 300000) {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl,
    });
  }
}
```

**权衡**：
- ✅ 渲染性能提升
- ✅ 内存使用优化
- ⚠️ 代码复杂度增加
- ⚠️ 需要额外的缓存策略

### 3. CI/CD集成

#### 3.1 CLI工具设计

**决策**：开发独立的CLI工具

**技术选型**：
- 框架：`click` 或 `typer`
- 打包：`PyInstaller`

**功能设计**：
```bash
# 触发测试
api-test run --project <id> --environment <id> --output junit.xml

# 查看结果
api-test results <execution-id>

# 导出报告
api-test export <execution-id> --format junit --output results.xml

# 质量门禁
api-test gate --threshold 95 --fail-on-error
```

**实现方案**：
```python
import click

@click.group()
def cli():
    """API测试平台CLI工具"""
    pass

@cli.command()
@click.option('--project', required=True, help='项目ID')
@click.option('--environment', help='环境ID')
@click.option('--output', help='输出文件路径')
@click.option('--format', type=click.Choice(['junit', 'allure', 'json']), default='junit')
def run(project, environment, output, format):
    """运行测试"""
    # 实现测试执行逻辑
    pass
```

**权衡**：
- ✅ 易于集成到CI/CD
- ✅ 支持自动化脚本
- ⚠️ 需要维护额外工具
- ❌ 增加发布复杂度

#### 3.2 Webhook支持

**决策**：实现事件驱动的Webhook通知

**事件类型**：
- `test_execution.started` - 测试开始
- `test_execution.completed` - 测试完成
- `test_execution.failed` - 测试失败
- `test_case.failed` - 用例失败

**实现方案**：
```python
class Webhook(models.Model):
    """Webhook配置"""
    EVENT_TYPE_CHOICES = [
        ('test_execution.started', '测试开始'),
        ('test_execution.completed', '测试完成'),
        ('test_execution.failed', '测试失败'),
        ('test_case.failed', '用例失败'),
    ]

    project = models.ForeignKey('ApiProject', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    url = models.URLField()
    secret = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

class WebhookService:
    def trigger(self, event_type: str, payload: Dict):
        """触发Webhook"""
        webhooks = Webhook.objects.filter(
            event_type=event_type,
            is_active=True
        )

        for webhook in webhooks:
            self._send_webhook(webhook, payload)

    def _send_webhook(self, webhook: Webhook, payload: Dict):
        """发送Webhook请求"""
        signature = self._generate_signature(payload, webhook.secret)

        requests.post(
            webhook.url,
            json=payload,
            headers={
                'X-Webhook-Signature': signature,
                'X-Webhook-Event': webhook.event_type,
            },
            timeout=10
        )
```

**权衡**：
- ✅ 灵活的集成方式
- ✅ 支持多种外部系统
- ⚠️ 需要处理失败重试
- ⚠️ 安全性需要保障

### 4. 安全增强

#### 4.1 敏感数据加密

**决策**：使用AES-256加密敏感字段

**技术选型**：
- 加密算法：AES-256-GCM
- 密钥管理：环境变量 + KMS（可选）

**实现方案**：
```python
from cryptography.fernet import Fernet

class EncryptedField(models.TextField):
    """加密字段"""

    def __init__(self, *args, **kwargs):
        self.cipher = Fernet(settings.ENCRYPTION_KEY)
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return value
        try:
            return self.cipher.decrypt(value.encode()).decode()
        except:
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return self.cipher.encrypt(value.encode()).decode()

# 使用示例
class ApiTestEnvironment(models.Model):
    # 加密存储敏感配置
    sensitive_config = EncryptedField(default=dict, blank=True)
```

**权衡**：
- ✅ 数据安全性高
- ⚠️ 无法直接查询加密字段
- ⚠️ 性能略有影响
- ❌ 密钥管理复杂

#### 4.2 审计日志

**决策**：实现完整的操作审计

**审计范围**：
- 用户登录/登出
- 测试执行
- 数据修改/删除
- 配置变更

**实现方案**：
```python
class AuditLog(models.Model):
    """审计日志"""
    ACTION_TYPE_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('execute', '执行'),
        ('login', '登录'),
        ('logout', '登出'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    resource_type = models.CharField(max_length=50)  # 'TestCase', 'Project', etc.
    resource_id = models.IntegerField()
    changes = JSONField(default=dict)  # 变更详情
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
```

**权衡**：
- ✅ 完整的操作追踪
- ✅ 满足合规要求
- ⚠️ 存储空间需求大
- ⚠️ 需要定期归档

### 5. 测试数据管理

#### 5.1 Mock服务

**决策**：集成 Mock Server

**技术选型**：
- 方案A：自研简单Mock服务
- 方案B：集成 mocket (推荐)
- 方案C：集成 WireMock

**推荐方案B**：使用 mocket 库

**实现方案**：
```python
import mocket

class MockService:
    def __init__(self):
        self.mocks = {}

    def add_mock(self, url: str, method: str, response: Dict):
        """添加Mock规则"""
        key = f"{method}:{url}"
        self.mocks[key] = response

    def enable_mocks(self):
        """启用Mock"""
        mocket.enable()
        for key, response in self.mocks.items():
            method, url = key.split(':')
            mocket.register(
                method,
                url,
                body=json.dumps(response),
                status=200
            )

    def disable_mocks(self):
        """禁用Mock"""
        mocket.disable()
```

**权衡**：
- ✅ 降低测试环境依赖
- ✅ 提高测试稳定性
- ⚠️ 需要维护Mock规则
- ❌ 与真实环境可能存在差异

## 数据库设计

### 新增表

#### 1. 测试钩子表 (api_test_hooks)
```sql
CREATE TABLE api_test_hooks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_case_id INT NULL,
    hook_type VARCHAR(20) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    action_config JSON NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    order INT DEFAULT 0,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_case_id) REFERENCES api_test_cases(id)
);
```

#### 2. 审计日志表 (api_audit_logs)
```sql
CREATE TABLE api_audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    action_type VARCHAR(20) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INT NOT NULL,
    changes JSON NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_timestamp (user_id, timestamp),
    INDEX idx_resource (resource_type, resource_id)
);
```

#### 3. Webhook表 (api_webhooks)
```sql
CREATE TABLE api_webhooks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES api_projects(id)
);
```

#### 4. 测试依赖表 (api_test_dependencies)
```sql
CREATE TABLE api_test_dependencies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_case_id INT NOT NULL,
    depends_on_case_id INT NOT NULL,
    dependency_type VARCHAR(20) DEFAULT 'sequential',
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_dependency (test_case_id, depends_on_case_id),
    FOREIGN KEY (test_case_id) REFERENCES api_test_cases(id),
    FOREIGN KEY (depends_on_case_id) REFERENCES api_test_cases(id)
);
```

### 索引优化

```sql
-- 测试结果表索引优化
ALTER TABLE api_test_results
ADD INDEX idx_execution_status_time (execution_id, status, start_time),
ADD INDEX idx_case_status_time (test_case_id, status, start_time),
ADD INDEX idx_response_time (response_time);

-- HTTP执行记录索引优化
ALTER TABLE api_http_execution_records
ADD INDEX idx_project_status_time (project_id, status, created_time),
ADD INDEX idx_environment_status_time (environment_id, status, created_time);

-- 测试用例表索引优化
ALTER TABLE api_test_cases
ADD INDEX idx_project_collection_deleted (project_id, collection_id, is_deleted),
ADD INDEX idx_method_url (method, url(255));
```

## API设计

### 新增端点

#### 1. 钩子管理
```
GET    /api/v1/api-automation/test-cases/{id}/hooks/     # 列出钩子
POST   /api/v1/api-automation/test-cases/{id}/hooks/     # 创建钩子
PUT    /api/v1/api-automation/hooks/{id}/                # 更新钩子
DELETE /api/v1/api-automation/hooks/{id}/                # 删除钩子
```

#### 2. 依赖管理
```
GET    /api/v1/api-automation/test-cases/{id}/dependencies/  # 列出依赖
POST   /api/v1/api-automation/test-cases/{id}/dependencies/  # 添加依赖
DELETE /api/v1/api-automation/test-cases/{id}/dependencies/{dep_id}/  # 删除依赖
```

#### 3. Webhook管理
```
GET    /api/v1/api-automation/projects/{id}/webhooks/    # 列出Webhook
POST   /api/v1/api-automation/projects/{id}/webhooks/    # 创建Webhook
PUT    /api/v1/api-automation/webhooks/{id}/             # 更新Webhook
DELETE /api/v1/api-automation/webhooks/{id}/             # 删除Webhook
POST   /api/v1/api-automation/webhooks/{id}/test/        # 测试Webhook
```

#### 4. 审计日志
```
GET    /api/v1/api-automation/audit-logs/                # 审计日志列表
GET    /api/v1/api-automation/audit-logs/{id}/           # 审计日志详情
```

#### 5. 分析统计
```
GET    /api/v1/api-automation/analytics/trends/          # 趋势分析
GET    /api/v1/api-automation/analytics/performance/     # 性能分析
GET    /api/v1/api-automation/analytics/defects/         # 缺陷分析
POST   /api/v1/api-automation/analytics/compare/         # 对比分析
```

## 迁移策略

### 阶段1：准备阶段（1周）
- 创建新的数据库迁移
- 准备回滚脚本
- 设置测试环境

### 阶段2：功能开发（按阶段依次进行）
- 每个阶段独立开发
- 保持向后兼容
- 单元测试覆盖

### 阶段3：灰度发布（2周）
- 小范围用户测试
- 监控性能指标
- 收集用户反馈

### 阶段4：全量发布（1周）
- 数据迁移
- 功能切换
- 旧版本下线

## 风险缓解

### 技术风险
1. **性能优化引入Bug**
   - 缓解：完整的回归测试套件
   - 缓解：性能基准测试

2. **数据迁移失败**
   - 缓解：迁移前完整备份
   - 缓解：分批迁移策略

3. **向后兼容性破坏**
   - 缓解：API版本控制
   - 缓解：兼容性测试

### 业务风险
1. **用户学习成本**
   - 缓解：详细的文档
   - 缓解：渐进式发布

2. **开发周期延长**
   - 缓解：分阶段交付
   - 缓解：优先级排序

## 监控指标

### 技术指标
- API响应时间 (P50, P95, P99)
- 数据库查询时间
- 缓存命中率
- 并发执行效率

### 业务指标
- 测试执行时间
- 测试通过率
- 用户活跃度
- 功能使用率
