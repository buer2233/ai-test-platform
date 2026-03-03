# 方案A：流量录制回放生成用例 测试用例（优化版）

**对应方案**：`develop_document/12A-traffic-based-generation.md`
**测试目标**：覆盖录制解析、过滤、参数化、生成、预览编辑、试运行门禁与提交流程。
**TDD约束**：先写测试，再写实现；覆盖率目标 80%+（单元 + 集成 + E2E）。

---

## 0. 依据与范围

- 设计依据：`develop_document/12A-traffic-based-generation.md`
- 脚本骨架：
  - API/集成：`test_case/api_test/test_traffic_generation_skeleton.py`
  - E2E：`test_case/playwright_Test/11-traffic-generation.spec.ts`

---

## 1. 用户旅程（User Journeys）

1. 作为测试人员，我希望在项目内上传录制文件并解析会话，从而快速生成可编辑用例。
2. 作为测试人员，我希望系统自动识别动态参数并生成变量提取规则，从而回放稳定。
3. 作为测试人员，我希望预览并调整生成用例，确保断言和步骤顺序正确。
4. 作为测试人员，我希望生成后自动试运行，只有全部通过才能提交。
5. 作为测试人员，我希望解析失败时可看到清晰错误并可重试。

---

## 1.1 需求对接要点转化为测试重点（PM/开发/测试）

- **PM**：入口在项目内、结果可编辑、失败可重试 -> 覆盖项目入口、预览编辑、失败提示与重试
- **DEV**：异步解析与去重、配置可追溯 -> 覆盖 content_hash 去重与 processing_config 记录
- **QA**：失败记录清晰、门禁强制 -> 覆盖 error_info 与门禁失败阻断

---

## 2. 单元测试用例（Service/Utils）

### 2.1 TrafficParseService
- **UT-TRAFFIC-001** 解析标准 JSON 文件为 Entry 列表
  - 期望：字段齐全、类型正确、错误记录为空
- **UT-TRAFFIC-002** 解析异常格式文件
  - 期望：抛出可读错误、Capture 状态置为 FAILED
- **UT-TRAFFIC-003** 解析空文件
  - 期望：提示无有效请求，entries=0
- **UT-TRAFFIC-004** 解析超大文件（> 限制）
  - 期望：返回明确错误码与说明
- **UT-TRAFFIC-005** 解析失败记录 error_info
  - 期望：error_info 有错误原因

### 2.2 TrafficFilterService
- **UT-TRAFFIC-006** 过滤静态资源与探活请求
  - 期望：is_valuable=false，filter_reason 记录原因
- **UT-TRAFFIC-007** 去重策略（fingerprint + content_hash）
  - 期望：重复请求仅保留一条

### 2.3 ParameterizeService
- **UT-TRAFFIC-008** 自动识别 token/id 等动态字段
  - 期望：生成变量规则，后续请求被替换
- **UT-TRAFFIC-009** 无动态字段的请求
  - 期望：不产生变量规则
- **UT-TRAFFIC-010** 变量命名冲突
  - 期望：提示冲突并生成待确认标记

### 2.4 TrafficScenarioBuilder
- **UT-TRAFFIC-011** 基于时间序列拼接步骤
  - 期望：step_order 正确
- **UT-TRAFFIC-012** 缺少前置请求
  - 期望：标记为需要人工确认

### 2.5 ArtifactGateService
- **UT-TRAFFIC-013** 试运行全通过 -> READY
  - 期望：状态从 DRAFT -> READY
- **UT-TRAFFIC-014** 试运行失败 -> 仍为 DRAFT
  - 期望：记录失败原因

---

## 3. 集成测试用例（API + DB）

### 3.1 录制上传与解析
- **IT-TRAFFIC-001** POST 录制上传（必须 project_id）
  - 期望：状态 UPLOADED，返回 capture_id
- **IT-TRAFFIC-002** POST 解析录制
  - 期望：状态 PARSED，sessions_count > 0
- **IT-TRAFFIC-003** 解析失败
  - 期望：状态 FAILED，error_info 写入
- **IT-TRAFFIC-004** 上传重复文件（content_hash）
  - 期望：可复用解析结果或提示重复
- **IT-TRAFFIC-005** processing_config 可追溯
  - 期望：解析配置保存并可查询

### 3.2 会话生成与预览
- **IT-TRAFFIC-006** 会话列表仅返回当前项目
  - 期望：跨项目不可见
- **IT-TRAFFIC-007** 生成用例草稿（session -> artifact）
  - 期望：artifact status = DRAFT
- **IT-TRAFFIC-008** 预览生成结果
  - 期望：返回可编辑 payload（步骤、变量、断言）

### 3.3 变量规则与提取
- **IT-TRAFFIC-009** 自动生成变量规则并保存
  - 期望：ApiTrafficVariableRule 记录正确
- **IT-TRAFFIC-010** 手工编辑变量规则
  - 期望：保存成功并影响预览结果

### 3.4 试运行门禁
- **IT-TRAFFIC-011** 试运行全部通过
  - 期望：artifact status = READY，允许提交
- **IT-TRAFFIC-012** 试运行失败
  - 期望：artifact status 保持 DRAFT
- **IT-TRAFFIC-013** 提交成功
  - 期望：生成 ApiTestCase/Scenario，artifact status=COMMITTED

---

## 4. E2E 测试用例（Playwright）

- **E2E-TRAFFIC-001** 项目内上传录制文件并解析
  - 期望：页面显示解析成功与会话列表
- **E2E-TRAFFIC-002** 进入预览并编辑变量/断言
  - 期望：保存草稿后返回最新内容
- **E2E-TRAFFIC-003** 触发试运行并查看结果
  - 期望：全部通过后按钮允许“提交”
- **E2E-TRAFFIC-004** 失败门禁
  - 期望：失败时“提交”按钮禁用并提示原因

---

## 5. 边界与异常用例

- **EDGE-TRAFFIC-001** 超大文件上传（> 限制）
  - 期望：前端提示限制，后端拒绝并返回错误
- **EDGE-TRAFFIC-002** 无有效请求（全部被过滤）
  - 期望：提示无可生成内容
- **EDGE-TRAFFIC-003** 缺少 project_id
  - 期望：返回 400
- **EDGE-TRAFFIC-004** 参数化规则冲突
  - 期望：提示人工处理冲突变量
- **EDGE-TRAFFIC-005** 解析后无会话
  - 期望：提示“无可用会话”

---

## 6. 覆盖率与验收标准

- 单元 + 集成 + E2E 覆盖率 >= 80%
- 所有试运行门禁逻辑覆盖（通过/失败）
- 生成后的用例必须可编辑与可执行
- 未通过测试不允许提交

---

## 7. 通过标准

- 以上用例全部通过
- 无阻塞级缺陷
- 生成用例可提交并进入执行报告流程
