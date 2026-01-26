# 测试场景（测试用例）功能设计文档

## 一、功能概述

### 1.1 功能背景

现有的 **ApiTestCase**（接口测试用例）是单接口级别的测试，虽然支持断言和数据提取，但无法实现多个接口之间的串联执行和变量传递。

为了支持复杂的业务流程测试，需要引入一个新的概念：**ApiTestScenario**（测试场景/测试用例）。

### 1.2 功能目标

测试场景功能允许用户将多个接口测试用例串联成一个完整的测试流程，实现：

1. **多接口串联执行**：按顺序执行多个接口
2. **变量传递**：前置接口提取的变量可供后续接口使用
3. **每个步骤独立断言**：每个接口步骤都可以配置独立的断言
4. **完整执行记录**：保留详细的执行记录供后续查询
5. **智能数据清理**：执行记录按需保留，7天前的数据自动清理

### 1.3 与现有功能的关系

| 概念 | 说明 | 关系 |
|------|------|------|
| **ApiTestCase** | 单个接口的测试配置 | 可被添加到测试场景作为步骤 |
| **ApiTestScenario** | 多个接口串联的测试流程 | 由多个 ApiTestCase 组成 |
| **ApiTestExecution** | 单个或批量用例的执行记录 | 现有执行记录，保持不变 |
| **ApiTestScenarioExecution** | 测试场景的执行记录 | 新增，记录场景执行过程 |

---

## 二、数据模型设计

### 2.1 核心数据模型

#### 2.1.1 ApiTestScenario（测试场景）

```python
class ApiTestScenario(models.Model):
    """
    测试场景（测试用例）
    用于串联执行多个接口，实现复杂业务流程测试
    """
    name = models.CharField(max_length=200, verbose_name='场景名称')
    description = models.TextField(blank=True, null=True, verbose_name='场景描述')
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='test_scenarios',
        verbose_name='所属项目'
    )
    # 场景配置
    execution_config = JSONField(default=dict, verbose_name='执行配置')
    # 例如：{"stop_on_failure": true, "retry_count": 1, "timeout": 30}

    # 统计信息
    total_steps = models.IntegerField(default=0, verbose_name='总步骤数')

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_scenarios',
        verbose_name='创建者'
    )
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_test_scenarios'
        verbose_name = '测试场景'
        verbose_name_plural = '测试场景'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['project', 'is_deleted'], name='scenario_project_deleted_idx'),
            models.Index(fields=['created_time'], name='scenario_created_idx'),
        ]
```

#### 2.1.2 ApiTestScenarioStep（场景步骤）

```python
class ApiTestScenarioStep(models.Model):
    """
    测试场景步骤
    定义场景中每个步骤的配置
    """
    scenario = models.ForeignKey(
        ApiTestScenario,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='所属场景'
    )
    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='scenario_steps',
        verbose_name='关联的接口测试用例'
    )

    # 步骤配置
    step_order = models.IntegerField(default=0, verbose_name='执行顺序')
    step_name = models.CharField(max_length=200, blank=True, verbose_name='步骤名称')

    # 步骤级变量覆盖（可选）
    variable_overrides = JSONField(default=dict, verbose_name='变量覆盖')

    # 步骤级断言配置（可选，覆盖用例默认断言）
    step_assertions = JSONField(default=list, verbose_name='步骤断言')

    # 步骤执行控制
    enabled = models.BooleanField(default=True, verbose_name='是否启用')
    stop_on_failure = models.BooleanField(default=False, verbose_name='失败时停止')

    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'api_test_scenario_steps'
        verbose_name = '场景步骤'
        verbose_name_plural = '场景步骤'
        ordering = ['step_order']
        indexes = [
            models.Index(fields=['scenario', 'step_order'], name='step_scenario_order_idx'),
            models.Index(fields=['test_case'], name='step_case_idx'),
        ]
```

#### 2.1.3 ApiTestScenarioExecution（场景执行记录）

```python
class ApiTestScenarioExecution(models.Model):
    """
    测试场景执行记录
    记录每次场景执行的总体信息
    """
    scenario = models.ForeignKey(
        ApiTestScenario,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name='测试场景'
    )
    project = models.ForeignKey(
        ApiProject,
        on_delete=models.CASCADE,
        related_name='scenario_executions',
        verbose_name='所属项目'
    )
    environment = models.ForeignKey(
        ApiTestEnvironment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scenario_executions',
        verbose_name='执行环境'
    )

    name = models.CharField(max_length=200, verbose_name='执行名称')
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', '待执行'),
            ('RUNNING', '执行中'),
            ('COMPLETED', '已完成'),
            ('FAILED', '执行失败'),
            ('CANCELLED', '已取消'),
        ],
        default='PENDING',
        verbose_name='执行状态'
    )

    # 统计信息
    total_steps = models.IntegerField(default=0, verbose_name='总步骤数')
    passed_steps = models.IntegerField(default=0, verbose_name='通过步骤数')
    failed_steps = models.IntegerField(default=0, verbose_name='失败步骤数')
    skipped_steps = models.IntegerField(default=0, verbose_name='跳过步骤数')

    # 时间信息
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='执行时长(秒)')

    # 执行信息
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scenario_executions',
        verbose_name='执行者'
    )
    execution_source = models.CharField(
        max_length=20,
        choices=[
            ('MANUAL', '手动执行'),
            ('SCHEDULED', '定时执行'),
            ('API', 'API触发'),
        ],
        default='MANUAL',
        verbose_name='执行来源'
    )

    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否删除')

    class Meta:
        db_table = 'api_test_scenario_executions'
        verbose_name = '场景执行记录'
        verbose_name_plural = '场景执行记录'
        ordering = ['-created_time']
        indexes = [
            models.Index(fields=['scenario', 'created_time'], name='scenario_exec_scenario_time_idx'),
            models.Index(fields=['environment', 'status'], name='scenario_exec_env_status_idx'),
            models.Index(fields=['status', 'created_time'], name='scenario_exec_status_time_idx'),
            models.Index(fields=['created_time'], name='scenario_exec_created_idx'),
        ]
```

#### 2.1.4 ApiTestScenarioStepResult（步骤执行结果）

```python
class ApiTestScenarioStepResult(models.Model):
    """
    场景步骤执行结果
    记录每个步骤的详细执行结果
    """
    scenario_execution = models.ForeignKey(
        ApiTestScenarioExecution,
        on_delete=models.CASCADE,
        related_name='step_results',
        verbose_name='场景执行记录'
    )
    scenario_step = models.ForeignKey(
        ApiTestScenarioStep,
        on_delete=models.CASCADE,
        related_name='execution_results',
        verbose_name='场景步骤'
    )
    test_case = models.ForeignKey(
        ApiTestCase,
        on_delete=models.CASCADE,
        related_name='scenario_step_results',
        verbose_name='测试用例'
    )

    # 执行状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', '待执行'),
            ('RUNNING', '执行中'),
            ('PASSED', '通过'),
            ('FAILED', '失败'),
            ('SKIPPED', '跳过'),
            ('ERROR', '错误'),
        ],
        default='PENDING',
        verbose_name='执行状态'
    )

    # 请求信息（简化存储，状态码200时只存必要信息）
    request_summary = JSONField(default=dict, verbose_name='请求摘要')
    # 包含: method, url, headers (部分)

    # 响应摘要
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_time = models.IntegerField(null=True, blank=True, verbose_name='响应时间(ms)')

    # 完整信息（仅状态码非200时存储）
    request_full = JSONField(default=dict, blank=True, verbose_name='完整请求信息')
    response_full = JSONField(default=dict, blank=True, verbose_name='完整响应信息')
    error_info = JSONField(default=dict, blank=True, verbose_name='错误信息')

    # 断言结果
    assertion_results = JSONField(default=list, blank=True, verbose_name='断言结果')

    # 提取的变量（用于变量传递）
    extracted_variables = JSONField(default=dict, blank=True, verbose_name='提取的变量')

    # 时间信息
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='执行时长(ms)')

    class Meta:
        db_table = 'api_test_scenario_step_results'
        verbose_name = '步骤执行结果'
        verbose_name_plural = '步骤执行结果'
        ordering = ['scenario_step__step_order']
        indexes = [
            models.Index(fields=['scenario_execution', 'scenario_step'], name='step_result_exec_step_idx'),
            models.Index(fields=['scenario_execution', 'status'], name='step_result_exec_status_idx'),
            models.Index(fields=['status', 'start_time'], name='step_result_status_time_idx'),
        ]
```

### 2.2 数据模型关系图

```
ApiProject (项目)
    │
    ├── ApiTestScenario (测试场景)
    │     │
    │     ├── ApiTestScenarioStep (场景步骤) ──→ ApiTestCase (接口用例)
    │     │
    │     └── ApiTestScenarioExecution (场景执行记录)
    │           │
    │           └── ApiTestScenarioStepResult (步骤执行结果)
    │
    └── ApiTestEnvironment (测试环境)
```

---

## 三、核心功能设计

### 3.1 变量传递机制

#### 3.1.1 变量类型

| 变量类型 | 语法格式 | 作用域 | 说明 |
|---------|---------|--------|------|
| 环境变量 | `${env.base_url}` | 场景级 | 从环境配置获取 |
| 全局变量 | `${global.xxx}` | 场景级 | 从环境全局变量获取 |
| 场景变量 | `${scenario.xxx}` | 场景级 | 前置步骤提取的变量 |
| 步骤变量 | `${step.xxx}` | 步骤级 | 当前步骤提取的变量 |

#### 3.1.2 变量提取和传递流程

```
┌─────────────────────────────────────────────────────────────┐
│                    测试场景执行开始                          │
│                  初始化场景变量池 = {}                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    步骤1：用户登录                            │
│  请求: POST /api/login                                       │
│  请求体: {"username": "test", "password": "123"}             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    响应处理和变量提取                         │
│  响应: {"code": 0, "data": {"token": "abc123", "id": 456}}  │
│  提取配置:                                                    │
│    - token: $.data.token → ${scenario.login_token}           │
│    - userId: $.data.id → ${scenario.user_id}                 │
│  场景变量池 = {login_token: "abc123", user_id: 456}         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    步骤2：获取用户信息                          │
│  请求: GET /api/user/${scenario.user_id}                     │
│  请求头: {"Authorization": "Bearer ${scenario.login_token}"} │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    步骤3：创建订单                             │
│  请求: POST /api/order/create                               │
│  请求体: {"userId": ${scenario.user_id}, ...}                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 执行流程控制

#### 3.2.1 执行策略

| 策略 | 说明 | 配置 |
|------|------|------|
| **失败停止** | 某步骤失败后停止执行后续步骤 | 场景级: `stop_on_failure: true` |
| **失败继续** | 某步骤失败后继续执行后续步骤 | 场景级: `stop_on_failure: false` |
| **步骤级控制** | 每个步骤可单独配置失败行为 | 步骤级: `stop_on_failure: true/false` |
| **重试机制** | 失败步骤自动重试 | 场景级: `retry_count: 1` |

#### 3.2.2 执行状态机

```
PENDING (待执行)
    │
    ▼
RUNNING (执行中)
    │
    ├─── 所有步骤通过 ──→ COMPLETED (已完成)
    │
    ├─── 某步骤失败 + stop_on_failure=true ──→ FAILED (执行失败)
    │
    ├─── 用户取消 ──→ CANCELLED (已取消)
    │
    └─── 执行异常 ──→ ERROR (执行错误)
```

### 3.3 数据存储优化

#### 3.3.1 数据分级存储

根据响应状态码分级存储数据：

| 状态码 | 存储内容 | 说明 |
|--------|---------|------|
| **200-299** | 简要信息 | 只存储 request_summary + response_status + response_time |
| **其他** | 完整信息 | 存储 request_full + response_full + error_info |

#### 3.3.2 数据清理机制

```python
# 定时任务：每天凌晨清理7天前的执行记录
@app.task
def cleanup_old_scenario_executions():
    """
    清理7天前的场景执行记录
    保留：最近7天的记录
    删除：7天前的记录（包括场景执行记录和步骤结果）
    """
    cutoff_date = timezone.now() - timedelta(days=7)
    ApiTestScenarioExecution.objects.filter(
        created_time__lt=cutoff_date
    ).delete()
```

---

## 四、后端API设计

### 4.1 场景管理API

```
# 场景管理
GET    /api/v1/api-automation/scenarios/              # 场景列表
POST   /api/v1/api-automation/scenarios/              # 创建场景
GET    /api/v1/api-automation/scenarios/{id}/         # 场景详情
PUT    /api/v1/api-automation/scenarios/{id}/         # 更新场景
DELETE /api/v1/api-automation/scenarios/{id}/         # 删除场景
POST   /api/v1/api-automation/scenarios/{id}/clone/   # 克隆场景

# 场景步骤管理
GET    /api/v1/api-automation/scenarios/{id}/steps/           # 获取步骤列表
POST   /api/v1/api-automation/scenarios/{id}/steps/           # 添加步骤
PUT    /api/v1/api-automation/scenarios/{id}/steps/batch/     # 批量更新步骤
DELETE /api/v1/api-automation/scenarios/{id}/steps/{step_id}/ # 删除步骤
```

### 4.2 场景执行API

```
# 场景执行
POST   /api/v1/api-automation/scenario-executions/              # 创建执行
GET    /api/v1/api-automation/scenario-executions/             # 执行列表
GET    /api/v1/api-automation/scenario-executions/{id}/        # 执行详情
POST   /api/v1/api-automation/scenario-executions/{id}/execute/# 执行场景
POST   /api/v1/api-automation/scenario-executions/{id}/cancel/ # 取消执行

# 步骤结果
GET    /api/v1/api-automation/scenario-executions/{id}/steps/  # 获取步骤结果
GET    /api/v1/api-automation/scenario-executions/{id}/steps/{step_id}/ # 步骤详情
```

### 4.3 数据管理API

```
# 数据清理
POST   /api/v1/api-automation/scenario-executions/cleanup/     # 手动清理旧数据
GET    /api/v1/api-automation/scenario-executions/statistics/  # 执行统计
```

---

## 五、前端页面设计

### 5.1 页面结构

```
测试场景模块
├── 场景列表页 (ScenarioList.vue)
│   ├── 场景列表表格
│   ├── 搜索和筛选
│   └── 新建场景按钮
│
├── 场景详情页 (ScenarioDetail.vue)
│   ├── 场景基本信息
│   ├── 步骤配置区域
│   │   ├── 步骤列表（可拖拽排序）
│   │   ├── 添加步骤按钮
│   │   └── 步骤配置面板
│   └── 执行记录区域
│
├── 场景创建/编辑页 (ScenarioEdit.vue)
│   ├── 基本信息表单
│   ├── 步骤选择器
│   ├── 执行配置
│   └── 预览和保存
│
└── 场景执行监控页 (ScenarioExecutionMonitor.vue)
    ├── 执行进度条
    ├── 实时日志显示
    ├── 步骤执行状态卡片
    ├── 变量查看器
    └── 执行结果汇总
```

### 5.2 核心组件

| 组件名称 | 功能描述 |
|---------|---------|
| `ScenarioStepList.vue` | 场景步骤列表，支持拖拽排序 |
| `ScenarioStepConfig.vue` | 单个步骤配置面板 |
| `ScenarioVariableViewer.vue` | 变量查看器，显示场景变量池 |
| `ScenarioExecutionProgress.vue` | 执行进度可视化 |
| `ScenarioStepResultCard.vue` | 步骤执行结果卡片 |

### 5.3 状态管理

```typescript
// stores/scenario.ts
export const useScenarioStore = defineStore('scenario', () => {
  const scenarios = ref<ApiTestScenario[]>([])
  const currentScenario = ref<ApiTestScenario | null>(null)
  const scenarioSteps = ref<ApiTestScenarioStep[]>([])
  const executions = ref<ApiTestScenarioExecution[]>([])

  // CRUD操作
  const fetchScenarios = async (params?: any) => { ... }
  const fetchScenario = async (id: number) => { ... }
  const createScenario = async (data: ScenarioCreate) => { ... }
  const updateScenario = async (id: number, data: Partial<ApiTestScenario>) => { ... }
  const deleteScenario = async (id: number) => { ... }

  // 步骤管理
  const fetchSteps = async (scenarioId: number) => { ... }
  const addStep = async (scenarioId: number, step: StepCreate) => { ... }
  const updateSteps = async (scenarioId: number, steps: ApiTestScenarioStep[]) => { ... }
  const deleteStep = async (scenarioId: number, stepId: number) => { ... }

  // 执行管理
  const executeScenario = async (executionId: number) => { ... }
  const cancelExecution = async (executionId: number) => { ... }
  const fetchExecutionResults = async (executionId: number) => { ... }

  return {
    scenarios, currentScenario, scenarioSteps, executions,
    fetchScenarios, fetchScenario, createScenario, updateScenario, deleteScenario,
    fetchSteps, addStep, updateSteps, deleteStep,
    executeScenario, cancelExecution, fetchExecutionResults
  }
})
```

---

## 六、执行引擎设计

### 6.1 场景执行引擎

```python
class ScenarioExecutionEngine:
    """
    测试场景执行引擎
    负责按顺序执行场景中的步骤，处理变量传递和断言验证
    """

    def __init__(self, scenario_execution: ApiTestScenarioExecution):
        self.scenario_execution = scenario_execution
        self.scenario = scenario_execution.scenario
        self.environment = scenario_execution.environment
        self.variable_pool = {}  # 场景变量池

    def execute(self):
        """执行场景"""
        self.scenario_execution.status = 'RUNNING'
        self.scenario_execution.start_time = timezone.now()
        self.scenario_execution.save()

        try:
            steps = self.scenario.steps.filter(enabled=True).order_by('step_order')
            self.scenario_execution.total_steps = steps.count()

            for step in steps:
                # 检查是否需要停止（前置步骤失败）
                if self._should_stop():
                    break

                # 执行步骤
                step_result = self._execute_step(step)
                self._process_step_result(step, step_result)

            # 更新执行状态
            self._finalize_execution()

        except Exception as e:
            self._handle_execution_error(e)

    def _execute_step(self, step: ApiTestScenarioStep) -> StepResult:
        """执行单个步骤"""
        # 1. 准备请求数据（应用变量替换）
        request_data = self._prepare_request(step)

        # 2. 执行HTTP请求
        http_response = self._execute_http_request(request_data)

        # 3. 执行断言
        assertion_results = self._execute_assertions(step, http_response)

        # 4. 提取变量到场景变量池
        extracted_vars = self._extract_variables(step, http_response)
        self.variable_pool.update(extracted_vars)

        # 5. 返回步骤结果
        return StepResult(
            status=self._determine_status(assertion_results),
            http_response=http_response,
            assertion_results=assertion_results,
            extracted_variables=extracted_vars
        )

    def _prepare_request(self, step: ApiTestScenarioStep) -> RequestData:
        """准备请求数据，应用变量替换"""
        test_case = step.test_case

        # 合并环境变量、场景变量、步骤变量
        variables = {
            'env': self.environment.global_variables or {},
            'scenario': self.variable_pool,
            'step': {}
        }

        # 变量替换
        url = self._replace_variables(test_case.url, variables)
        headers = self._replace_variables(test_case.headers, variables)
        params = self._replace_variables(test_case.params, variables)
        body = self._replace_variables(test_case.body, variables)

        return RequestData(
            method=test_case.method,
            url=url,
            headers=headers,
            params=params,
            body=body
        )
```

### 6.2 变量处理服务

```python
class ScenarioVariableService:
    """
    场景变量服务
    负责变量的管理、替换和传递
    """

    @staticmethod
    def replace_variables(text: str, variable_pool: dict) -> str:
        """替换文本中的变量"""
        if not text or not variable_pool:
            return text

        # 支持多种变量格式
        # ${env.xxx}, ${global.xxx}, ${scenario.xxx}, ${step.xxx}
        pattern = r'\$\{(env|global|scenario|step)\.([^}]+)\}'

        def replacer(match):
            var_type, var_name = match.groups()
            if var_type in variable_pool:
                return str(variable_pool[var_type].get(var_name, match.group(0)))
            return match.group(0)

        return re.sub(pattern, replacer, text)

    @staticmethod
    def extract_variables(
        step: ApiTestScenarioStep,
        http_response: HttpResponse,
        variable_pool: dict
    ) -> dict:
        """从响应中提取变量"""
        extraction_engine = ExtractionEngine()

        # 获取步骤的数据提取配置
        extractions = []
        if step.step_assertions:
            # 步骤级断言中可能包含提取配置
            extractions = step.step_assertions.get('extractions', [])
        else:
            # 使用测试用例的提取配置
            extractions = ApiTestCaseExtractionSerializer(
                step.test_case.extractions.all(),
                many=True
            ).data

        # 执行提取
        extracted_vars, _ = extraction_engine.extract_variables(
            extractions=extractions,
            http_response=http_response.raw_response,
            response_body=http_response.body,
            response_text=http_response.text
        )

        # 添加到场景变量池
        for var_name, var_value in extracted_vars.items():
            variable_pool['scenario'][var_name] = var_value

        return extracted_vars
```

---

## 七、WebSocket 实时推送

### 7.1 推送事件

```python
# 场景执行相关事件
{
    "type": "scenario_execution_started",
    "data": {
        "execution_id": 123,
        "scenario_id": 456,
        "scenario_name": "用户注册流程"
    }
}

{
    "type": "scenario_step_started",
    "data": {
        "execution_id": 123,
        "step_id": 789,
        "step_name": "用户登录",
        "step_order": 1
    }
}

{
    "type": "scenario_step_completed",
    "data": {
        "execution_id": 123,
        "step_id": 789,
        "status": "PASSED",
        "response_time": 250,
        "extracted_variables": {
            "user_id": 123,
            "token": "abc123"
        }
    }
}

{
    "type": "scenario_execution_completed",
    "data": {
        "execution_id": 123,
        "status": "COMPLETED",
        "total_steps": 5,
        "passed_steps": 4,
        "failed_steps": 1,
        "duration": 1500
    }
}

{
    "type": "scenario_variable_extracted",
    "data": {
        "execution_id": 123,
        "step_id": 789,
        "variable_name": "user_id",
        "variable_value": 123
    }
}
```

---

## 八、测试用例使用场景

### 8.1 用户注册流程

```
场景名称: 用户注册完整流程

步骤1: 发送验证码
  请求: POST /api/sms/send
  请求体: {"phone": "13800138000"}
  断言: status_code == 200
  提取: 无

步骤2: 用户注册
  请求: POST /api/user/register
  请求体: {"phone": "13800138000", "code": "1234", "password": "abc123"}
  断言: status_code == 200, $.code == 0
  提取: user_id = $.data.user.id

步骤3: 自动登录
  请求: POST /api/user/login
  请求体: {"phone": "13800138000", "password": "abc123"}
  断言: status_code == 200, $.data.token exists
  提取: token = $.data.token

步骤4: 获取用户信息
  请求: GET /api/user/${scenario.user_id}
  请求头: {"Authorization": "Bearer ${scenario.token}"}
  断言: status_code == 200, $.data.user.phone == "13800138000"
  提取: 无
```

### 8.2 订单创建流程

```
场景名称: 订单创建完整流程

步骤1: 用户登录
  请求: POST /api/user/login
  请求体: {"username": "test", "password": "123456"}
  断言: status_code == 200
  提取: token = $.data.token, user_id = $.data.user.id

步骤2: 获取商品列表
  请求: GET /api/products
  请求头: {"Authorization": "Bearer ${scenario.token}"}
  断言: status_code == 200
  提取: product_id = $.data.products[0].id

步骤3: 添加购物车
  请求: POST /api/cart/add
  请求头: {"Authorization": "Bearer ${scenario.token}"}
  请求体: {"product_id": ${scenario.product_id}, "quantity": 2}
  断言: status_code == 200
  提取: cart_id = $.data.cart.id

步骤4: 创建订单
  请求: POST /api/order/create
  请求头: {"Authorization": "Bearer ${scenario.token}"}
  请求体: {"cart_id": ${scenario.cart_id}}
  断言: status_code == 200, $.data.order.status == "pending"
  提取: order_id = $.data.order.id

步骤5: 查询订单
  请求: GET /api/order/${scenario.order_id}
  请求头: {"Authorization": "Bearer ${scenario.token}"}
  断言: status_code == 200, $.data.order.status == "pending"
  提取: 无
```

---

## 九、实施计划

### 9.1 开发步骤

1. **阶段一：数据模型和后端API（预计2天）**
   - 创建数据模型
   - 编写序列化器
   - 实现ViewSet和API接口
   - 编写单元测试

2. **阶段二：执行引擎开发（预计2天）**
   - 实现场景执行引擎
   - 实现变量处理服务
   - 集成WebSocket实时推送
   - 实现数据清理定时任务

3. **阶段三：前端页面开发（预计3天）**
   - 创建场景列表页面
   - 创建场景详情页面
   - 创建场景编辑页面
   - 创建执行监控页面
   - 实现拖拽排序功能
   - 集成WebSocket实时更新

4. **阶段四：测试和优化（预计1天）**
   - 功能测试
   - 性能优化
   - 文档更新

### 9.2 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 变量传递冲突 | 高 | 使用命名空间区分不同类型变量 |
| 执行性能问题 | 中 | 实现异步执行，添加缓存 |
| 数据量过大 | 中 | 分级存储，定期清理 |
| 并发执行冲突 | 低 | 添加执行锁机制 |

---

## 十、总结

测试场景功能通过串联多个接口测试用例，实现了复杂业务流程的自动化测试。核心特点包括：

1. **变量传递**：前置接口提取的变量可供后续接口使用
2. **独立断言**：每个步骤都可以配置独立的断言
3. **执行控制**：支持失败停止/继续、重试等策略
4. **数据优化**：根据响应状态码分级存储数据
5. **实时监控**：WebSocket推送执行进度和结果
6. **自动清理**：定期清理旧的执行记录

该功能与现有的接口测试功能互补，共同构建完整的API自动化测试体系。
