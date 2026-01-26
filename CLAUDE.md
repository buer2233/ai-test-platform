<!-- OPENSPEC:START -->
# OpenSpec 指令

本项目使用 OpenSpec 进行规范驱动开发。**所有新功能开发、重大变更、架构调整都必须遵循 OpenSpec 工作流**。

## 工作流概览

### 何时创建 OpenSpec 提案

- 新功能或能力添加
- 破坏性变更（API、数据库 schema）
- 架构模式变更
- 性能优化（改变行为）
- 安全模式更新

### 何时跳过提案

- Bug 修复
- 拼写错误、格式、注释修改
- 非破坏性依赖更新
- 配置变更
- 现有行为的测试添加

### 三阶段工作流

**阶段 1: 创建变更提案 (openspec proposal)**
1. 查看 `openspec/project.md`, `openspec list`, `openspec list --specs` 了解当前上下文
2. 选择唯一的动词引导的 `change-id` (如 add-xxx, update-xxx, remove-xxx)
3. 在 `openspec/changes/<id>/` 下创建提案文件
4. 编写规格增量，使用 ADDED/MODIFIED/REMOVED/RENAMED Requirements 格式
5. 每个需求必须包含至少一个 Scenario（使用 `#### Scenario:` 格式）
6. 运行 `openspec validate <id> --strict` 验证并修复问题

**阶段 2: 实施变更 (openspec apply)**
1. 阅读 `proposal.md` 了解要构建什么
2. 阅读 `design.md`（如果存在）审查技术决策
3. 阅读 `tasks.md` 获取实施检查清单
4. 按顺序实施任务
5. 完成后更新 `tasks.md` 中的检查清单

**阶段 3: 归档变更 (openspec archive)**
部署后，创建单独的 PR：
- 将 `changes/[name]/` 移动到 `changes/archive/YYYY-MM-DD-[name]/`
- 更新 `specs/` 中的能力定义
- 运行 `openspec validate --strict` 确认归档通过检查

### 常用命令

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

# CLAUDE 开发指南

本文件为 Claude Code 提供项目开发工作指导。

## 重要规则

- 优先使用简体中文
- 前端服务地址固定：**http://localhost:3000/**（IP被占用时先kill再重启）
- 后端服务地址固定：**http://127.0.0.1:8000/**（IP被占用时先kill再重启）
- 后端代码改动后，如涉及模型变更需执行数据库迁移
- **禁止使用Write工具覆盖整个文件**，如必须覆盖请先备份
- 所有Python命令使用该路径下的Python执行:**D:\Python3.12\python.exe**,不要执行使用默认的Python命令

## 重要文档/目录

- **project_info.md** - 接口自动化的完整项目概述、技术架构、功能模块、开发进度
- **ui_project_info.md** - 基于 **browser_use** 开源框架的 AI 驱动 UI 自动化测试平台，文件记录完整项目介绍、技术架构、功能模块、开发进度
- **README.md** - 用户操作手册和快速开始指南
- **/develop_document/** - 功能设计和实现文档
- **/test_case/** - 测试用例和测试报告
- **/test_case/playwright_Test** - UI自动化测试用例
- **/test_case/api_test** - 接口自动化测试用例

## 开发流程

### TDD 测试驱动开发（优先）

新功能开发必须遵循 TDD 流程：

1. 新功能开发必须分析需求，并编写功能文档和测试用例文档
2. 按照功能文档进行开发
3. 根据测试用例进行完整测试

### 开发文档编写

- 位置：`D:\AI\AI-test-project\develop_document\`
- 按功能模块分类，同一功能的前后端实现写在一个文件
- 格式：markdown
- 内容：功能和实现思路，无需包含代码

### 测试用例编写

- 位置：`D:\AI\AI-test-project\test_case\`
- 按功能区分，同一功能的用例写在同一文件
- 格式：markdown

## 项目环境

- **操作系统**：Windows（优先使用 PowerShell）
- **代码位置**：当前仓库目录及其子目录

## 工作方式

- 作为自动化开发助手，**尽量减少交互次数**
- 能连续完成的步骤，不要每步都停下来询问
- 在权限允许前提下，**自动执行安全操作并直接应用变更**

### 修改完成后提供

- 变更概要
- 关键文件的 diff 摘要
- 测试/构建命令执行结果

## 开发命令

### 后端 (Django)

```bash
cd Django_project

# 运行开发服务器（端口: 127.0.0.1:8000）
python manage.py runserver 127.0.0.1:8000

# 创建/应用迁移
python manage.py makemigrations
python manage.py migrate

# 运行测试
python manage.py test

# 创建管理员
python manage.py createsuperuser
```

### 前端 (Vue 3)

```bash
cd VUE3

# 安装依赖
npm install

# 运行开发服务器（端口: localhost:3000）
npm run dev -- --host localhost --port 3000

# 构建生产版本
npm run build

# 运行测试
npm run test

# 代码检查
npm run lint
npm run type-check
```

## 模块开发规范

### 模块隔离

- API自动化模块：数据库表使用 `api_` 前缀
- API路由：必须使用 `/api/v1/api-automation/` 前缀
- 前端路由：必须使用 `/api-automation/*` 命名空间
- 禁止跨模块代码共享
- 每个模块必须可独立部署

### 当前开发重点

**API自动化测试模块已100%完成。UI自动化测试模块已启动开发。**

### UI自动化测试模块开发中

- 项目需求文档：`ui_project_info.md`
- 后端路径：`Django_project/ui_automation/`
- 前端路径：`VUE3/src/modules/ui-automation/`
- 核心执行器：browser_use (https://github.com/browser-use/browser-use)

## 数据库设计规范

- 表名：小写+下划线，复数形式（如 `api_test_cases`）
- 所有表必须有 `created_at` 和 `updated_at` 字段
- 使用外键约束保证数据完整性
- 为常用查询字段添加索引
- API自动化模块表使用 `api_` 前缀
- 支持软删除（`is_deleted` 字段）

## 代码质量规范

### 后端 (Python)

- 严格遵循 PEP 8
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 所有API端点必须有单元测试
- 测试覆盖率必须 ≥80%
- 使用 `select_related` 和 `prefetch_related` 优化查询
- 实现适当的错误处理和日志记录

### 前端 (TypeScript/Vue)

- 使用 `<script setup>` 语法
- 组件名使用 PascalCase
- 明确定义 props 和 emits 类型
- 新代码使用 TypeScript
- 组件文件不超过300行
- 使用 ESLint + Prettier 格式化
- 实现适当的错误边界

## 性能要求

### 后端性能

- 有效使用数据库索引
- 优化查询避免 N+1 问题
- 实现缓存策略（Redis + 应用缓存）
- 大数据集使用分页
- 长时间任务使用异步处理
- 监控和优化慢查询

### 前端性能

- 路由组件懒加载
- 有效使用代码分割
- 优化图片（压缩、WebP格式）
- 适当实现API请求缓存
- 通过 tree shaking 减小打包体积

## Git 工作流

### 分支策略

- 主分支：`main`
- 功能分支：`feature/description`
- 修复分支：`bugfix/description`
- 紧急修复：`hotfix/description`

### 提交信息格式

遵循 Conventional Commits：
- `feat`：新功能
- `fix`：Bug修复
- `docs`：文档变更
- `style`：代码风格变更
- `refactor`：代码重构
- `test`：测试添加或变更
- `chore`：维护任务

示例：
```
feat(api-automation): add test case execution feature

- Implement test case executor service
- Add API endpoint for running tests
- Create frontend component for test execution
```

### 自动提交和推送规则

**⚠️ 强制规则**：Claude Code 必须遵守以下 Git 工作流

| 触发条件 | 操作 |
|---------|------|
| **每次修改文件** | 必须执行 `git commit` |
| **修改文件超过 3 个** | 必须执行 `git push` |
| **本地 commit 超过 3 个** | 必须执行 `git push` |

**工作流程**：
```
1. 修改代码
2. git add <修改的文件>
3. git commit -m "类型: 描述"
4. 检查触发条件：
   - 修改文件数 > 3？→ git push
   - 未推送 commit 数 > 3？→ git push
```

**Commit 消息规范**：
```
<类型>(<模块>): <简短描述>

- 详细说明1
- 详细说明2
```

**类型示例**：
- `feat(api-automation): 新增测试用例批量执行功能`
- `fix(ui-automation): 修复浏览器启动失败问题`
- `docs(readme): 更新安装步骤说明`
- `refactor(dashboard): 重构数据获取逻辑`

### 代码审查检查清单

- [ ] 代码遵循项目风格指南
- [ ] 测试已编写并通过
- [ ] 文档已更新
- [ ] 安全考虑已处理
- [ ] 性能影响已考虑
- [ ] 错误处理已实现
- [ ] Git 规则已遵守（commit + push）

## 常见开发流程

### 添加新API端点

1. 在 `Django_project/api_automation/models.py` 创建/更新模型
2. 运行 `python manage.py makemigrations api_automation`
3. 运行 `python manage.py migrate`
4. 在 `Django_project/api_automation/serializers.py` 创建/更新序列化器
5. 在 `Django_project/api_automation/views.py` 创建/更新视图
6. 在 `Django_project/api_automation/urls.py` 添加URL
7. 在 `VUE3/src/modules/api-automation/api/` 创建/更新API文件
8. 在 `VUE3/src/modules/api-automation/types/` 创建/更新类型
9. 添加/更新前端组件/视图
10. 编写前后端测试
11. 更新文档

### 数据库迁移流程

```bash
# 模型变更后
python manage.py makemigrations api_automation

# 查看生成的迁移文件

# 应用迁移
python manage.py migrate

# 生产环境使用
python manage.py migrate --settings=config.settings.production
```

### 添加新前端组件

1. 在适当的模块目录创建组件
2. 使用 TypeScript，正确定义 prop/emit
3. 遵循单一职责原则
4. 复杂组件添加单元测试
5. 如需要从模块 index 文件导出
6. 更新文档

### 重启服务

**重启后端（端口 127.0.0.1:8000）**
```bash
# 1. 查找占用端口的进程
netstat -ano | findstr ":8000" | findstr "LISTENING"

# 2. Kill进程（假设PID为1234）
taskkill /F /PID 1234

# 3. 重新启动
cd Django_project
python manage.py runserver 127.0.0.1:8000
```

**重启前端（端口 localhost:3000）**
```bash
# 1. 查找占用端口的进程
netstat -ano | findstr ":3000" | findstr "LISTENING"

# 2. Kill进程（假设PID为5678）
taskkill /F /PID 5678

# 3. 重新启动
cd VUE3
npm run dev -- --host localhost --port 3000
```

## 重要提醒

1. **始终**使用适当的模块隔离 - 禁止跨模块导入
2. **必须**遵循命名约定（所有API模块类使用Api前缀）
3. **必需**为所有新功能编写测试（≥80%覆盖率）
4. **强制**合并任何变更前进行代码审查
5. **始终**考虑新代码的安全影响
6. **必须**优化性能（数据库查询、打包体积）
7. **必需**为API变更更新文档
