# AI自动化测试平台 - 总项目说明（现状盘点版）

> 更新时间：2026-02-13
> 文档目的：基于当前仓库代码，给出“已实现 / 未实现 / 预计实现”的全盘分析，作为开发与协作基线。

## 1. 项目定位

本项目是一个前后端分离的自动化测试平台，当前由两个可用业务模块组成：

- API 自动化测试（主成熟模块）
- UI 自动化测试（可用并持续迭代）

AI 自动化模块（独立于 UI browser_use 场景）尚未落地为独立业务子系统。

## 2. 当前实现状态总览

| 模块 | 当前状态 | 说明 |
|------|----------|------|
| API 自动化（后端） | 已实现 | 完整 CRUD + 执行 + 报告 + 回收站 + 仪表盘 + WebSocket |
| API 自动化（前端） | 已实现 | 登录、仪表盘、项目/集合/用例/环境、HTTP 执行器、报告、回收站 |
| UI 自动化（后端） | 已实现并迭代 | 项目/用例/执行/报告/截图模型与 API，CLI 执行链路可用 |
| UI 自动化（前端） | 已实现并迭代 | 项目、用例、执行监控、报告列表与详情、状态统一 |
| AI 自动化独立模块 | 未实现 | 仅有规划目标，暂无独立代码结构与路由 |

## 3. 架构与目录

```text
Django_project/
  api_automation/         # API 自动化后端
  ui_automation/          # UI 自动化后端（含 browser-use 集成）
  config/                 # Django 配置、总路由、ASGI

VUE3/
  src/core/               # 核心路由与基础设施
  src/modules/api-automation/
  src/modules/ui-automation/
  src/shared/ui/element-plus/  # 自研兼容层（通过 vite alias 接管 element-plus）
  tests/                  # Playwright E2E

openspec/                # 规范驱动变更
develop_document/        # 开发文档
test_case/               # 手工测试用例
```

## 4. 技术栈与依赖现状

### 4.1 后端（从代码与配置提取）

- Django 3.2.x
- Django REST Framework
- drf-yasg（Swagger）
- Channels（WebSocket）
- django-filter
- corsheaders
- 数据库：MySQL（`config/settings.py` 当前为 MySQL 配置）

说明：仓库当前未发现统一的后端 `requirements.txt` 根文件，依赖以环境与现有代码导入为准。

### 4.2 前端（`VUE3/package.json`）

- Vue 3 + TypeScript + Vite
- Pinia、Vue Router、Axios
- ECharts
- Playwright（E2E）
- `element-plus` 依赖仍在包中，但运行期通过 `vite.config.ts` alias 指向 `src/shared/ui/element-plus/index.ts` 兼容层

## 5. 已实现功能盘点

### 5.1 API 自动化模块（后端）

已实现核心能力：

- 项目、集合、测试用例、环境、执行、结果、报告、数据驱动、HTTP 执行记录、回收站管理
- 断言与提取配置（含批量更新）
- 测试执行动作（执行、取消、失败重试等）
- 仪表盘统计与维度报表
- Token 认证、当前用户接口
- WebSocket 事件推送（ASGI 已接入）

主要入口：`Django_project/api_automation/urls.py`、`Django_project/api_automation/views.py`

### 5.2 API 自动化模块（前端）

已实现页面与交互主链路：

- 登录/注册页
- 仪表盘
- 项目/集合/测试用例管理
- 环境管理
- HTTP 执行器与执行记录
- 测试报告列表/详情
- 回收站

路由定义：`VUE3/src/modules/api-automation/router/index.ts`

### 5.3 UI 自动化模块（后端）

已实现核心能力：

- `UiTestProject`、`UiTestCase`、`UiTestExecution`、`UiTestReport`、`UiScreenshot`
- 项目/用例/执行/报告/截图 API
- 执行取消
- 报告文件接口 + 报告 summary 接口
- 通过 subprocess 调用 browser_use CLI，支持进度解析与状态更新

主要入口：`Django_project/ui_automation/urls.py`、`Django_project/ui_automation/views.py`

### 5.4 UI 自动化模块（前端）

已实现页面与链路：

- 项目列表/详情
- 用例列表/创建/详情
- 执行记录与执行监控
- 报告列表与报告详情
- 与 API 模块的侧边栏模块切换

路由定义：`VUE3/src/modules/ui-automation/router/index.ts`

### 5.5 前端基础设施与视觉体系

已实现：

- 模块化路由合并（`src/core/router/index.ts`）
- 自研 Element Plus 兼容层（`src/shared/ui/element-plus`）
- 全局设计令牌与统一视觉基线
- Playwright E2E 框架与报告输出链路

## 6. 未实现与待完善项（基于代码扫描）

### 6.1 功能缺口（主仓主线代码）

- 仪表盘“测试结果详情跳转”未落地
  - `VUE3/src/modules/api-automation/views/Dashboard/index.vue`
  - `VUE3/src/modules/api-automation/views/Dashboard/components/DataDetailDialog.vue`
- 测试用例编辑器“按光标插入变量”逻辑待完善
  - `VUE3/src/modules/api-automation/components/TestCaseEditor.vue`
- UI 执行监控页“从报告接口加载截图”待完成
  - `VUE3/src/modules/ui-automation/views/Execution/ExecutionMonitor.vue`

### 6.2 工程化缺口

- 缺少统一后端依赖清单（根级 requirements）
- 仓库存在大量测试产物与调试文件变更，影响协作清晰度
- 全量回归（build + E2E + 后端测试）需持续固定为 CI 标准流程

### 6.3 独立 AI 自动化模块

- 当前仅在文档层有规划，尚未形成独立前后端模块、数据模型、路由和测试基线

## 7. 预计实现功能（建议路线图）

### P0（近期，建议 1-2 个迭代）

- 完成 3 个主线 TODO 闭环（详情跳转、光标插入、截图联动）
- 固化“构建 + E2E + 后端关键用例”流水线并门禁
- 清理测试产物纳入 `.gitignore` 规范

### P1（中期）

- UI 自动化报告增强（失败步骤聚焦、关键动作摘要）
- API 自动化结果详情深链路（从仪表盘到单条结果）
- 执行稳定性与异常可观测性提升（错误分类、重试策略、日志结构化）

### P2（后续）

- 定时调度与任务编排（含批量策略）
- 历史趋势与质量看板
- AI 自动化独立模块立项与最小可用版本

## 8. 测试现状

- 前端 E2E：`VUE3/tests/`（Playwright）
  - `01-auth-shell.spec.ts`
  - `02-api-platform.spec.ts`
  - `03-ui-platform.spec.ts`
  - `04-visual-regression.spec.ts`
- UI 自动化后端新增 summary 接口测试已在仓库中
- 建议将后端测试与前端 E2E 统一纳入一次性回归命令

## 9. 风险与约束

- 平台依赖本地服务地址约定：
  - 前端：`http://localhost:3000/`
  - 后端：`http://127.0.0.1:8000/`
- UI 自动化执行依赖 browser_use 环境与外部模型配置（`.env`）
- 文档中的“完成度百分比”不再使用绝对值，后续以“可用性 + 缺口清单”维护

## 10. 结论

当前项目已形成“API 自动化成熟 + UI 自动化可用迭代”的双模块格局。下一阶段重点不是扩功能面，而是补齐主链路缺口、强化回归门禁、稳定交付质量。
