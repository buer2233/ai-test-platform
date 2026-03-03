# 方案B：RAG 文档解析生成用例 测试用例（优化版）

**对应方案**：`develop_document/12B-rag-doc-generation.md`
**测试目标**：覆盖文档入库、向量检索、生成、预览编辑、试运行门禁与提交流程。
**TDD约束**：先写测试，再写实现；覆盖率目标 80%+（单元 + 集成 + E2E）。

---

## 0. 依据与范围

- 设计依据：`develop_document/12B-rag-doc-generation.md`
- 脚本骨架：
  - API/集成：`test_case/api_test/test_rag_generation_skeleton.py`
  - E2E：`test_case/playwright_Test/12-rag-generation.spec.ts`

---

## 1. 用户旅程（User Journeys）

1. 作为测试人员，我希望在项目内上传 Markdown 文档并完成入库，以便后续 RAG 生成。
2. 作为测试人员，我希望输入需求后生成用例草稿，并可编辑确认。
3. 作为测试人员，我希望生成后自动试运行，全部通过才能提交。
4. 作为测试人员，我希望向量库异常时能得到明确提示并可重试。

---

## 1.1 需求对接要点转化为测试重点（PM/开发/测试）

- **PM**：入口在项目内、文档版本可追溯、结果可编辑 -> 覆盖文档上传、预览编辑、版本/来源展示
- **DEV**：切分策略可配置、向量库配置项目隔离 -> 覆盖 ingest_config 与 vector_config 校验
- **QA**：异常明确、门禁强制 -> 覆盖 error_info、向量库异常与门禁阻断

---

## 2. 单元测试用例（Service/Utils）

### 2.1 DocIngestService
- **UT-RAG-001** Markdown 按标题层级切分
  - 期望：chunk_count 正确，heading_path 正确
- **UT-RAG-002** 空文档或无有效内容
  - 期望：入库失败并给出提示
- **UT-RAG-003** ingest_config 生效
  - 期望：切分策略与清洗规则按配置执行

### 2.2 RagRetrieveService
- **UT-RAG-004** 向量检索返回相关 chunks
  - 期望：返回列表按相关性排序
- **UT-RAG-005** 向量库不可用
  - 期望：抛出可读错误并记录

### 2.3 CaseGenerateService
- **UT-RAG-006** 生成 ApiTestCase 草稿
  - 期望：payload 含 method/url/params/body/断言
- **UT-RAG-007** 生成 ApiTestScenario 草稿
  - 期望：steps 顺序正确、变量引用合理

### 2.4 CaseValidateService
- **UT-RAG-008** 参数完整性校验
  - 期望：缺失必填字段则失败

### 2.5 ArtifactGateService
- **UT-RAG-009** 试运行全通过 -> READY
- **UT-RAG-010** 试运行失败 -> 仍为 DRAFT

---

## 3. 集成测试用例（API + DB）

### 3.1 文档上传与入库
- **IT-RAG-001** 上传 Markdown 文档（必须 project_id）
  - 期望：状态 UPLOADED，返回 doc_id
- **IT-RAG-002** 入库任务
  - 期望：状态 INGESTED，chunk_count > 0
- **IT-RAG-003** 入库失败
  - 期望：状态 FAILED，error_info 记录原因
- **IT-RAG-004** 向量库配置缺失
  - 期望：入库被拒绝并提示配置缺失

### 3.2 生成与预览
- **IT-RAG-005** 触发生成请求
  - 期望：创建 rag_query 记录，status COMPLETED
- **IT-RAG-006** 生成用例预览
  - 期望：返回 artifact payload 可编辑
- **IT-RAG-007** 检索为空
  - 期望：提示无相关文档
- **IT-RAG-008** rag_query 记录完整
  - 期望：retrieved_chunk_ids 与 model_name 存在

### 3.3 试运行门禁
- **IT-RAG-009** 试运行全部通过
  - 期望：artifact status = READY
- **IT-RAG-010** 试运行失败
  - 期望：artifact status 保持 DRAFT
- **IT-RAG-011** 提交成功
  - 期望：生成 ApiTestCase/Scenario，artifact status=COMMITTED

---

## 4. E2E 测试用例（Playwright）

- **E2E-RAG-001** 项目内上传文档并入库
  - 期望：显示入库成功与文档状态
- **E2E-RAG-002** 输入需求生成用例并预览
  - 期望：生成草稿可编辑并保存
- **E2E-RAG-003** 触发试运行并提交
  - 期望：通过后可提交，失败禁止提交
- **E2E-RAG-004** 向量库不可用提示
  - 期望：显示可重试提示

---

## 5. 边界与异常用例

- **EDGE-RAG-001** 文档无接口信息
  - 期望：提示无法生成，返回可读错误
- **EDGE-RAG-002** 向量库连接失败
  - 期望：返回 503，提示稍后重试
- **EDGE-RAG-003** 检索为空
  - 期望：提示无相关文档
- **EDGE-RAG-004** 缺少 project_id
  - 期望：返回 400

---

## 6. 覆盖率与验收标准

- 单元 + 集成 + E2E 覆盖率 >= 80%
- 生成后的用例必须可编辑与可执行
- 门禁逻辑严格生效（失败不能提交）

---

## 7. 通过标准

- 以上用例全部通过
- 无阻塞级缺陷
- 生成用例可提交并进入执行报告流程
