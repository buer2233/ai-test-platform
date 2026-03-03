# 方案A：流量录制回放生成用例（仅本方案）

**版本**: v1.0
**日期**: 2026-03-03
**范围**: 仅覆盖“流量录制回放生成用例”方案，不包含 RAG 文档解析。

---

## 1. 方案边界与目标

- 输入：代理抓包得到的请求/响应数据（JSON/HAR），由用户在项目内触发上传/解析。
- 输出：ApiTestCase + ApiTestScenario（草稿/已提交），并可执行与生成报告。
- 过程：自动生成 + 人工确认 + 试运行门禁（全部通过才允许提交）。
- 质量门禁：必须完成全部测试用例并通过，功能开发才视为完成。

---

## 2. 数据模型（详细字段）

> 说明：字段类型以 Django 模型为参考，可按现有项目风格调整。

### 2.1 ApiTrafficCapture（录制任务）

```python
class ApiTrafficCapture(models.Model):
    project = models.ForeignKey(ApiProject, on_delete=models.CASCADE, related_name='traffic_captures')
    name = models.CharField(max_length=200, verbose_name='录制名称')
    description = models.TextField(blank=True, null=True)

    capture_type = models.CharField(
        max_length=20,
        choices=[('PROXY_UPLOAD', '代理上传'), ('PROXY_LIVE', '代理实时')],
        default='PROXY_UPLOAD'
    )
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_format = models.CharField(max_length=20, default='JSON')
    file_size = models.IntegerField(null=True, blank=True)
    content_hash = models.CharField(max_length=64, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[('UPLOADED', '已上传'), ('PARSING', '解析中'), ('PARSED', '已解析'), ('FAILED', '解析失败')],
        default='UPLOADED'
    )
    total_entries = models.IntegerField(default=0)
    filtered_entries = models.IntegerField(default=0)
    sessions_count = models.IntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
```

### 2.2 ApiTrafficSession（会话摘要）

```python
class ApiTrafficSession(models.Model):
    project = models.ForeignKey(ApiProject, on_delete=models.CASCADE, related_name='traffic_sessions')
    capture = models.ForeignKey(ApiTrafficCapture, on_delete=models.CASCADE, related_name='sessions')

    session_key = models.CharField(max_length=128, db_index=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_ms = models.IntegerField(default=0)
    entry_count = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[('READY', '可生成'), ('FILTERED', '已过滤'), ('FAILED', '失败')],
        default='READY'
    )
    tags = JSONField(default=list, blank=True)  # 业务标签/模块标签

    created_time = models.DateTimeField(auto_now_add=True)
```

### 2.3 ApiTrafficEntry（标准化请求/响应）

```python
class ApiTrafficEntry(models.Model):
    session = models.ForeignKey(ApiTrafficSession, on_delete=models.CASCADE, related_name='entries')

    request_method = models.CharField(max_length=10)
    request_url = models.TextField()
    request_headers = JSONField(default=dict, blank=True)
    request_params = JSONField(default=dict, blank=True)
    request_body = JSONField(default=dict, blank=True)  # 或 TextField

    response_status = models.IntegerField(null=True, blank=True)
    response_headers = JSONField(default=dict, blank=True)
    response_body = JSONField(default=dict, blank=True)  # 或 TextField
    response_time_ms = models.IntegerField(default=0)

    error_info = JSONField(default=dict, blank=True)
    fingerprint = models.CharField(max_length=64, db_index=True)  # 去重用
    is_valuable = models.BooleanField(default=True)
    filter_reason = models.CharField(max_length=200, blank=True)

    created_time = models.DateTimeField(auto_now_add=True)
```

### 2.4 ApiTrafficVariableRule（变量提取规则）

```python
class ApiTrafficVariableRule(models.Model):
    entry = models.ForeignKey(ApiTrafficEntry, on_delete=models.CASCADE, related_name='variable_rules')

    variable_name = models.CharField(max_length=100)
    source_type = models.CharField(
        max_length=20,
        choices=[('JSONPATH', 'JSONPath'), ('REGEX', 'Regex'), ('HEADER', 'Header')]
    )
    expression = models.CharField(max_length=500)

    target_scope = models.CharField(
        max_length=20,
        choices=[('SCENARIO', '场景变量'), ('GLOBAL', '全局变量')],
        default='SCENARIO'
    )

    created_time = models.DateTimeField(auto_now_add=True)
```

### 2.5 ApiGeneratedArtifact（生成结果与追溯）

```python
class ApiGeneratedArtifact(models.Model):
    project = models.ForeignKey(ApiProject, on_delete=models.CASCADE, related_name='generated_artifacts')

    source_type = models.CharField(
        max_length=20,
        choices=[('TRAFFIC', '流量录制'), ('RAG', '文档生成')]
    )
    source_id = models.IntegerField()  # 对应 ApiTrafficSession.id

    artifact_type = models.CharField(
        max_length=20,
        choices=[('TEST_CASE', '单接口用例'), ('SCENARIO', '场景用例')]
    )
    name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=[('DRAFT', '草稿'), ('READY', '可提交'), ('COMMITTED', '已提交'), ('FAILED', '失败')],
        default='DRAFT'
    )

    payload = JSONField(default=dict)  # 生成的用例草稿内容
    preview_diff = JSONField(default=dict, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
```

---

## 3. 流程与门禁

1. 录制上传 -> 解析 -> 会话切分
2. 过滤与参数化 -> 生成用例草稿
3. 人工确认 -> 试运行
4. 全部通过 -> 提交（落库为 ApiTestCase/Scenario）
5. 失败则修改并重试

--- 

## 3.1 TDD 工作流要求（本方案）

1. **先写测试**：以 `test_case/13A-traffic-generation-test-cases.md` 为准，先补齐单元/集成/E2E 测试脚本，再写实现代码。
2. **测试必然失败**：首次运行必须失败（红灯），以验证测试有效。
3. **最小实现**：只写最小代码让测试通过（绿灯）。
4. **重构**：保持测试绿色前提下优化结构。
5. **覆盖率**：单元+集成+E2E 总覆盖率 >= 80%。
6. **提交门禁**：所有测试必须通过，否则禁止提交；失败则修复后重测直至全绿。

---

## 4. 接口与前端要点（简述）

- 后端接口必须带 project_id
- 前端入口位于“项目”上下文中触发录制与生成
- 预览页支持编辑变量/断言/步骤顺序

---

## 5. 方案独立性声明

本文件仅用于方案A（流量录制回放），方案B（RAG 文档解析）见 `develop_document/12B-rag-doc-generation.md`。
