# 接口自动化用例生成（录制回放 + RAG 文档解析）设计方案

**版本**: v1.0
**日期**: 2026-03-03
**范围**: API 自动化用例生成（双轨方案）

---

## 1. 背景与目标

现有系统已具备接口测试用例管理、断言、数据提取、批量执行与报告能力，但用例仍需人工编写，成本高且覆盖不足。本方案目标是引入 **流量录制回放** 与 **AI 文档解析（RAG）** 两条通道自动生成用例，并统一落地为可执行的接口自动化用例（支持多接口串联）。

**核心目标**：
- 同时实现两种生成方式
- 生成用例可执行、可编辑、可复用
- 引入人工确认环节，保证质量
- 结果可追溯（来自录制或文档）

---

## 2. 现有能力复用

根据现有设计文档，系统已支持：
- 单接口用例（ApiTestCase）
- 变量池与参数替换
- 断言与数据提取
- 场景式多步骤串联（ApiTestScenario + Step）
- 执行记录与报告展示

**结论**：生成后的用例建议统一落库为 **ApiTestCase + ApiTestScenario**，减少重复执行引擎开发成本，并与现有执行/报告体系复用。

**命名策略（已确认）**：用例名称由 AI 在生成阶段基于接口信息或功能信息自动生成，支持人工二次编辑。

---

## 3. 总体架构

```
[流量抓包] -> [录制文件] -> [解析/过滤/参数化] -> [AI辅助链路拼接] -> [生成用例] -> [人工确认] -> [执行与报告]

[Markdown文档] -> [切分/向量化] -> [RAG检索] -> [用例生成] -> [人工确认] -> [执行与报告]
```

**统一输出**：
- ApiTestCase: 单接口配置
- ApiTestScenario: 多步骤串联
- 生成来源（traffic / rag）与追溯信息

---

## 4. 方案A：流量录制回放生成用例

### 4.1 数据采集
- **方式**：代理抓包（Python 第三方库）
- **建议库**：`mitmproxy`（支持 HTTPS，脚本扩展方便）
- **输出格式**：JSON（建议统一成内部格式）

**建议内部格式（示例）**
```json
{
  "session_id": "xxx",
  "started_at": "2026-03-03T10:00:00",
  "entries": [
    {
      "timestamp": "...",
      "method": "POST",
      "url": "https://api.xxx.com/login",
      "headers": {"Content-Type": "application/json"},
      "params": {},
      "body": {"username": "test", "password": "123"},
      "response": {
        "status": 200,
        "headers": {},
        "body": {"token": "abc", "user_id": 1},
        "elapsed_ms": 120
      }
    }
  ]
}
```

### 4.2 解析与生成流程
1. **解析与标准化**：统一字段、规范 body 类型
2. **会话切分**：按 session_id / 时间窗口 / trace_id 聚合
3. **过滤与去噪**：剔除静态、探活、重复、无效接口
4. **参数化识别**：识别 token/id/时间戳等动态字段
5. **变量提取**：自动生成 JSONPath 提取规则
6. **链路拼接**：排序并生成场景步骤（可结合 AI）
7. **生成用例**：落库 ApiTestCase + ApiTestScenario
8. **人工确认**：在前端确认变量/断言/步骤顺序

### 4.3 AI 辅助点
- 价值接口识别（分类）
- 动态字段识别与变量命名建议
- 断言建议（状态码/关键字段）
- 步骤依赖关系推断

### 4.4 后端实现要点
- **新增模型建议**
  - ApiTrafficCapture: 录制任务
  - ApiTrafficSession: 解析后的会话摘要
  - ApiTrafficEntry: 标准化请求/响应
  - ApiGeneratedArtifact: 生成结果与追溯信息

- **核心服务**
  - TrafficParseService
  - TrafficFilterService
  - ParameterizeService
  - TrafficScenarioBuilder

- **API**
  - POST `/api/v1/api-automation/traffic-captures/` 上传/创建录制（需 project_id）
  - POST `/api/v1/api-automation/traffic-captures/{id}/parse/`
  - GET `/api/v1/api-automation/traffic-sessions/`
  - POST `/api/v1/api-automation/traffic-sessions/{id}/generate/`（需 project_id）
  - GET `/api/v1/api-automation/generated-artifacts/{id}/preview/`

### 4.5 前端实现要点
- 项目内入口（项目详情页/列表操作：录制生成用例）
- 录制管理页（上传文件、解析状态）
- 会话列表与筛选
- 用例预览与编辑（变量、断言、步骤顺序）
- 一键生成（生成草稿）与试运行结果展示

---

## 5. 方案B：AI 文档解析（RAG）生成用例

### 5.1 文档处理
- 文档统一为 Markdown
- 按标题层级切分（H1/H2/H3）
- 每块附带元数据（模块、接口名、路径）

### 5.2 向量数据库选型
- **推荐**：Qdrant
- **原因**：部署简单（Docker 单容器）、RESTful API、Python SDK 完整

**部署示例**
```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 5.3 RAG 生成流程
1. **文档入库**：Markdown -> chunk -> embedding -> Qdrant
2. **检索**：根据用户需求或功能描述召回相关接口段落
3. **生成**：LLM 根据召回文档生成 ApiTestCase/Scenario
4. **校验**：参数完整性、必填字段、Schema 检查
5. **试跑与修正**：可选自动试跑，失败回写
6. **人工确认**：保存前可编辑

### 5.4 后端实现要点
- **新增模型建议**
  - ApiDocSource: 文档源
  - ApiDocChunk: 文档切片
  - ApiRagQuery: 生成请求记录
  - ApiGeneratedArtifact: 生成结果

- **核心服务**
  - DocIngestService
  - RagRetrieveService
  - CaseGenerateService
  - CaseValidateService

- **API**
  - POST `/api/v1/api-automation/doc-sources/` 上传文档（需 project_id）
  - POST `/api/v1/api-automation/doc-sources/{id}/ingest/`
  - POST `/api/v1/api-automation/rag/generate/`（需 project_id）
  - GET `/api/v1/api-automation/rag/tasks/{id}/`

### 5.5 前端实现要点
- 项目内入口（项目详情页/列表操作：文档解析生成用例）
- 文档管理页（上传/解析/状态）
- 生成向导页（需求输入、预览）
- 生成结果确认页

---

## 6. 统一生成与人工确认流程

```
生成任务 -> 预览 -> 人工确认 -> 试运行 -> 通过后提交 -> 报告
                     ^ 失败则修改并重试
```

**关键配置**
- 断言默认模板（状态码/关键字段）
- 变量提取规则可编辑
- 执行环境选择
- 提交门禁：试运行全部通过后才允许提交/发布

---

## 7. 质量评估指标

- 覆盖度：接口覆盖率、业务流程覆盖率
- 可执行性：首次执行通过率
- 稳定性：同一用例多次执行通过率
- 参数化有效率：动态字段识别准确率
- 人工修改比例：生成后需手工调整占比

---

## 8. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 录制数据噪声多 | 生成无价值用例 | 规则过滤 + AI 分类 |
| 动态参数识别不准 | 回放失败 | 参数化规则 + 可视化编辑 |
| 文档质量参差 | 生成偏差 | RAG 检索 + 人工确认 |
| 无向量库基础 | 进度拖延 | 选型 Qdrant，先 MVP |
| 未来脱敏需求 | 数据合规 | 预留脱敏规则接口 |

---

## 9. MVP 分阶段实施

### Phase A（流量录制回放 MVP）
- 录制文件上传
- 基础解析与过滤
- 生成单接口用例
- 人工确认与保存

### Phase B（流量串联增强）
- 会话切分
- 变量提取与参数化
- 多步骤场景生成

### Phase C（RAG MVP）
- Markdown 文档入库
- Qdrant 向量检索
- 生成单接口用例

### Phase D（RAG 场景增强）
- 文档驱动多步骤场景生成
- 自动断言与变量提取建议

---

## 10. 后续扩展
- 脱敏与合规模块
- 用例版本管理
- 自动回归与调度
- 多模型策略（小模型 + 大模型）

---

## 11. 确认信息（已确认）
- 用例名称由 AI 在生成阶段自动生成，可手动调整
- 项目需手动创建，生成入口在项目内触发（录制或文档解析）
- 生成后必须执行测试，全部通过后才允许提交；失败则修改重试

---

**结论**：两条方案均可落地，建议双轨并行，统一输出为场景/用例结构，保证执行与报告复用现有体系。
