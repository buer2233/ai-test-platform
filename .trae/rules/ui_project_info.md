# UI自动化测试模块 - 项目需求文档

> 创建日期：2026-01-20
> 状态：需求对接阶段
> 版本：v0.1.0-alpha

---

## 一、项目概述

### 1.1 项目定位

基于 **browser_use** 开源框架的 AI 驱动 UI 自动化测试平台。用户通过自然语言描述测试场景，AI 自动理解并执行浏览器操作，生成可视化测试报告。

### 1.2 核心价值

- **自然语言驱动**：无需编码，用中文描述测试意图即可
- **AI 智能执行**：browser_use Agent 自动解析并操作浏览器
- **完全模块化**：独立于 API 自动化模块，可独立部署
- **可视化报告**：实时展示执行过程和结果

### 1.3 技术选型

| 分类 | 技术栈 | 说明 |
|------|--------|------|
| **执行引擎** | browser_use (Python) | GitHub: https://github.com/browser-use/browser-use |
| **LLM 模型** | ChatBrowserUse / OpenAI GPT-4 | browser_use 优化的模型，速度提升 3-5x |
| **浏览器** | Chromium (Playwright驱动) | 支持无头/有头模式 |
| **后端框架** | Django + DRF | 与现有项目保持一致 |
| **前端框架** | Vue 3 + TypeScript + Element Plus | 沿用现有设计系统 |
| **数据库** | SQLite (开发) / MySQL (生产) | 表前缀：`ui_` |

---

## 二、架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  顶部导航栏下拉切换：[API测试 ▼] [UI测试 ▼] [AI测试 ▼]    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  自然语言编辑器   │  │  执行监控面板    │  │  测试报告查看    │  │
│  │  (Markdown输入) │  │  (实时日志/截图) │  │  (ECharts可视化) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/REST API + WebSocket
                                │
┌─────────────────────────────────────────────────────────────────┐
│                       后端层 (Django)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ui_automation 模块 (完全独立)                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │  测试用例管理  │  │  browser_use │  │  报告生成服务 │        │  │
│  │  │  (CRUD API)  │  │  Agent封装   │  │  (HTML/PDF)  │        │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    browser_use 执行层                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Agent ──► Browser ──► Playwright ──► Chromium            │  │
│  │    ↓                                                        │  │
│  │  [自然语言任务] → [AI解析] → [浏览器操作] → [结果返回]      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 项目目录结构

#### 后端结构
```
Django_project/
├── ui_automation/                    # UI自动化模块（新建）
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                     # 数据模型 (UiTestProject, UiTestCase, UiTestReport...)
│   ├── serializers.py                # DRF 序列化器
│   ├── views.py                      # API 视图
│   ├── urls.py                       # 路由配置
│   ├── consumers.py                  # WebSocket 消费者（实时推送）
│   ├── routing.py                    # WebSocket 路由
│   ├── services/                     # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── browser_use_service.py    # browser_use Agent 封装
│   │   ├── test_executor_service.py  # 测试执行服务
│   │   ├── report_generator.py       # 报告生成服务
│   │   └── websocket_service.py      # WebSocket 广播服务
│   ├── browser_use/                  # browser_use 源码（git clone）
│   │   └── (browser_use 项目代码)
│   ├── migrations/
│   └── tests/
```

#### 前端结构
```
VUE3/src/modules/ui-automation/       # UI自动化模块（新建）
├── api/                              # API 调用封装
│   ├── index.ts
│   ├── project.ts                    # 项目管理 API
│   ├── testCase.ts                   # 测试用例 API
│   └── report.ts                     # 报告 API
├── types/                            # TypeScript 类型定义
│   ├── index.ts
│   ├── project.ts
│   ├── testCase.ts
│   └── report.ts
├── stores/                           # Pinia 状态管理
│   ├── project.ts
│   ├── testCase.ts
│   └── execution.ts
├── components/                       # 业务组件
│   ├── NaturalLanguageEditor.vue     # 自然语言编辑器
│   ├── ExecutionMonitor.vue          # 执行监控面板
│   └── ReportViewer.vue              # 报告查看器
├── views/                            # 页面视图
│   ├── Dashboard.vue                 # 仪表盘
│   ├── ProjectList.vue               # 项目列表
│   ├── TestCaseList.vue              # 测试用例列表
│   └── ReportDetail.vue              # 报告详情
└── utils/                            # 工具函数
```

### 2.3 数据模型设计

```python
# 核心数据模型（ui_ 前缀）

class UiTestProject(models.Model):
    """UI测试项目"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    base_url = models.URLField(help_text="被测应用基础URL")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class UiTestCase(models.Model):
    """UI测试用例（自然语言）"""
    project = models.ForeignKey(UiTestProject, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    # 核心字段：自然语言描述
    natural_language_task = models.TextField(
        help_text="用自然语言描述测试任务，如：打开首页，搜索'手机'，验证搜索结果不为空"
    )
    expected_result = models.TextField(blank=True)
    tags = models.JSONField(default=list, help_text="标签")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class UiTestExecution(models.Model):
    """UI测试执行记录"""
    project = models.ForeignKey(UiTestProject, on_delete=models.CASCADE)
    test_case = models.ForeignKey(UiTestCase, on_delete=models.CASCADE)
    status = models.CharField(choices=[
        ('pending', '待执行'),
        ('running', '执行中'),
        ('passed', '通过'),
        ('failed', '失败'),
        ('error', '错误'),
    ])
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True)

class UiTestReport(models.Model):
    """UI测试报告"""
    execution = models.OneToOneField(UiTestExecution, on_delete=models.CASCADE)
    # browser_use 执行历史
    agent_history = models.JSONField(help_text="Agent执行步骤历史")
    screenshots = models.JSONField(help_text="截图路径列表")
    duration_seconds = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 三、核心功能设计

### 3.1 功能清单

| 模块 | 功能 | 优先级 | 说明 |
|------|------|--------|------|
| **项目管理** | 项目 CRUD | P0 | 创建/查看/编辑/删除 UI 测试项目 |
| **项目管理** | 项目配置 | P0 | 配置基础 URL、浏览器选项、LLM 配置 |
| **用例管理** | 自然语言编辑器 | P0 | Markdown 风格编辑器，支持实时预览 |
| **用例管理** | 用例 CRUD | P0 | 创建/查看/编辑/删除测试用例 |
| **用例管理** | 用例模板 | P1 | 预置常见测试场景模板（登录、搜索、下单等） |
| **执行引擎** | browser_use 封装 | P0 | Agent 服务封装，支持同步/异步执行 |
| **执行引擎** | 实时日志推送 | P0 | WebSocket 推送执行步骤和截图 |
| **执行引擎** | 批量执行 | P1 | 支持按项目/集合批量执行 |
| **报告系统** | 执行历史 | P0 | 记录每次执行的完整信息 |
| **报告系统** | 可视化报告 | P0 | 时间线视图、步骤视图、截图展示 |
| **报告系统** | 报告导出 | P1 | PDF/HTML 格式导出 |

### 3.2 自然语言用例示例

```
# 示例1：电商登录测试
任务描述：
1. 打开电商首页 https://www.example.com
2. 点击右上角登录按钮
3. 输入用户名 test@example.com 和密码 Test123456
4. 点击登录按钮
5. 验证登录成功，页面显示用户名 "TestUser"

# 示例2：搜索功能测试
任务描述：
在首页搜索框输入 "iPhone 15"，点击搜索按钮，
验证搜索结果页面显示至少5个商品，且每个商品标题包含 "iPhone"

# 示例3：购物车测试
任务描述：
1. 登录系统
2. 搜索 "MacBook Pro"
3. 点击第一个商品进入详情页
4. 点击加入购物车
5. 进入购物车页面
6. 验证购物车中存在该商品，数量为1
```

### 3.3 前端页面切换设计

```vue
<!-- 顶部导航栏设计 -->
<el-menu mode="horizontal" :default-active="activeModule">
  <el-sub-menu index="modules">
    <template #title>
      <el-icon><Switch /></el-icon>
      <span>{{ currentModuleName }}</span>
    </template>
    <el-menu-item index="api-automation" @click="switchModule('api')">
      <el-icon><Connection /></el-icon>
      <span>API 测试</span>
    </el-menu-item>
    <el-menu-item index="ui-automation" @click="switchModule('ui')">
      <el-icon><Monitor /></el-icon>
      <span>UI 测试</span>
    </el-menu-item>
    <el-menu-item index="ai-automation" @click="switchModule('ai')" disabled>
      <el-icon><MagicStick /></el-icon>
      <span>AI 测试</span>
    </el-menu-item>
  </el-sub-menu>
</el-menu>
```

---

## 四、browser_use 集成方案

### 4.1 安装配置

```bash
# Python 环境要求
Python >= 3.11

# 安装 browser_use
pip install browser-use

# 安装 Chromium 浏览器
playwright install chromium
```

### 4.2 后端服务封装

```python
# ui_automation/services/browser_use_service.py

from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

class BrowserUseService:
    """browser_use Agent 封装服务"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.browser = None
        self.llm = None

    async def execute_task(
        self,
        task: str,
        base_url: str = None,
        headless: bool = True,
    ) -> dict:
        """
        执行自然语言任务

        Args:
            task: 自然语言任务描述
            base_url: 起始 URL
            headless: 是否无头模式

        Returns:
            执行历史和结果
        """
        try:
            # 初始化浏览器
            self.browser = Browser(
                headless=headless,
            )

            # 初始化 LLM
            self.llm = ChatBrowserUse(
                api_key=self.api_key,
            )

            # 创建 Agent
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser,
            )

            # 执行任务
            history = await agent.run()

            return {
                'success': True,
                'history': history.model_dump(),
                'final_result': history.final_result(),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
        finally:
            if self.browser:
                await self.browser.close()
```

### 4.3 API 接口设计

```
# 项目管理
POST   /api/v1/ui-automation/projects/          # 创建项目
GET    /api/v1/ui-automation/projects/          # 项目列表
GET    /api/v1/ui-automation/projects/{id}/     # 项目详情
PUT    /api/v1/ui-automation/projects/{id}/     # 更新项目
DELETE /api/v1/ui-automation/projects/{id}/     # 删除项目

# 用例管理
POST   /api/v1/ui-automation/test-cases/        # 创建用例
GET    /api/v1/ui-automation/test-cases/        # 用例列表
GET    /api/v1/ui-automation/test-cases/{id}/   # 用例详情
PUT    /api/v1/ui-automation/test-cases/{id}/   # 更新用例
DELETE /api/v1/ui-automation/test-cases/{id}/   # 删除用例

# 执行管理
POST   /api/v1/ui-automation/executions/        # 创建执行
POST   /api/v1/ui-automation/executions/{id}/run/  # 运行测试
GET    /api/v1/ui-automation/executions/{id}/   # 执行详情
POST   /api/v1/ui-automation/executions/{id}/cancel/  # 取消执行

# 报告管理
GET    /api/v1/ui-automation/reports/           # 报告列表
GET    /api/v1/ui-automation/reports/{id}/      # 报告详情
GET    /api/v1/ui-automation/reports/{id}/export/  # 导出报告
```

---

## 五、开发进度跟踪

### 5.1 当前状态

| 阶段 | 状态 | 完成度 | 说明 |
|------|------|--------|------|
| 需求对接 | ✅ 已完成 | 100% | 头脑风暴完成，所有决策已确认 |
| 环境验证 | ⏸️ 等待用户 | 0% | 等待用户配置 .env 并验证 browser_use |
| 后端开发 | ⚪ 未开始 | 0% | |
| 前端开发 | ⚪ 未开始 | 0% | |
| 测试验证 | ⚪ 未开始 | 0% | |

### 5.2 详细开发计划

> **重要说明**：本计划于 2026-01-20 确定，后续开发严格按此计划执行，进度实时更新。

---

#### 📍 阶段 1：环境验证 (等待用户触发)

**状态**: ⏸️ 等待用户配置 .env 并验证 browser_use

**前置条件**:
- [ ] 用户配置 `browser-use-0.11.2\.env` 文件 (LLM API Key)
- [ ] 用户成功运行 browser_use 示例
- [ ] 用户通知"开始开发"

**本阶段任务**:
1. [ ] 验证 browser_use 可正常运行
2. [ ] 测试 LLM 连接
3. [ ] 确认 Chromium 浏览器已安装
4. [ ] 记录环境配置信息

**完成后状态**: ✅ 环境就绪，进入阶段 2

---

#### 📍 阶段 2：后端基础框架

**状态**: ⚪ 未开始

**任务清单**:
1. [ ] 创建 `ui_automation` Django 模块目录结构
2. [ ] 设计数据模型 (UiTestProject, UiTestCase, UiTestExecution, UiTestReport)
3. [ ] 创建数据库迁移文件
4. [ ] 创建序列化器 (serializers.py)
5. [ ] 创建 API 视图 (views.py)
6. [ ] 配置 URL 路由 (urls.py)
7. [ ] 注册到 Django settings

**完成后状态**: ✅ 后端框架就绪，API 可访问

---

#### 📍 阶段 3：browser_use 集成

**状态**: ⚪ 未开始

**任务清单**:
1. [ ] 封装 BrowserUseService (`services/browser_use_service.py`)
2. [ ] 实现测试执行服务 (`services/test_executor_service.py`)
3. [ ] 实现 WebSocket 推送服务 (`services/websocket_service.py`)
4. [ ] 实现报告生成服务 (`services/report_generator.py`)
5. [ ] 创建执行 API 端点
6. [ ] 集成 browser_use Agent 调用
7. [ ] 测试完整执行流程

**完成后状态**: ✅ 可执行 UI 测试并生成报告

---

#### 📍 阶段 4：前端开发

**状态**: ⚪ 未开始

**任务清单**:

**4.1 基础架构**
1. [ ] 创建 `ui-automation` 模块目录结构
2. [ ] 创建 API 客户端 (`api/index.ts`, `api/project.ts`, `api/testCase.ts`, `api/execution.ts`)
3. [ ] 创建 TypeScript 类型定义 (`types/*.ts`)
4. [ ] 创建 Pinia 状态管理 (`stores/*.ts`)

**4.2 模块切换**
5. [ ] 实现顶部 Tab 切换 (API/UI 测试模块切换)
6. [ ] 更新主路由配置

**4.3 核心页面**
7. [ ] 创建项目列表页面 (`views/ProjectList.vue`)
8. [ ] 创建项目详情页面 (`views/ProjectDetail.vue`)
9. [ ] 创建测试用例列表页面 (`views/TestCaseList.vue`)
10. [ ] 创建测试用例详情页面 (`views/TestCaseDetail.vue`)
11. [ ] 创建执行监控页面 (`views/ExecutionMonitor.vue`)

**4.4 核心组件**
12. [ ] 开发自然语言 Markdown 编辑器组件 (`components/NaturalLanguageEditor.vue`)
13. [ ] 开发执行状态显示组件 (`components/ExecutionStatus.vue`)
14. [ ] 开发报告查看器组件 (`components/ReportViewer.vue`)

**完成后状态**: ✅ 前端功能完整，可操作测试

---

#### 📍 阶段 5：联调测试

**状态**: ⚪ 未开始

**任务清单**:
1. [ ] 端到端功能测试
2. [ ] 创建测试用例文档 (`test_case/ui_automation_测试用例.md`)
3. [ ] 修复发现的问题
4. [ ] 性能优化
5. [ ] 更新 project_info.md 记录 UI 模块完成状态

**完成后状态**: ✅ UI 自动化模块完成

---

### 5.3 里程碑规划

| 里程碑 | 状态 | 预期触发条件 |
|--------|------|-------------|
| **M0**: 需求确认完成 | ✅ 已完成 | 用户确认所有技术方案 |
| **M1**: 环境验证通过 | ⏸️ 等待 | 用户通知 browser_use 调试成功 |
| **M2**: 后端 API 就绪 | ⚪ 未开始 | 阶段 2 完成 |
| **M3**: browser_use 集成完成 | ⚪ 未开始 | 阶段 3 完成 |
| **M4**: 前端开发完成 | ⚪ 未开始 | 阶段 4 完成 |
| **M5**: 联调测试通过 | ⚪ 未开始 | 阶段 5 完成 |

---

### 5.4 进度更新日志

| 日期 | 事件 | 状态 |
|------|------|------|
| 2026-01-20 | 创建 ui_project_info.md，完成需求对接 | ✅ |
| 2026-01-20 | 用户确认开发计划 | ✅ |
| 2026-01-20 | 等待用户配置 .env 并验证 browser_use | ⏸️ |

---

## 六、需求对接决策记录 (2026-01-20)

### 6.1 已确定的技术方案

| 决策项 | 确定方案 | 说明 |
|--------|----------|------|
| **browser_use 部署** | 本地源码 | 路径：`D:\AI\AI-test-project\Django_project\ui_automation\browser-use-0.11.2` |
| **Python 环境** | 本地 Python 3.12 | 路径：`D:\Python3.12\python.exe` |
| **依赖管理** | uv (推荐方式) | 使用 `uv init` 初始化，`uv add browser-use` 安装 |
| **LLM 模型** | 用户手动配置 | 配置文件：`browser-use-0.11.2\.env` (用户自行填写 API Key) |
| **前端模块切换** | Tab 式 | Element Plus `el-tabs` 风格 |
| **自然语言编辑器** | 增强 Markdown 编辑器 | 支持实时预览、语法高亮 |
| **执行监控** | 时间 + 进度估算 | WebSocket 实时推送 |
| **报告存储** | 本地文件，永久保存 | 报告生成后前端直接链接显示 |
| **模板库** | 暂不需要 | MVP 阶段不实现 |
| **批量执行** | 串行执行 | MVP 阶段单用例串行 |
| **浏览器模式** | 用户可选 | 执行时下拉选择无头/有头模式 |

### 6.2 技术环境配置

**browser_use 路径结构**
```
D:\AI\AI-test-project\Django_project\ui_automation\
├── browser-use-0.11.2/          # browser_use 源码
│   ├── .env                      # LLM API 配置 (用户填写)
│   ├── .venv/                    # 虚拟环境
│   ├── browser_use/              # 核心代码
│   └── README.md                 # 官方文档
└── (待创建的 Django 模块)
```

**快速启动命令** (browser_use 官方推荐)
```bash
# 进入 browser_use 目录
cd D:\AI\AI-test-project\Django_project\ui_automation\browser-use-0.11.2

# 安装 Chromium 浏览器
uvx browser-use install

# 测试运行示例
python -c "from browser_use import Agent, Browser, ChatBrowserUse; import asyncio; ..."
```

### 6.3 前端 Tab 切换设计

```vue
<!-- 顶部模块切换 Tab -->
<el-tabs v-model="activeModule" @tab-change="handleModuleChange">
  <el-tab-pane label="API 测试" name="api-automation">
    <ApiAutomationModule />
  </el-tab-pane>
  <el-tab-pane label="UI 测试" name="ui-automation">
    <UiAutomationModule />
  </el-tab-pane>
  <el-tab-pane label="AI 测试" name="ai-automation" disabled>
    <span class="text-gray-400">（规划中）</span>
  </el-tab-pane>
</el-tabs>
```

### 6.4 执行流程设计

```
用户操作流程：
1. 前端填写自然语言任务
2. 选择浏览器模式（无头/有头）
3. 点击执行
   ↓
4. 后端创建执行记录
5. 调用 browser_use Agent
6. WebSocket 实时推送进度
   ↓
7. Agent 执行完成
8. 生成报告到本地 (HTML/JSON)
9. 前端显示报告链接
```

---

## 七、风险与挑战

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| browser_use 兼容性问题 | 高 | 充分测试，准备好备选方案（Selenium/Playwright） |
| LLM API 成本 | 中 | 提供本地模型选项，优化 Prompt 减少 Token 消耗 |
| 执行稳定性 | 中 | 完善重试机制，提供详细错误日志 |
| 资源消耗 | 中 | 无头模式 + 并发控制 + 定期清理 |

---

## 八、后续行动

- [ ] 与用户确认上述需求文档
- [ ] 讨论头脑风暴中的技术问题
- [ ] 确定开发优先级和里程碑
- [ ] 创建 OpenSpec 变更提案

---

*文档维护：本文档将在需求对接阶段持续更新*
