# 方案B：RAG 文档解析生成用例（仅本方案）

**版本**: v1.0
**日期**: 2026-03-03
**范围**: 仅覆盖“文档解析 + RAG 生成用例”方案，不包含流量录制回放。

---

## 1. 方案边界与目标

- 输入：项目内上传的 Markdown 接口/功能文档
- 输出：ApiTestCase + ApiTestScenario（草稿/已提交），并可执行与生成报告
- 过程：向量检索 + 生成 + 人工确认 + 试运行门禁（全部通过才允许提交）
- 质量门禁：必须完成全部测试用例并通过，功能开发才视为完成。

---

## 2. 向量库选型

- **推荐**：Qdrant
- **原因**：部署简单、单容器、RESTful API、Python SDK 完整

---

## 3. 数据模型（详细字段）

### 3.1 ApiDocSource（文档源）

```python
class ApiDocSource(models.Model):
    project = models.ForeignKey(ApiProject, on_delete=models.CASCADE, related_name='doc_sources')

    name = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=20, default='MARKDOWN')
    version = models.CharField(max_length=50, blank=True)

    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[('UPLOADED', '已上传'), ('INGESTING', '入库中'), ('INGESTED', '已入库'), ('FAILED', '失败')],
        default='UPLOADED'
    )
    chunk_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
```

### 3.2 ApiDocChunk（文档切片）

```python
class ApiDocChunk(models.Model):
    doc_source = models.ForeignKey(ApiDocSource, on_delete=models.CASCADE, related_name='chunks')

    chunk_index = models.IntegerField()
    heading_path = models.CharField(max_length=500, blank=True)  # 例如 H1/H2 标题路径
    content = models.TextField()

    token_count = models.IntegerField(default=0)
    embedding_id = models.CharField(max_length=100, blank=True)  # 对应向量库主键
    metadata = JSONField(default=dict, blank=True)  # endpoint、method、module 等

    created_time = models.DateTimeField(auto_now_add=True)
```

### 3.3 ApiVectorStoreConfig（向量库配置）

```python
class ApiVectorStoreConfig(models.Model):
    project = models.OneToOneField(ApiProject, on_delete=models.CASCADE, related_name='vector_config')

    provider = models.CharField(max_length=20, default='QDRANT')
    endpoint = models.CharField(max_length=200, default='http://localhost:6333')
    collection = models.CharField(max_length=200)

    embedding_model = models.CharField(max_length=100)  # 例如 text-embedding-3-large
    embedding_dim = models.IntegerField(default=1536)

    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
```

### 3.4 ApiRagQuery（生成请求记录）

```python
class ApiRagQuery(models.Model):
    project = models.ForeignKey(ApiProject, on_delete=models.CASCADE, related_name='rag_queries')

    query_text = models.TextField()
    filters = JSONField(default=dict, blank=True)  # 模块/接口/标签等

    retrieved_chunk_ids = JSONField(default=list, blank=True)
    model_name = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=[('PENDING', '待处理'), ('RUNNING', '处理中'), ('COMPLETED', '完成'), ('FAILED', '失败')],
        default='PENDING'
    )
    error_info = JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
```

### 3.5 ApiGeneratedArtifact（生成结果与追溯）

> 同方案A，仅 source_type 设为 RAG，source_id 对应 ApiRagQuery.id

---

## 4. 生成与门禁流程

1. 文档上传 -> 切分 -> 向量化入库
2. RAG 检索 -> 生成用例草稿
3. 人工确认 -> 试运行
4. 全部通过 -> 提交（落库为 ApiTestCase/Scenario）
5. 失败则修改并重试

---

## 4.1 TDD 工作流要求（本方案）

1. **先写测试**：以 `test_case/13B-rag-generation-test-cases.md` 为准，先补齐单元/集成/E2E 测试脚本，再写实现代码。
2. **测试必然失败**：首次运行必须失败（红灯），以验证测试有效。
3. **最小实现**：只写最小代码让测试通过（绿灯）。
4. **重构**：保持测试绿色前提下优化结构。
5. **覆盖率**：单元+集成+E2E 总覆盖率 >= 80%。
6. **提交门禁**：所有测试必须通过，否则禁止提交；失败则修复后重测直至全绿。

---

## 5. 接口与前端要点（简述）

- 后端接口必须带 project_id
- 前端入口位于“项目”上下文中触发文档解析与生成
- 生成向导支持需求输入、召回预览与可编辑生成结果

---

## 6. 方案独立性声明

本文件仅用于方案B（RAG 文档解析），方案A（流量录制回放）见 `develop_document/12A-traffic-based-generation.md`。
