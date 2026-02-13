# UI自动化测试模块 - 项目说明（现状与路线图）

> 更新时间：2026-02-13
> 模块状态：可用并持续迭代
> 版本标识：v0.11.x（文档版）

## 1. 模块定位

UI 自动化模块用于把“自然语言测试意图”转成可执行浏览器动作，最终沉淀执行记录、报告与截图。

当前采用“前端触发 + Django 编排 + browser_use CLI 执行”的混合架构，已形成可运行闭环。

## 2. 当前架构

```text
Vue3 (ui-automation views)
  -> DRF API (ui_automation)
    -> CliTestExecutorService
      -> subprocess 调用 run_aiTest.py
        -> browser_use Agent + Playwright
          -> JSON 报告 / 截图
```

关键目录：

- `Django_project/ui_automation/`
- `Django_project/ui_automation/browser-use-0.11.2/`
- `VUE3/src/modules/ui-automation/`

## 3. 已实现功能

### 3.1 后端

已实现：

- 模型：项目、用例、执行、报告、截图
- 路由：`/api/v1/ui-automation/projects|test-cases|executions|reports|screenshots`
- 执行链路：执行创建、执行启动、执行取消、状态流转
- 报告能力：
  - 报告详情
  - 报告 summary（结构化汇总）
  - 报告 file（原始文件读取）
- WebSocket 推送：执行进度/状态广播

主要文件：

- `Django_project/ui_automation/models.py`
- `Django_project/ui_automation/views.py`
- `Django_project/ui_automation/services/cli_test_executor_service.py`
- `Django_project/ui_automation/services/websocket_service.py`

### 3.2 前端

已实现页面：

- 项目：列表、详情
- 用例：列表、创建、详情
- 执行：执行记录、执行监控
- 报告：列表、详情
- 侧边栏模块切换：API 平台 <-> UI 平台

主要文件：

- `VUE3/src/modules/ui-automation/router/index.ts`
- `VUE3/src/modules/ui-automation/views/Execution/ExecutionList.vue`
- `VUE3/src/modules/ui-automation/views/Execution/ExecutionMonitor.vue`
- `VUE3/src/modules/ui-automation/views/Report/ReportList.vue`
- `VUE3/src/modules/ui-automation/views/Report/ReportDetail.vue`

### 3.3 测试

已落地：

- 后端接口测试：`Django_project/ui_automation/tests/test_report_summary_api.py`
- 前端 E2E 覆盖入口：`VUE3/tests/03-ui-platform.spec.ts`

## 4. 未实现与待完善（当前主线缺口）

### 4.1 前端缺口

- 执行监控页截图链路仍有 TODO（应从报告 API 获取截图并渲染）
  - `VUE3/src/modules/ui-automation/views/Execution/ExecutionMonitor.vue`

### 4.2 稳定性与工程化缺口

- browser_use 依赖外部模型配置，环境问题会直接影响执行稳定性
- 报告文件缺失、权限异常、路径异常等场景还需更系统的前后端兜底提示
- E2E 用例目前以主流程覆盖为主，异常路径覆盖仍有提升空间

### 4.3 与主项目协同缺口

- 与 API 模块的跨模块导航与状态共享仍较弱（更多是并列模块，而非联动编排）
- 构建、回归、报告留存的 CI 标准化仍需统一

## 5. 预计实现功能（按优先级）

### P0（近期）

- 完成执行监控页截图展示闭环
- 补齐 UI 模块主流程与异常流程的 Playwright 固化用例
- 统一报告异常提示（无文件、路径失效、解析失败）

### P1（中期）

- 报告详情增强：关键步骤摘要、失败动作聚焦、截图时间轴
- 执行过程可观测性增强：状态阶段化、错误分类标签
- 类型收敛：UI 模块 TS 类型补强，减少页面推断逻辑

### P2（后续）

- 批量执行与调度能力
- 历史执行对比与趋势分析
- 更丰富的执行策略（重试、并发、策略模板）

## 6. 运行与联调要点

- 前端地址：`http://localhost:3000/`
- 后端地址：`http://127.0.0.1:8000/`
- UI 执行依赖：
  - Python 运行时
  - `browser-use-0.11.2` 环境
  - `.env` 中模型配置（如 `OPENAI_API_KEY`、`OPENAI_API_BASE_URL`）

## 7. 验收建议（下一阶段）

- 主流程：登录 -> UI 用例 -> 执行记录 -> 报告列表 -> 报告详情
- 异常流程：报告文件缺失、执行失败、WebSocket 中断
- 通过标准：
  - 关键后端测试通过
  - 前端主流程 E2E 通过
  - 构建无错误且页面无阻断问题

---

本说明聚焦“当前代码可证实的事实状态”。后续迭代建议以缺口清单驱动，不使用绝对完成度口径。
