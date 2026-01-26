<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

本项目使用 OpenSpec 进行规范驱动开发。**所有新功能开发、重大变更、架构调整都必须遵循 OpenSpec 工作流**。

## OpenSpec 工作流概览

### 何时需要创建 OpenSpec 提案

创建 OpenSpec 变更提案当请求涉及：
- 新功能或能力添加
- 破坏性变更（API、数据库 schema）
- 架构模式变更
- 性能优化（改变行为）
- 安全模式更新

### 何时跳过 OpenSpec 提案

以下情况可以直接实施，无需创建提案：
- Bug 修复（恢复预期行为）
- 拼写错误、格式、注释修改
- 非破坏性依赖更新
- 配置变更
- 现有行为的测试添加

### OpenSpec 三阶段工作流

#### 阶段 1: 创建变更提案 (openspec proposal)
1. 查看 `openspec/project.md`, `openspec list`, `openspec list --specs` 了解当前上下文
2. 选择唯一的动词引导的 `change-id` (如 add-xxx, update-xxx, remove-xxx)
3. 在 `openspec/changes/<id>/` 下创建提案文件
4. 编写规格增量，使用 ADDED/MODIFIED/REMOVED/RENAMED Requirements 格式
5. 每个需求必须包含至少一个 Scenario（使用 `#### Scenario:` 格式）
6. 运行 `openspec validate <id> --strict` 验证并修复问题

#### 阶段 2: 实施变更 (openspec apply)
1. 阅读 `proposal.md` 了解要构建什么
2. 阅读 `design.md`（如果存在）审查技术决策
3. 阅读 `tasks.md` 获取实施检查清单
4. 按顺序实施任务
5. 完成后更新 `tasks.md` 中的检查清单

#### 阶段 3: 归档变更 (openspec archive)
部署后，创建单独的 PR：
- 将 `changes/[name]/` 移动到 `changes/archive/YYYY-MM-DD-[name]/`
- 更新 `specs/` 中的能力定义
- 运行 `openspec validate --strict` 确认归档通过检查

### 常用 OpenSpec 命令

```bash
# 列出活跃的变更
openspec list

# 列出规格
openspec list --specs

# 查看详情
openspec show [item]

# 验证变更
openspec validate [change-id] --strict

# 归档变更
openspec archive <change-id> --yes
```

### 参考文档

- `openspec/AGENTS.md` - 完整的 OpenSpec 指令
- `openspec/project.md` - 项目上下文和约定

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 重要规则

- 优先使用简体中文
- 重启前端服务不要修改IP，IP固定为：**http://localhost:3000/**。如何当前IP被占用，请kill掉占用后重新启动。必须永远前端地址为：**http://localhost:3000/**
- 后端服务地址固定为：http://127.0.0.1:8000/， 同样如果有占用时，先kill再重新启动
- 后端代码改动后，如涉及模型变更需要执行数据库迁移
- **禁止使用Write工具覆盖整个文件**。如必须使用Write工具覆盖全文，请在覆盖前先备份该文件，在覆盖完成后经过用户测试确认没问题后，可删除备份文件。

## 重要文档

- **项目说明文档**: project_info.md - 完整的项目概述、技术架构、功能模块、开发进度
- **操作说明文档**: README.md
- **开发文档**: ./develop_document - 各功能模块的设计文档和实现思路
- **测试文档**: ./test_case - 测试用例和测试报告

## 设计系统 (重要)

本项目采用**简约科技风格**设计系统，浅色主题。

### 设计令牌
- **配色**: 纯净白 (#FFFFFF) + 科技蓝 (#007AFF) + 清新绿 (#34C759)
- **字体**: IBM Plex Sans (标题) + JetBrains Mono (代码)
- **文件位置**:
  - `VUE3/src/assets/styles/design-tokens.css` - CSS设计令牌
  - `VUE3/src/assets/styles/global.css` - 全局样式和工具类
  - `VUE3/src/assets/styles/element-plus-overrides.css` - Element Plus主题覆盖

### 设计原则
- 使用 CSS Variables 定义颜色、字体、间距、动画
- Spring缓动函数 + 数据流动画效果
- 高对比度文字层次，微妙阴影和圆角
- 响应式设计，移动端适配

## 新功能/需求开发:TDD（Test-Driven Development，测试驱动开发）优先

在本项目中，所有**新功能开发**和**非紧急 Bug 修复**，Claude Code 必须尽量遵循
**TDD（Test-Driven Development，测试驱动开发）** 流程。

1. 充分分析和思考需求需要实现的功能会包含哪些,优先编写功能文档和测试用例文档
2. 编写完功能文档和测试用例后,严格按照功能文档进行开发
3. 开发完成后根据测试用例进行完整且细致的测试

## 开发/功能文档编写(重要)

- 在进行功能开发前，需要充分分析需求并编写功能文档和测试用例：`D:\AI\AI-test-project\develop_document\`
- 开发文档按照功能模块进行分类，同一功能的前后端实现写在一个文件下，不同功能则新建文件编写
- 编写格式要求为 markdown
- 仅包含功能和实现思路，无需包含代码
- 前端开发时，优先参考对应的开发文档（`D:\AI\AI-test-project\develop_document\`）和接口文档：**http://127.0.0.1:8000/swagger/**

## 测试用例编写(重要)

- 在分析用户需求和编写功能文档时，需要对需求进行充分分析，并依据分析结果编写完整的测试用例
- 开发完成后需要能满足所有编写测试用例的要求才算成功
- 测试用例和测试报告存放目录：`D:\AI\AI-test-project\test_case\`
- 测试用例同开发文档一样，按照功能进行区分，同一功能的用例写在同一.md文件下
- 编写格式要求为 markdown

## 项目环境说明
- 操作系统：Windows（主要通过 PowerShell 或 CMD 进行操作）
- 请优先使用 **PowerShell 命令**，仅在我明确说明时使用 CMD 或 WSL（Windows Subsystem for Linux，WSL）
- 本项目代码、依赖和脚本默认都位于当前仓库目录及其子目录中

## 总体目标
- 你在本项目中应当作为自动化开发助手，**尽量减少与我的交互次数**
- 能自己连续完成的一组步骤，不要每一步都停下来问我
- 在权限允许的前提下，优先**自动执行安全操作并直接应用变更**

## 执行模式偏好
- 在 Claude Code 中，如无特别说明，请：
  - 优先使用 **Auto-accept mode（自动接受模式）** 应用代码修改
  - 对小范围、本地代码修改，可以直接编辑文件、创建新文件、重命名文件，无需每次征求确认
- 修改完成后，请始终提供：
  - 变更概要（Summary of changes）
  - 关键文件的 diff 摘要
  - 如果运行了测试或构建，请说明执行了哪些命令及结果
- 所有功能实现完成后，都需要进行充分且全面的测试

## Project Overview

This is an AI and Automation Testing Platform with three main modules:
1. **API Automation Testing** (Backend 100% complete, Frontend 100% complete)
2. **UI Automation Testing** (Placeholder only)
3. **AI Automation Testing** (Placeholder only)

**Current Status (2026-01-16)**:
- **Backend (API Automation)**: Fully implemented with 12 core models, complete REST APIs (23+ endpoints), HTTP execution engine, assertion engine (11 types, 13 operators), extraction engine (6 types), WebSocket service, dashboard APIs with data fixes
- **Frontend (API Automation)**: 100% complete with authentication, project management, dashboard with chart visualization (bar/pie charts with click interaction), **15 pages**, 24 components, WebSocket integration, design system (简约科技风格)
- **Testing**: Comprehensive testing completed - A+ rating (100% pass rate), Playwright exploratory testing completed (6 errors fixed)
- **Production Ready**: All core features implemented and tested

### 项目完成度
- **后端完成度**: 100%
- **前端完成度**: 100%
- **设计系统完成度**: 100%
- **项目整体完成度**: 100%
- **测试状态**: 探索性测试通过 (A+)

## Architecture

### Backend (Django + DRF)
- **Location**: `./Django_project/`
- **Framework**: Django 3.2.13 + Django REST Framework 3.14+
- **Database**: SQLite (development), MySQL 8.0+ (production)
- **Python**: Python 3.9+
- **API Documentation**: Swagger/OpenAPI via drf-yasg at `http://127.0.0.1:8000/swagger/`
- **WebSocket**: Django Channels (real-time updates implemented)

### Frontend (Vue 3)
- **Location**: `./VUE3/`
- **Framework**: Vue 3.3.4 with TypeScript 5.0.2
- **UI Library**: Element Plus 2.3.9
- **Build Tool**: Vite 4.4.5
- **State Management**: Pinia 2.1.6
- **Router**: Vue Router 4.2.4
- **Charts**: ECharts 5.4.3
- **Design System**: 简约科技风格 (浅色主题)
  - design-tokens.css, global.css, element-plus-overrides.css
  - 配色: 纯净白 + 科技蓝 + 清新绿
- **Current Dev Server**: `http://localhost:3000/` (must always use this port)

## Development Commands

### Backend Commands (Django)
```bash
# Navigate to Django project
cd Django_project

# Run development server (固定端口: 127.0.0.1:8000)
python manage.py runserver 127.0.0.1:8000

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Check for issues
python manage.py check
```

### Frontend Commands (Vue 3)
```bash
# Navigate to Vue project
cd VUE3

# Install dependencies
npm install

# Run development server (固定端口: localhost:3000)
npm run dev -- --host localhost --port 3000

# Build for production
npm run build

# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Type checking
npm run type-check
```

## Module Development Rules

### Strict Module Isolation
- API Automation module: Use `api_` prefix for all database tables
- API routes: Must use `/api/v1/api-automation/` prefix
- Frontend routes: Must use `/api-automation/*` namespace
- NO cross-module code sharing allowed
- Each module must be independently deployable

### Current Development Focus
**API Automation Testing module is now 100% complete.** The UI and AI automation modules should remain as placeholder directories with `.gitkeep` files only.

**Latest Completed Features (2025-12-25)**:
1. ✅ Dashboard data statistics fix (total_cases = passed + failed + skipped + error)
2. ✅ Environment/Collection dimension reports filtering (only show items with execution records)
3. ✅ Chart visualization (ECharts bar chart and pie chart)
4. ✅ Chart click interaction (click to filter test results)
5. ✅ Report export functionality (PDF/Excel/CSV/JSON/图片)
6. ✅ Batch operations interface (execute, export, delete)
7. ✅ WebSocket real-time updates (complete implementation)
8. ✅ Enhanced test case editor with request builder and cURL import

**Optional Enhancements**:
- Unit tests and E2E tests
- Performance optimization
- CI/CD pipeline setup

### Key Directory Structure for API Automation Module

#### Backend (100% Complete)
```
Django_project/api_automation/
├── models.py               # 12 core data models
│   ├── ApiProject         # Test project management
│   ├── ApiCollection      # API collection management
│   ├── ApiTestCase       # Test case management
│   ├── ApiTestEnvironment # Test environment management
│   ├── ApiTestExecution  # Test execution records
│   ├── ApiTestReport     # Test reports
│   ├── ApiTestResult     # Detailed test results
│   ├── ApiDataDriver     # Data-driven testing
│   ├── ApiTestCaseAssertion # Assertion configuration
│   ├── ApiTestCaseExtraction # Data extraction configuration
│   ├── ApiUserGlobalVariable # User global variables
│   └── ApiHttpExecutionRecord # HTTP execution records
├── serializers.py          # API serializers for all models
├── views.py                # ViewSets with CRUD + custom actions
│   └── DashboardViewSet   # Dashboard statistics and reports (with data fixes)
├── urls.py                 # Module URL routing
├── consumers.py            # WebSocket consumers ✅
├── routing.py              # WebSocket routing ✅
├── services/               # Business logic services
│   ├── http_executor.py    # HTTP request executor ✅
│   ├── assertion_engine.py # Assertion engine (11 types, 13 operators) ✅
│   ├── extraction_engine.py # Data extraction engine (6 types) ✅
│   ├── websocket_service.py # WebSocket broadcast service ✅
│   └── cascade_delete_service.py # Cascade delete service ✅
└── migrations/             # Database migrations
```

#### Frontend (100% Complete)
```
VUE3/src/modules/api-automation/
├── components/           # Module-specific components (24 components)
│   ├── Layout/          # Layout components ✅
│   ├── Project/         # Project management components ✅
│   ├── Auth/            # Authentication components ✅
│   ├── Environment/     # Environment components ✅
│   ├── HttpExecutor/    # HTTP executor components (7 sub-components) ✅
│   ├── TestExecutor.vue # Test executor ✅ (17KB)
│   ├── TestCaseRunner.vue # Case runner ✅ (16KB)
│   ├── AssertionConfig.vue # Assertion config ✅ (enhanced with 12 templates, batch ops, drag-sort)
│   ├── DataDrivenConfig.vue # Data-driven config ✅ (enhanced with preview, variable mapping)
│   ├── VariableExtraction.vue # Variable extraction ✅ (enhanced with expression testing, 9 templates)
│   ├── ReportViewer.vue # Report viewer ✅ (16KB)
│   ├── EnhancedReportViewer.vue # Enhanced report viewer ✅ (ECharts charts, export)
│   └── RealtimeExecutionStatus.vue # Real-time execution status ✅ (2089 lines, with charts, shortcuts, complete WebSocket integration)
├── views/               # Module pages (15 pages)
│   ├── Auth/Login.vue   # Login/Register page ✅
│   ├── Dashboard/       # Dashboard ✅ (with bar/pie charts, click interaction)
│   ├── Project/         # Project pages ✅ (list, detail)
│   ├── Collection/      # Collection pages ✅ (list, detail)
│   ├── TestCase/        # API test pages ✅ (list, detail, create)
│   ├── Environment/     # Environment pages ✅ (list)
│   ├── HttpExecutor/    # HTTP executor page ✅
│   ├── HttpExecutor/    # HTTP execution records page ✅
│   ├── Reports/         # Report pages ✅ (list, detail)
│   └── RecycleBin/      # Recycle bin page ✅
├── stores/              # Pinia stores for module state (8 stores) ✅
├── api/                 # API calls (12 API files) ✅
│   ├── auth.ts
│   ├── project.ts
│   ├── collection.ts
│   ├── test-case.ts
│   ├── environment.ts
│   ├── execution.ts
│   ├── report.ts
│   ├── dashboard.ts
│   ├── assertion.ts
│   ├── extraction.ts
│   ├── httpExecutor.ts
│   └── recycleBin.ts
├── types/               # TypeScript type definitions (8 type files) ✅
│   ├── project.ts
│   ├── collection.ts
│   ├── testCase.ts
│   ├── environment.ts
│   ├── execution.ts
│   ├── report.ts
│   ├── dataDriver.ts
│   └── http.ts
└── utils/               # Module utilities ✅

VUE3/src/assets/styles/   # Design system ✅
├── design-tokens.css    # CSS design tokens (简约科技风格)
├── global.css           # Global styles and utilities
└── element-plus-overrides.css # Element Plus theme overrides
```

## API Design Standards

### RESTful API Conventions
- Use plural nouns for URLs: `/api/v1/api-automation/test-cases/`
- HTTP methods: GET (retrieve), POST (create), PUT (update), DELETE (remove)
- Standard response format:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
  ```
- All list endpoints must support pagination with format:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "count": 100,
      "next": "http://api.example.com/test-cases/?page=3",
      "previous": "http://api.example.com/test-cases/?page=1",
      "results": []
    }
  }
  ```

### Authentication
- Token-based authentication with 30-minute expiration
- Token stored in localStorage on frontend
- Automatic token refresh implementation
- All endpoints validate permissions

## Database Design Rules

- Table names: lowercase with underscores, use plural form (e.g., `api_test_cases`)
- All tables must have `created_at` and `updated_at` fields
- Use foreign key constraints for data integrity
- Add indexes for frequently queried fields
- Use `api_` prefix for all API automation module tables
- Support soft deletion with `is_deleted` field

## Code Quality Standards

### Backend (Python)
- Follow PEP 8 strictly
- Use Black for code formatting
- Use isort for import sorting
- All API endpoints must have unit tests
- Test coverage must be ≥80%
- Use `select_related` and `prefetch_related` for query optimization
- Implement proper error handling and logging

### Frontend (TypeScript/Vue)
- Use `<script setup>` syntax for Vue 3 components
- Components must be PascalCase
- Define props and emits explicitly with proper types
- Use TypeScript for all new code
- Component files should not exceed 300 lines
- Use ESLint + Prettier for code formatting
- Implement proper error boundaries

## Performance Requirements

### Backend Performance
- Use database indexes effectively
- Optimize queries to avoid N+1 problems
- Implement caching strategy (Redis + application cache)
- Use pagination for large datasets
- Implement async processing for long-running tasks
- Monitor and optimize slow queries

### Frontend Performance
- Implement lazy loading for route components
- Use code splitting effectively
- Optimize images (compress, use WebP format)
- Implement API request caching where appropriate
- Minimize bundle size through tree shaking

## Testing Requirements

### Backend Testing
```bash
# Run all tests
python manage.py test

# Run specific module tests
python manage.py test api_automation

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report

# Run specific test file
python manage.py test api_automation.tests.test_models

# Run custom test scripts
python test_dashboard.py        # Backend data model tests
python test_dashboard_api.py    # API endpoint tests
```

### Frontend Testing
```bash
# Run unit tests
npm run test

# Run E2E tests
npm run test:e2e

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test ApiCollectionManager.spec.ts
```

## Git Workflow

### Branch Strategy
- Use GitHub Flow model
- Main branch: `main`
- Feature branches: `feature/description`
- Bugfix branches: `bugfix/description`
- Hotfix branches: `hotfix/description`

### Commit Message Format
Follow Conventional Commits:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

Example:
```
feat(api-automation): add test case execution feature

- Implement test case executor service
- Add API endpoint for running tests
- Create frontend component for test execution
```

### Code Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Error handling is implemented

## Deployment

### Backend Deployment
- Use Gunicorn as WSGI server
- Use Nginx as reverse proxy
- Docker containerization required
- Support multiple environments (dev/staging/prod)
- Use environment variables for configuration

### Frontend Deployment
- Build optimization for production
- CDN for static assets
- Environment variable configuration
- Docker containerization

## Common Development Workflows

### Adding New API Endpoint
1. Create/update model in `Django_project/api_automation/models.py`
2. Run `python manage.py makemigrations api_automation`
3. Run `python manage.py migrate`
4. Create/update serializer in `Django_project/api_automation/serializers.py`
5. Create/update view in `Django_project/api_automation/views.py`
6. Add URL in `Django_project/api_automation/urls.py`
7. Create/update API file in `VUE3/src/modules/api-automation/api/`
8. Create/update TypeScript types in `VUE3/src/modules/api-automation/types/`
9. Add/update frontend components/views as needed
10. Write tests for both backend and frontend
11. Update documentation

### Database Migration Workflow
```bash
# After model changes
python manage.py makemigrations api_automation

# Review the generated migration file
# Apply migration
python manage.py migrate

# For production, use:
python manage.py migrate --settings=config.settings.production
```

### Adding New Frontend Component
1. Create component in appropriate module directory
2. Use TypeScript with proper prop/emit definitions
3. Follow single-responsibility principle
4. Add unit tests if component is complex
5. Export from module's index file if needed
6. Update documentation

### Restarting Services

**重启后端服务（端口固定为 127.0.0.1:8000）:**
```bash
# 1. 找到占用端口的进程
netstat -ano | findstr ":8000" | findstr "LISTENING"

# 2. Kill掉占用进程（假设PID为1234）
taskkill /F /PID 1234
# 或使用 PowerShell
powershell -Command "Stop-Process -Id 1234 -Force"

# 3. 重新启动后端
cd Django_project
python manage.py runserver 127.0.0.1:8000
```

**重启前端服务（端口固定为 localhost:3000）:**
```bash
# 1. 找到占用端口的进程
netstat -ano | findstr ":3000" | findstr "LISTENING"

# 2. Kill掉占用进程（假设PID为5678）
taskkill /F /PID 5678
# 或使用 PowerShell
powershell -Command "Stop-Process -Id 5678 -Force"

# 3. 重新启动前端
cd VUE3
npm run dev -- --host localhost --port 3000
```

## Important Reminders

1. **NEVER** develop UI or AI automation modules until API module is complete
2. **ALWAYS** use proper module isolation - no cross-module imports
3. **MUST** follow the naming conventions (Api prefix for all API module classes)
4. **REQUIRED** to write tests for all new functionality (≥80% coverage)
5. **MANDATORY** code review before merging any changes
6. **ALWAYS** consider security implications of new code
7. **MUST** optimize for performance (database queries, bundle size)
8. **REQUIRED** to update documentation for API changes

## Current Implementation Status

### Backend (API Automation Module) - ✅ 100% COMPLETE
- [x] 12 core data models with relationships
- [x] Complete REST API with CRUD operations (23+ endpoints)
- [x] HTTP execution engine with variable support
- [x] Assertion engine (11 assertion types, 13 operators)
- [x] Data extraction engine (6 extraction types)
- [x] Dashboard API with data statistics fixes
  - [x] Total cases = passed + failed + skipped + error
  - [x] Pass rate = passed / total cases
  - [x] Environment reports filter (only show with execution records)
  - [x] Collection reports filter (only show with execution records)
- [x] Authentication and authorization
- [x] API documentation (Swagger)
- [x] Soft deletion support
- [x] Clone functionality for projects, collections, and test cases
- [x] Nested routes for assertions and extractions
- [x] Environment connection testing
- [x] Global variables support
- [x] WebSocket service (real-time updates)
- [x] Environment import/export
- [x] Recycle bin functionality (cascade delete preview, restore, permanent delete)

### Frontend (API Automation Module) - ✅ 100% COMPLETE
- [x] Project setup and configuration
- [x] Authentication (login/logout/register)
- [x] Basic layout and navigation
- [x] Design system (简约科技风格 - light minimal tech theme)
  - [x] design-tokens.css, global.css, element-plus-overrides.css
- [x] All 15 pages implemented
  - [x] Login/Register page
  - [x] Dashboard with charts
  - [x] Project list/detail
  - [x] Collection list/detail
  - [x] Test case list/detail/create
  - [x] Environment list
  - [x] HTTP executor
  - [x] HTTP execution records
  - [x] Report list/detail
  - [x] Recycle bin
- [x] Dashboard with enhanced features
  - [x] Statistics cards (clickable to filter)
  - [x] Bar chart (ECharts, click to filter)
  - [x] Pie chart (ECharts, click to filter)
  - [x] Environment dimension reports (Tab labels show count)
  - [x] Collection dimension reports (Tab labels show count)
  - [x] Empty state handling
- [x] API state management (Pinia stores - 8 stores)
- [x] TypeScript types for all models (8 type files)
- [x] API client with error handling (12 API files)
- [x] 24 reusable components
- [x] Assertion config with templates, batch operations, drag-sort
- [x] Variable extraction with expression testing and templates
- [x] Environment management with import/export, connection test
- [x] Real-time execution status with charts and shortcuts
- [x] Report export functionality (PDF/Excel/CSV/JSON/图片)
- [x] Batch operations interface
- [x] WebSocket real-time updates (fully implemented with backend consumers and frontend integration)
- [x] Enhanced test case editor with request builder, code editing, split preview, and cURL import/export

### Playwright Exploratory Testing (2026-01-16)
- [x] All 15 pages tested and verified working
- [x] 6 errors found and fixed
  - [x] HTTP executor import path error
  - [x] Recycle bin route missing
  - [x] HTTP executor request history data type error
  - [x] SaveTestCaseDialog import path error
  - [x] Recycle bin icon import invalid
  - [x] Recycle bin API response handling error

### Optional Enhancements (Priority Order)
1. ~~**Dashboard data fix**~~ - ✅ Complete (COMPLETED)
2. ~~**Chart visualization**~~ - ✅ Complete (COMPLETED)
3. ~~**Chart click interaction**~~ - ✅ Complete (COMPLETED)
4. ~~**WebSocket integration**~~ - ✅ Complete (COMPLETED)
5. ~~**Test case editor**~~ - ✅ Complete (COMPLETED)
6. ~~**Report export**~~ - ✅ Complete (COMPLETED)
7. ~~**Batch operations**~~ - ✅ Complete (COMPLETED)
8. ~~**Design system**~~ - ✅ Complete (COMPLETED)
9. ~~**User registration**~~ - ✅ Complete (COMPLETED)
10. ~~**Recycle bin**~~ - ✅ Complete (COMPLETED)
11. ~~**Playwright testing**~~ - ✅ Complete (COMPLETED)
12. **Unit tests** - Add component and service unit tests
13. **E2E tests** - Add end-to-end testing
14. **Performance optimization** - Caching, query optimization, code splitting

## Feature Highlights

### Assertion Engine (11 types, 13 operators)
Supports 11 assertion types:
- `status_code` - HTTP status code assertions
- `response_time` - Response time validation
- `response_body` - Response body content validation
- `response_headers` - HTTP header assertions
- `json_value` - JSON value extraction and validation
- `text_contains` - Text content validation
- `json_schema` - JSON Schema validation
- `full_json` - Complete JSON response validation
- `json_array` - JSON array validation
- `array_length` - Array length validation
- `is_empty` - Empty value validation

Supports 13 operators:
- `equals`, `not_equals`
- `contains`, `not_contains`
- `greater_than`, `less_than`, `between`
- `starts_with`, `ends_with`
- `matches`, `exists`
- `is_null`, `is_not_null`

### Variable System
Supports variable substitution in requests:
- `${env.base_url}` - Environment variables
- `${global.token}` - Global variables
- `${local.user_id}` - Local/test case variables
- `${extract.user.id}` - Extracted from previous responses

### Data-Driven Testing
- Support for multiple data sources (JSON, CSV, Excel, Database)
- Variable mapping for test parameterization
- Preview functionality for data sources

### Dashboard Features (Latest Updates)
- **Statistics Cards**: Total cases, passed, failed, pass rate (clickable to filter)
- **Bar Chart**: Test execution statistics (click to filter results)
- **Pie Chart**: Test execution distribution (click to filter results)
- **Environment Reports**: Only show environments with execution records
- **Collection Reports**: Only show collections with execution records
- **Tab Labels**: Display case count for easy navigation
- **Empty States**: Friendly messages when no data available
- **Chart Interaction**: Click any chart element to filter test results
- **Real-time Updates**: WebSocket integration for live data

### Component Features
- **AssertionConfig**: 12 assertion templates, batch enable/disable/delete, drag-sort
- **VariableExtraction**: 9 extraction templates, expression testing dialog, help section
- **EnvironmentList**: Statistics cards, batch operations, import/export (JSON), connection test
- **RealtimeExecutionStatus**: Response time chart (ECharts), 10 keyboard shortcuts, WebSocket status indicator
- **Dashboard**: Enhanced with bar/pie charts, click interactions, data fixes

## Testing Summary

### Playwright Exploratory Testing Results (2026-01-16)
**Overall Test Rating: A+ (Excellent)**
**Testing Method**: Automated browser testing with Playwright

#### Errors Found and Fixed (6 errors)
1. ✅ HTTP执行器导入路径错误 - `useHttpExecutor` composable import path fixed
2. ✅ 回收站路由缺失 - Added recycle-bin route to router/index.ts
3. ✅ HTTP执行器请求历史数据类型错误 - Fixed history data type
4. ✅ SaveTestCaseDialog导入路径错误 - Fixed import from `'../types/http'` to `'../../types/http'`
5. ✅ 回收站图标导入无效 - Replaced `ListData` with `Tickets` icon
6. ✅ 回收站API响应处理错误 - Fixed API response handling (removed `.data` from response access)

#### Pages Verified (15/15 passed)
- ✅ Dashboard (仪表盘) - Statistics cards, charts, reports
- ✅ Projects (项目管理) - 6 projects
- ✅ Collections (集合管理) - 1 collection
- ✅ Test Cases (测试用例) - 8 test cases
- ✅ Environment (环境管理) - 5 environments
- ✅ HTTP Executor (HTTP执行器) - Request builder, history
- ✅ Reports (测试报告) - 7 reports
- ✅ Recycle Bin (回收站) - 11 projects, 9 collections, 71 cases, 7 environments

### Comprehensive Testing Results (2025-12-25)
**Overall Test Rating: A+ (Excellent)**

### Backend Tests
- API endpoint tests: 23/23 passed (100%)
- Average response time: ~20ms
- Data model tests: 12 models verified
- Authentication & authorization: Passed
- Swagger documentation: Working correctly
- Dashboard data statistics: Fixed and verified

### Frontend Tests
- Page functionality tests: 15/15 passed (100%)
- Component functionality tests: 24 components passed
- TypeScript coverage: 100%
- API integration tests: 12 modules passed
- WebSocket real-time updates: Working correctly
- Chart visualization tests: Passed
- Chart interaction tests: Passed

### Test Scripts & Reports
- `Django_project/test_dashboard.py` - Backend data validation
- `Django_project/test_dashboard_api.py` - API endpoint testing
- `test_case/PROJECT_TEST_REPORT.md` - Comprehensive test report
- Playwright exploratory test session - 2026-01-16

### Production Readiness
- All core features implemented and tested
- No blocking issues found
- Performance within acceptable ranges
- Ready for production deployment
