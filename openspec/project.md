# Project Context

## Purpose
AI自动化测试平台是一款基于前后端分离架构的自动化测试解决方案，专注于提供全面的API自动化测试能力。项目采用模块化设计，包含三个核心模块：API自动化测试、UI自动化测试和AI自动化测试。当前专注于**API自动化测试模块**的完整实现。

核心价值：
- **提高测试效率**：自动化执行重复性测试任务
- **降低测试成本**：减少人工测试投入，提高测试覆盖率
- **增强测试质量**：标准化测试流程，减少人为错误
- **数据驱动决策**：详细的测试报告和数据分析

## Tech Stack

### 后端技术
- **框架**: Django 3.2.13 + Django REST Framework 3.14+
- **数据库**: MySQL 8.0+ (当前使用SQLite开发)
- **认证**: Token认证 + Session认证
- **API文档**: drf-yasg (Swagger/OpenAPI)
- **WebSocket**: Django Channels (实时推送已实现)
- **任务队列**: Celery (待集成)

### 前端技术
- **框架**: Vue 3.3.4 + Composition API
- **语言**: TypeScript 5.0.2
- **UI组件**: Element Plus 2.3.9
- **构建工具**: Vite 4.4.5
- **状态管理**: Pinia 2.1.6
- **路由**: Vue Router 4.2.4
- **HTTP客户端**: Axios 1.5.0
- **图表**: ECharts 5.4.3
- **导出**: jsPDF, html2canvas, xlsx, file-saver
- **其他**: vuedraggable (拖拽排序)

## Project Conventions

### Code Style

#### 后端 (Python)
- 遵循 PEP 8 代码规范
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 所有API端点必须有单元测试
- 测试覆盖率必须 >= 80%
- 使用 `select_related` 和 `prefetch_related` 优化查询
- 实现适当的错误处理和日志记录

#### 前端 (TypeScript/Vue)
- 使用 Vue 3 的 `<script setup>` 语法
- 组件必须使用 PascalCase 命名
- 明确定义 props 和 emits，使用正确的类型
- 所有新代码使用 TypeScript
- 组件文件不应超过 300 行
- 使用 ESLint + Prettier 进行代码格式化
- 实现适当的错误边界

### Architecture Patterns

#### 模块隔离
- **严格的模块隔离**：三个模块完全独立，可单独开发、测试、部署
- **数据隔离**：每个模块使用独立的数据表前缀 (api_, ui_, ai_)
- **接口隔离**：独立的API路由前缀，避免冲突

#### API自动化模块规范
- 数据模型：使用 `api_` 前缀命名所有数据库表
- API路由：必须使用 `/api/v1/api-automation/` 前缀
- 前端路由：必须使用 `/api-automation/*` 命名空间
- 不允许跨模块代码共享

#### RESTful API 约定
- 使用复数名词作为URL：`/api/v1/api-automation/test-cases/`
- HTTP方法：GET (检索), POST (创建), PUT (更新), DELETE (删除)
- 标准响应格式：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```
- 所有列表端点必须支持分页

### Testing Strategy

#### TDD（测试驱动开发）优先
所有**新功能开发**和**非紧急Bug修复**，必须遵循TDD流程：
1. 充分分析需求，编写功能文档和测试用例文档
2. 严格按照功能文档进行开发
3. 开发完成后根据测试用例进行完整且细致的测试

#### 后端测试
```bash
# 运行所有测试
python manage.py test

# 运行特定模块测试
python manage.py test api_automation

# 运行带覆盖率的测试
coverage run --source='.' manage.py test
coverage report
```

#### 前端测试
```bash
# 运行单元测试
npm run test

# 运行E2E测试
npm run test:e2e

# 运行带覆盖率的测试
npm run test:coverage
```

### Git Workflow

#### 分支策略
- 使用 GitHub Flow 模型
- 主分支：`main`
- 功能分支：`feature/description`
- Bug修复分支：`bugfix/description`
- 热修复分支：`hotfix/description`

#### 提交消息格式
遵循 Conventional Commits：
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档变更
- `style`: 代码风格变更（格式化等）
- `refactor`: 代码重构
- `test`: 测试添加或变更
- `chore`: 维护任务

示例：
```
feat(api-automation): add test case execution feature

- Implement test case executor service
- Add API endpoint for running tests
- Create frontend component for test execution
```

## Domain Context

### 核心数据模型 (11个)
```
ApiProject              # 测试项目管理
ApiCollection           # API集合管理
ApiTestCase            # 测试用例管理
ApiTestEnvironment     # 测试环境配置
ApiTestExecution       # 测试执行记录
ApiTestReport          # 测试报告
ApiTestResult          # 测试结果详情
ApiDataDriver          # 数据驱动测试
ApiTestCaseAssertion   # 测试断言配置
ApiTestCaseExtraction  # 数据提取配置
ApiUserGlobalVariable  # 用户全局变量
```

### 变量系统
支持4种变量类型：
- `${env.base_url}` - 环境变量（当前环境）
- `${global.token}` - 全局变量（所有测试）
- `${local.user_id}` - 局部变量（当前用例）
- `${extract.user.id}` - 提取变量（后续用例）

### 断言引擎
- **11种断言类型**: status_code, response_time, response_body, response_headers, json_value, text_contains, json_schema, full_json, json_array, array_length, is_empty
- **13种操作符**: equals, not_equals, contains, not_contains, greater_than, less_than, between, starts_with, ends_with, matches, exists, is_null, is_not_null

### 数据提取引擎
- **6种提取类型**: regex, json_path, xpath, css_selector, header, cookie
- 变量作用域管理 (local/global)
- 默认值支持

## Important Constraints

### 端口固定约束
- **后端服务地址固定为**: `http://127.0.0.1:8000/`
- **前端服务地址固定为**: `http://localhost:3000/`
- 如果端口被占用，必须先kill掉占用进程再重新启动

### 模块开发约束
- **当前仅开发API自动化模块**
- UI和AI自动化模块保持为预留目录（仅包含.gitkeep文件）
- 不允许跨模块代码共享
- 每个模块必须独立可部署

### 数据库约束
- 所有表必须有 `created_at` 和 `updated_at` 字段
- 使用外键约束保证数据完整性
- 为频繁查询的字段添加索引
- 支持软删除（`is_deleted` 字段）

### 性能约束
- 使用数据库索引优化查询
- 优化查询避免N+1问题
- 实现缓存策略（Redis + 应用缓存）
- 对大数据集使用分页
- 实现异步处理长时间任务

## External Dependencies

### 后端依赖
- Django 3.2.13 - Web框架
- Django REST Framework 3.14+ - API框架
- drf-yasg - Swagger/OpenAPI文档
- Django Channels - WebSocket支持
- MySQL 8.0+ - 生产数据库
- Celery (待集成) - 异步任务队列
- Redis (待集成) - 缓存和消息队列

### 前端依赖
- Vue 3.3.4 - 前端框架
- Element Plus 2.3.9 - UI组件库
- Pinia 2.1.6 - 状态管理
- ECharts 5.4.3 - 图表库
- Axios 1.5.0 - HTTP客户端
- Vite 4.4.5 - 构建工具

### 开发工具
- OpenSpec - 规范驱动开发工具
- Black - Python代码格式化
- ESLint/Prettier - 前端代码格式化
- Coverage - 测试覆盖率工具

## OpenSpec Integration

本项目使用 OpenSpec 进行规范驱动开发。所有新功能开发、重大变更、架构调整都需要遵循 OpenSpec 工作流：

1. **创建变更提案**：在 `openspec/changes/` 下创建提案
2. **编写规格增量**：使用 ADDED/MODIFIED/REMOVED 格式
3. **验证提案**：使用 `openspec validate --strict`
4. **实施变更**：按照 tasks.md 逐步实施
5. **归档变更**：部署后使用 `openspec archive`

详细流程参见 `openspec/AGENTS.md`。
