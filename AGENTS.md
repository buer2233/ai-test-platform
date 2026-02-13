# AI自动化平台（仓库指南）

## 项目结构与模块组织
- `Django_project/`：Django 后端（应用包含 `api_automation/`、`ui_automation/`、`config/`）。
- `VUE3/`：Vue 3 + Vite 前端，业务模块位于 `src/modules/`（`api-automation/`、`ui-automation/`）。
- `openspec/`：规范驱动变更的提案、任务与规格说明。
- `develop_document/`：设计/功能文档；`test_case/`：手工测试用例与报告。
- 前端测试输出位于 `VUE3/tests/report/` 和 `VUE3/test-results/`。

## 重要规则

- 优先使用简体中文
- 前端服务地址固定：**http://localhost:3000/**（IP占用表示服务已启动,直接使用,未占用才开启）
- 后端服务地址固定：**http://127.0.0.1:8000/**（IP占用表示服务已启动,直接使用,未占用才开启）
- 后端代码改动后，如涉及模型变更需执行数据库迁移

## 重要文档/目录

- **project_info.md** - 接口自动化的完整项目概述、技术架构、功能模块、开发进度
- **ui_project_info.md** - 基于 **browser_use** 开源框架的 AI 驱动 UI 自动化测试平台，文件记录完整项目介绍、技术架构、功能模块、开发进度

## 构建、测试与开发命令

- 后端开发：
  - `cd Django_project`
  - `python manage.py migrate`
  - `python manage.py runserver`
- 前端开发/构建：
  - `cd VUE3`
  - `npm install`
  - `npm run dev`（启动本地开发服务）
  - `npm run build`（类型检查 + 生产构建）
  - `npm run preview`（预览构建产物）
- 前端端到端测试（Playwright）：
  - `cd VUE3`
  - `npx playwright test`
- 后端测试（pytest 风格）：
  - `cd Django_project`
  - `python -m pytest`

## 编码风格与命名规范
- 前端 lint 规则见 `VUE3/.eslintrc.cjs`（Vue 3 essential + TypeScript）。
- 遵循既有模块结构，API 与 UI 自动化代码分别放在对应目录中。
- 命名约定：TS/JS 变量与函数用 camelCase，Vue 组件/类用 PascalCase，Python 函数与模块用 snake_case。

## 测试指南
- Playwright 用例位于 `VUE3/tests/`，文件名为 `*.spec.ts`。
- 后端测试位于 `Django_project/` 和 `Django_project/api_automation/tests/`，文件名为 `test_*.py`。
- 新增测试请与修改区域就近放置，并保持命名一致。

## OpenSpec 工作流
- 新功能或架构调整请在 `openspec/changes/<change-id>/` 创建提案并更新任务/规格。
- 详见 `openspec/AGENTS.md` 与 `openspec/project.md`。

## 自动提交和推送规则

**⚠️ 强制规则**：必须遵守以下 Git 工作流

| 触发条件                  | 操作                           |
| ------------------------- | ------------------------------ |
| **每次 commit 前**        | 必须先执行 `git pull` 更新代码 |
| **每次修改文件**          | 必须执行 `git commit`          |
| **修改文件超过 5 个**     | 必须执行 `git push`            |
| **本地 commit 超过 3 个** | 必须执行 `git push`            |

**工作流程**：

```
1. 修改代码
2. git add <修改的文件>
3. git pull (更新最新代码)
   ├─ 无冲突 → 继续
   └─ 有冲突 → 等待用户确认解决
4. git commit -m "类型: 描述"
5. 检查触发条件：
   - 修改文件数 > 5？→ git push
   - 未推送 commit 数 > 3？→ git push
```

**冲突处理规则**：

- 如果 `git pull` 检测到冲突，**必须停止自动操作**
- 向用户报告冲突信息
- 等待用户手动解决冲突
- 用户确认后才能继续 commit

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

