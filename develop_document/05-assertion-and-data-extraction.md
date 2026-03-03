# 断言配置与数据提取功能

## 功能概述

为测试用例添加断言配置和数据提取功能，实现接口测试的核心验证能力和变量复用机制。

## 一、断言配置功能

### 1.1 功能描述

断言配置允许用户为API测试用例定义多种验证规则，在测试执行时自动验证响应数据是否符合预期。

### 1.2 断言类型

| 类型 | 说明 | 目标字段 | 支持操作符 |
|------|------|----------|------------|
| status_code | HTTP状态码断言 | 自动 | 等于、不等于、包含、范围 |
| response_time | 响应时间断言 | 自动 | 小于、小于等于、大于、大于等于 |
| response_body | 响应体断言 | 需指定 | 包含、不包含、等于、不等于、正则匹配、JSON路径 |
| response_headers | 响应头断言 | 需指定 | 包含、不包含、等于、不等于 |
| json_value | JSON值提取断言 | JSONPath | 等于、不等于、包含、大于、小于、为空、不为空 |
| text_contains | 文本包含断言 | 自动 | 包含、不包含 |
| json_schema | JSON Schema验证 | 自动 | 有效、无效 |

### 1.3 实现思路

**后端实现：**
- 创建 `ApiTestCaseAssertion` 模型，包含：测试用例关联、断言类型、目标字段、操作符、期望值、启用状态、排序
- 提供 CRUD API 端点：`/test-cases/{id}/assertions/`
- 完善 `AssertionEngine` 类，实现7种断言类型的验证逻辑
- 在测试执行时自动调用断言引擎，返回断言结果

**前端实现：**
- 使用现有 `AssertionConfig.vue` 组件
- 添加 API 调用方法 `assertionApi`
- 集成到测试用例编辑页面
- 在测试结果页面展示断言结果

### 1.4 断言执行流程

1. 测试执行完成后，获取响应数据
2. 根据断言配置类型调用对应的验证方法
3. 比较实际值与期望值
4. 记录断言结果（通过/失败、错误信息）
5. 汇总断言结果，影响测试用例的通过/失败状态

## 二、数据提取功能

### 2.1 功能描述

数据提取功能允许用户从API响应中提取变量值，存储后在后续请求中复用，实现测试用例间的数据传递。

### 2.2 提取类型

| 类型 | 说明 | 表达式格式 | 示例 |
|------|------|------------|------|
| regex | 正则表达式提取 | 正则模式 | `"token":"([^"]+)"` |
| json_path | JSON路径提取 | JSONPath | `$.data.id` |
| xpath | XPath表达式 | XPath | `//div[@class="content"]/text()` |
| css_selector | CSS选择器 | CSS选择器 | `.user-id` |
| header | Header提取 | Header名称 | `Authorization` |
| cookie | Cookie提取 | Cookie名称 | `session_id` |

### 2.3 提取范围

- **响应体(body)**: 从响应体内容中提取
- **响应头(headers)**: 从响应头中提取
- **URL**: 从请求/响应URL中提取

### 2.4 变量作用域

- **局部变量**: 仅在当前测试用例中有效，格式：`${local.variable_name}`
- **全局变量**: 在整个测试执行中有效，格式：`${global.variable_name}`
- **环境变量**: 从环境配置中读取，格式：`${env.variable_name}`

### 2.5 实现思路

**后端实现：**
- 创建 `ApiTestCaseExtraction` 模型，包含：测试用例关联、变量名、提取类型、提取表达式、默认值、启用状态、作用域
- 提供 CRUD API 端点：`/test-cases/{id}/extractions/`
- 实现 `ExtractionEngine` 类，支持6种提取类型
- 在测试执行时先执行数据提取，再进行变量替换

**前端实现：**
- 使用现有 `VariableExtraction.vue` 组件
- 添加 API 调用方法 `extractionApi`
- 集成到测试用例编辑页面
- 显示已提取的变量值

### 2.6 变量替换流程

1. 在发送请求前，扫描请求URL、参数、头、体中的变量占位符
2. 按优先级解析变量：环境变量 > 全局变量 > 局部变量
3. 替换占位符为实际值
4. 发送完成请求后，执行数据提取
5. 将提取的值存储到对应作用域的变量池中

## 三、数据模型设计

### 3.1 断言配置模型

```python
class ApiTestCaseAssertion(models.Model):
    test_case = ForeignKey(ApiTestCase)
    assertion_type = CharField()  # 断言类型
    target = CharField()          # 目标字段
    operator = CharField()        # 操作符
    expected_value = TextField()  # 期望值
    is_enabled = BooleanField()   # 是否启用
    order = IntegerField()        # 排序
```

### 3.2 数据提取模型

```python
class ApiTestCaseExtraction(models.Model):
    test_case = ForeignKey(ApiTestCase)
    variable_name = CharField()       # 变量名
    extract_type = CharField()        # 提取类型
    extract_expression = TextField()  # 提取表达式
    default_value = TextField()       # 默认值
    is_enabled = BooleanField()       # 是否启用
    scope = CharField()               # 作用域: local/global
```

## 四、API设计

### 4.1 断言配置API

- `GET /api/v1/api-automation/test-cases/{id}/assertions/` - 获取断言列表
- `POST /api/v1/api-automation/test-cases/{id}/assertions/` - 创建断言
- `PUT /api/v1/api-automation/test-cases/{id}/assertions/{assertion_id}/` - 更新断言
- `DELETE /api/v1/api-automation/test-cases/{id}/assertions/{assertion_id}/` - 删除断言
- `POST /api/v1/api-automation/test-cases/{id}/assertions/batch/` - 批量操作

### 4.2 数据提取API

- `GET /api/v1/api-automation/test-cases/{id}/extractions/` - 获取提取配置列表
- `POST /api/v1/api-automation/test-cases/{id}/extractions/` - 创建提取配置
- `PUT /api/v1/api-automation/test-cases/{id}/extractions/{extraction_id}/` - 更新提取配置
- `DELETE /api/v1/api-automation/test-cases/{id}/extractions/{extraction_id}/` - 删除提取配置

## 五、执行引擎集成

测试执行流程更新：
1. 加载测试用例及断言配置、数据提取配置
2. 执行变量替换（环境变量、已提取的变量）
3. 发送HTTP请求
4. 执行数据提取，存储变量
5. 执行断言验证
6. 返回执行结果（包含断言结果和提取的变量）
