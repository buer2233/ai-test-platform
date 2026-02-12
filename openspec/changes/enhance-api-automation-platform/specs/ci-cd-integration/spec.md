# Capability: ci-cd-integration

CI/CD集成能力规格说明

## ADDED Requirements

### Requirement: CLI命令行工具

系统 SHALL 提供命令行工具以支持自动化测试执行。

#### Scenario: 通过CLI触发测试

**Given** 安装了 `api-test` CLI工具

**When** 执行命令：
```bash
api-test run --project 1 --environment 2
```

**Then** 应触发测试执行

**And** 显示执行进度

**And** 执行完成后显示摘要

**Example输出**:
```
Starting test execution...
[=====>     ] 25% (10/40) Running...
[=========> ] 50% (20/40) Running...
[============] 100% (40/40) Completed

Test Execution Summary:
- Total: 40
- Passed: 35 (87.5%)
- Failed: 4 (10%)
- Skipped: 1 (2.5%)
- Duration: 2m 15s
```

#### Scenario: 导出JUnit XML格式

**Given** 测试执行完成

**When** 使用命令：
```bash
api-test run --project 1 --output junit.xml --format junit
```

**Then** 应生成JUnit XML格式的报告

**And** 报告应包含所有测试用例结果

**And** 报告应能被CI/CD工具识别（如Jenkins、GitLab CI）

#### Scenario: 导出Allure报告格式

**Given** 需要生成Allure报告

**When** 使用命令：
```bash
api-test run --project 1 --output allure-results --format allure
```

**Then** 应生成Allure JSON格式的结果

**And** 可使用 `allure generate` 生成HTML报告

#### Scenario: 设置质量门禁

**Given** CI/CD流水线需要根据测试结果决定是否继续

**When** 使用命令：
```bash
api-test gate --project 1 --threshold 95 --fail-on-error
```

**Then** 如果通过率 >= 95%，退出码为0

**And** 如果通过率 < 95%，退出码为1

**And** 如果有错误，退出码为2

**And** CI/CD可根据退出码决定是否继续部署

#### Scenario: 查看历史执行记录

**Given** 需要查看测试执行历史

**When** 使用命令：
```bash
api-test history --project 1 --limit 10
```

**Then** 应显示最近10次执行记录

**And** 包含执行ID、状态、通过率、时间

---

### Requirement: Webhook事件通知

系统 SHALL 支持测试事件的外部通知。

#### Scenario: 测试完成通知

**Given** 配置了Webhook：
```yaml
url: https://ci.example.com/api/test-complete
event: test_execution.completed
```

**When** 测试执行完成

**Then** 应发送POST请求到配置的URL

**And** 请求体应包含：
```json
{
  "event": "test_execution.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "execution": {
    "id": 123,
    "project_id": 1,
    "status": "COMPLETED",
    "total": 40,
    "passed": 35,
    "failed": 4,
    "skipped": 1,
    "duration": 135
  }
}
```

**And** 请求头应包含签名：
```
X-Webhook-Signature: sha256=...
X-Webhook-Event: test_execution.completed
```

#### Scenario: 测试失败通知

**Given** 配置了失败事件Webhook

**When** 测试用例失败

**Then** 应立即发送失败通知

**And** 通知应包含失败详情

**And** 应包含断言失败信息

#### Scenario: Webhook重试机制

**Given** Webhook目标服务暂时不可用

**When** 发送Webhook失败

**Then** 应进行重试

**And** 重试间隔：30秒、2分钟、10分钟

**And** 最多重试3次

**And** 记录重试日志

#### Scenario: Webhook安全验证

**Given** 配置了Webhook密钥

**When** 发送Webhook请求

**Then** 应使用HMAC-SHA256计算签名

**And** 签名应基于请求体和密钥

**And** 接收方可验证签名确保消息完整性

---

### Requirement: 质量门禁配置

系统 SHALL 支持基于测试结果的质量门禁。

#### Scenario: 配置通过率门禁

**Given** 项目配置了质量门禁：
```yaml
gates:
  - type: pass_rate
    threshold: 95
    action: block
```

**When** 测试执行完成，通过率为93%

**Then** 应标记质量门禁失败

**And** 应阻止部署

**And** 应显示失败原因

#### Scenario: 配置关键用例门禁

**Given** 配置了关键用例门禁：
```yaml
gates:
  - type: critical_cases
    require_all_passed: true
    action: warn
```

**When** 有关键用例失败

**Then** 应显示警告

**And** 不应阻止部署（配置为warn）

**And** 应列出失败的关键用例

#### Scenario: 配置响应时间门禁

**Given** 配置了性能门禁：
```yaml
gates:
  - type: response_time
    endpoint: /api/users
    percentile: p95
    threshold: 200ms
    action: block
```

**When** P95响应时间为250ms

**Then** 应标记性能门禁失败

**And** 应阻止部署

#### Scenario: 质量趋势门禁

**Given** 配置了趋势门禁：
```yaml
gates:
  - type: trend
    metric: pass_rate
    comparison: vs_last_week
    threshold: -5%
    action: warn
```

**When** 相比上周通过率下降6%

**Then** 应触发警告

**And** 应显示趋势数据

---

### Requirement: Mock服务集成

系统 SHALL 支持内置Mock服务以减少外部依赖。

#### Scenario: 配置Mock响应

**Given** 配置了Mock规则：
```yaml
mocks:
  - url: /api/users/*
    method: GET
    response:
      status: 200
      body:
        data:
          - id: 1
            name: "测试用户"
```

**When** 启用Mock服务

**Then** 请求 `/api/users/1` 应返回Mock数据

**And** 不应调用真实API

#### Scenario: 动态Mock响应

**Given** 配置了动态Mock：
```yaml
mocks:
  - url: /api/users/${id}
    method: GET
    response:
      status: 200
      body:
        id: ${url.id}
        name: "用户${url.id}"
```

**When** 请求 `/api/users/123`

**Then** 应返回：
```json
{
  "id": 123,
  "name": "用户123"
}
```

#### Scenario: Mock状态管理

**Given** 配置了带状态的Mock

**When** 发送POST请求创建资源

**Then** Mock应记录创建的资源

**And** 后续GET请求应返回创建的资源

**And** 支持PUT和DELETE操作

---

### Requirement: 测试数据管理

系统 SHALL 支持测试数据的生成和管理。

#### Scenario: 生成测试数据

**Given** 配置了数据生成规则：
```yaml
data_generators:
  - name: user
    fields:
      name: ${random.name}
      email: ${random.email}
      age: ${random.int(18, 65)}
```

**When** 执行测试

**Then** 应自动生成测试数据

**And** 每次生成不同的数据

#### Scenario: 数据快照

**Given** 测试需要特定的数据状态

**When** 创建数据快照

**Then** 应保存当前数据库状态

**And** 应可在测试前恢复快照

**And** 测试完成后应自动清理

#### Scenario: 数据隔离

**Given** 多个测试并发执行

**When** 每个测试使用生成的数据

**Then** 测试数据应相互隔离

**And** 测试A不应访问测试B的数据

**And** 每个测试应有独立的数据空间

---

### Requirement: 环境配置管理

系统 SHALL 支持灵活的多环境配置。

#### Scenario: 环境变量覆盖

**Given** 有基础环境配置

**When** 需要在特定环境覆盖配置

**Then** 应支持变量继承和覆盖

**Example**:
```yaml
base:
  base_url: https://api.example.com
  timeout: 30000

production:
  inherits: base
  base_url: https://api.production.com
  timeout: 60000
```

#### Scenario: 敏感配置加密

**Given** 环境配置包含敏感信息（密码、Token）

**When** 保存配置

**Then** 敏感字段应加密存储

**And** 前端显示时应脱敏

**And** 使用时应自动解密

#### Scenario: 环境切换验证

**Given** 需要切换测试环境

**When** 用户选择新环境

**Then** 应验证环境连接

**And** 应显示连接状态

**And** 连接失败应提示错误
