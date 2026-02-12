# Capability: test-execution-engine

测试执行引擎能力规格说明

## ADDED Requirements

### Requirement: 支持嵌套变量访问

测试平台 SHALL 支持嵌套变量访问，以便从复杂的响应数据中提取嵌套字段。

#### Scenario: 从嵌套JSON响应中提取用户ID

**Given** 一个返回嵌套JSON数据的API响应：
```json
{
  "data": {
    "user": {
      "profile": {
        "id": 12345,
        "name": "张三"
      }
    }
  }
}
```

**When** 用户在后续请求中使用变量 `${response.data.user.profile.id}`

**Then** 变量应被正确解析为 `12345`

**And** 请求URL应正确替换为 `/api/users/12345`

#### Scenario: 使用默认值处理缺失字段

**Given** 响应数据中缺少某些字段

**When** 用户使用带默认值的变量 `${missing.field.value|100}`

**Then** 变量应解析为默认值 `100`

**And** 请求不应因为变量缺失而失败

#### Scenario: 支持数组索引访问

**Given** 响应数据包含数组：
```json
{
  "items": [
    {"id": 1, "name": "项目1"},
    {"id": 2, "name": "项目2"}
  ]
}
```

**When** 用户使用变量 `${response.items.0.id}`

**Then** 变量应正确解析为 `1`

---

### Requirement: 支持测试用例生命周期钩子

测试平台 SHALL 在测试用例执行前后支持自定义操作钩子。

#### Scenario: 执行前置SQL准备测试数据

**Given** 一个测试用例配置了前置钩子：
```yaml
before_test_case:
  - action_type: sql
    config:
      query: "INSERT INTO users (name, email) VALUES ('test', 'test@example.com')"
```

**When** 测试用例开始执行

**Then** 前置钩子应首先执行SQL语句

**And** 数据库中应存在测试用户数据

**And** 测试用例应正常执行

#### Scenario: 执行后置清理操作

**Given** 一个测试用例配置了后置钩子：
```yaml
after_test_case:
  - action_type: sql
    config:
      query: "DELETE FROM users WHERE email = 'test@example.com'"
  - action_type: delay
    config:
      seconds: 1
```

**When** 测试用例执行完成（无论成功或失败）

**Then** 后置钩子应依次执行

**And** 测试数据应被清理

#### Scenario: 支持HTTP请求钩子

**Given** 一个测试用例需要在执行前调用登录接口

**When** 配置前置钩子：
```yaml
before_test_case:
  - action_type: http
    config:
      url: /api/login
      method: POST
      body:
        username: admin
        password: secret
      extract: token from $.data.token
```

**Then** 钩子应执行HTTP请求

**And** 提取的token应可用于主测试用例

---

### Requirement: 支持条件分支执行

测试平台 SHALL 支持基于响应数据的条件分支，实现动态测试流程。

#### Scenario: 根据响应状态码执行不同操作

**Given** 测试用例配置了条件分支：
```yaml
conditions:
  - if: "${response.status} == 200"
    then:
      - extract: user_id from $.data.id
      - execute: verify_profile
  - elif: "${response.status} == 401"
    then:
      - execute: refresh_token
      - execute: retry_request
  - else:
      - execute: report_error
```

**When** API响应状态码为200

**Then** 应执行第一个分支的操作

**And** 应提取user_id并执行verify_profile

**And** 不应执行其他分支

#### Scenario: 支持复杂条件表达式

**Given** 配置条件：`${response.status} == 200 && response.data.count > 0`

**When** 响应状态为200且count大于0

**Then** 条件应评估为true

**And** 对应分支应被执行

#### Scenario: 支持字符串匹配条件

**Given** 配置条件：`${response.message} contains 'success'}`

**When** 响应消息为"Operation successful"

**Then** 条件应评估为true

---

### Requirement: 支持测试用例依赖管理

测试平台 SHALL 支持测试用例之间的依赖关系管理。

#### Scenario: 顺序执行依赖的测试用例

**Given** 测试用例B依赖于测试用例A

**When** 执行测试计划

**Then** 测试用例A应首先执行

**And** 只有A成功完成后，B才开始执行

**And** B可以使用A提取的变量

#### Scenario: 依赖失败时跳过后续用例

**Given** 测试用例B依赖于测试用例A

**When** 测试用例A执行失败

**Then** 测试用例B应被标记为SKIPPED

**And** B不应执行

#### Scenario: 支持多依赖关系

**Given** 测试用例C同时依赖于A和B

**When** 执行测试计划

**Then** A和B应可以并发执行

**And** 只有A和B都成功后，C才执行

---

### Requirement: 支持并发执行测试用例

测试平台 SHALL 支持并发执行独立的测试用例以提高执行效率。

#### Scenario: 并发执行无依赖的测试用例

**Given** 有10个无依赖关系的测试用例

**When** 配置并发度为4

**Then** 最多4个用例应同时执行

**And** 总执行时间应显著少于顺序执行

**And** 所有测试结果应正确记录

#### Scenario: 并发执行时变量隔离

**Given** 测试用例A和B同时执行

**And** A提取变量 `user_id = 1`

**And** B提取变量 `user_id = 2`

**When** A和B同时使用 `${user_id}`

**Then** A应使用值1

**And** B应使用值2

**And** 变量不应相互干扰

#### Scenario: 正确处理并发执行中的错误

**Given** 3个测试用例并发执行

**When** 其中1个用例失败

**Then** 其他用例应继续执行

**And** 失败用例的错误应独立记录

---

### Requirement: 支持循环迭代执行

测试平台 SHALL 支持数据驱动的循环迭代执行。

#### Scenario: 基于数据源的循环执行

**Given** 配置了数据源：
```yaml
data_source:
  type: csv
  file: test_data.csv
  # 包含: username, password, expected_status
```

**And** 配置循环：
```yaml
loop:
  over: ${data_source}
  as: row
  execute:
    - request:
        url: /api/login
        body:
          username: ${row.username}
          password: ${row.password}
```

**When** 执行测试

**Then** 测试应对数据源的每一行执行一次

**And** 每次迭代使用不同的数据

**And** 所有迭代结果应被记录

#### Scenario: 支持固定次数循环

**Given** 配置循环：
```yaml
loop:
  times: 5
  execute:
    - request:
        url: /api/test
```

**When** 执行测试

**Then** 测试应执行5次

#### Scenario: 支持循环中断条件

**Given** 配置循环：
```yaml
loop:
  over: ${test_items}
  until: "${response.status} != 200"
  execute:
    - request: ...
```

**When** 某次迭代返回非200状态码

**Then** 循环应中断

**And** 后续迭代不再执行
