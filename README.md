# AI 自动化测试平台

[![frontend](https://img.shields.io/badge/frontend-Vue3%20%2B%20TS-42b883)](./VUE3)
[![backend](https://img.shields.io/badge/backend-Django%20%2B%20DRF-0c4b33)](./Django_project)
[![e2e](https://img.shields.io/badge/E2E-Playwright-2EAD33)](./VUE3/tests)
[![docs](https://img.shields.io/badge/docs-OpenSpec-blue)](./openspec)

一个面向团队协作的自动化测试平台，覆盖 API 自动化与 AI 驱动 UI 自动化两条主线。

平台目标不是“单点执行工具”，而是“可持续迭代的测试工程系统”：

- 统一测试资产：项目、用例、执行、报告
- 统一执行链路：页面触发、服务编排、实时状态、结果沉淀
- 统一扩展路径：OpenSpec 规范驱动、模块化演进

## 亮点

| 亮点 | 当前能力 |
|------|----------|
| 双模块架构 | API 自动化 + UI 自动化并行可用 |
| 前端体验升级 | 自研 `element-plus` 兼容层 + 新视觉体系 |
| 执行可观测性 | WebSocket 实时状态 + 报告 summary/file 双接口 |
| 工程化测试 | Playwright E2E 用例与报告输出链路已落地 |
| 模块化设计 | 前后端都按模块拆分，可独立迭代 |

## 模块状态

| 模块 | 状态 | 说明 |
|------|------|------|
| API 自动化 | 可用（主成熟模块） | 覆盖项目/集合/用例/环境/执行/报告/回收站 |
| UI 自动化 | 可用并持续迭代 | 基于 browser_use，支持执行与报告闭环 |
| AI 独立模块 | 规划中 | 尚未形成独立业务子系统 |

## 架构速览

```text
Vue3 Frontend
  -> Django REST API
    -> 执行服务 / WebSocket
      -> API 引擎 or UI(browser_use CLI)
        -> 结果与报告存储
```

关键目录：

- `Django_project/api_automation/`
- `Django_project/ui_automation/`
- `VUE3/src/modules/api-automation/`
- `VUE3/src/modules/ui-automation/`
- `VUE3/src/shared/ui/element-plus/`

## 快速启动

### 1. 启动后端

```bash
cd Django_project
python manage.py migrate
python manage.py runserver
```

后端地址：`http://127.0.0.1:8000/`
Swagger：`http://127.0.0.1:8000/swagger/`

### 2. 启动前端

```bash
cd VUE3
npm install
npm run dev
```

前端地址：`http://localhost:3000/`

### 3. 构建验证

```bash
cd VUE3
npm run build
```

### 4. 端到端测试

```bash
cd VUE3
npx playwright test
```

## 功能地图

### API 自动化

- 项目/集合/测试用例管理
- 断言与数据提取配置
- HTTP 执行器与执行记录
- 批量执行、重试、取消
- 报告详情与仪表盘统计
- 回收站恢复与永久删除

### UI 自动化

- 自然语言用例管理
- 执行记录与执行监控
- browser_use CLI 执行编排
- 报告汇总（summary）与原始文件读取（file）
- 截图模型与报告关联

## 当前已知缺口（代码层）

- 仪表盘到测试结果详情的跳转链路未完成
- 测试用例编辑器按光标插入变量待完善
- UI 执行监控页截图从报告 API 自动加载待完善
- 后端统一依赖清单（根级 requirements）待补齐

## 文档索引

- 总体盘点：`project_info.md`
- UI 模块说明：`ui_project_info.md`
- OpenSpec 规范：`openspec/AGENTS.md`
- 开发文档：`develop_document/`
- 手工测试用例：`test_case/`

## 推荐阅读路径

1. 先看 `README.md` 了解整体能力边界
2. 再看 `project_info.md` 了解全盘实现/缺口
3. 若做 UI 模块开发，重点看 `ui_project_info.md`
4. 开发前按 `openspec/AGENTS.md` 建立变更提案

## 路线图

- 近期：补齐主链路 TODO，固定 build + E2E + 关键后端测试门禁
- 中期：增强报告可观测性与执行稳定性，完善异常场景覆盖
- 后续：调度能力、趋势分析、AI 独立模块立项

## 许可

MIT
