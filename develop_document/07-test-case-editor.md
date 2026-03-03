# 测试用例编辑器开发文档

## 功能概述

测试用例编辑器是API自动化测试平台的核心功能模块，提供测试用例的创建、编辑、保存和测试请求执行等功能。

## 技术架构

### 前端技术栈
- Vue 3 Composition API (TypeScript)
- Element Plus UI组件库
- Pinia状态管理
- Vue Router路由管理

### 后端API
- Django REST Framework
- HTTP执行引擎服务
- 断言引擎服务
- 数据提取引擎服务

## 核心功能

### 1. 基本信息配置
- 用例名称、描述输入
- 请求方法选择（GET/POST/PUT/PATCH/DELETE）
- 所属项目和集合选择
- 请求URL配置

### 2. 请求参数配置
- **Query参数**：键值对表格形式编辑，支持动态增删
- **Headers**：请求头配置，支持自定义和常用预设
- **Body**：
  - JSON格式：支持语法高亮和格式验证
  - Form Data：表单数据，支持Text和File类型
  - Raw：原始文本输入

### 3. 断言配置
- 集成AssertionConfig组件
- 支持11种断言类型
- 支持多条件组合断言

### 4. 数据提取配置
- 集成VariableExtraction组件
- 支持6种提取类型
- 支持局部和全局变量作用域

### 5. 测试请求功能
- 选择测试环境
- 执行HTTP请求测试
- 实时显示请求结果（状态码、响应时间、响应体、响应头）
- 错误提示和异常处理

## 实现要点

### 组件结构
```
TestCaseCreate.vue (主组件)
├── 基本信息表单卡片
├── 请求参数配置卡片
├── 断言配置卡片 (AssertionConfig)
├── 数据提取配置卡片 (VariableExtraction)
├── 测试操作卡片
└── 测试结果对话框
```

### 状态管理
- 使用Pinia stores管理项目、集合、环境数据
- 表单数据使用reactive进行双向绑定
- 加载状态使用ref管理

### API集成
- testCaseApi：测试用例CRUD操作
- assertionApi：断言配置管理
- extractionApi：数据提取配置管理
- httpExecutorApi：测试请求执行
- environmentApi：环境配置加载

### 路由配置
- 创建路由：`/test-cases/create`
- 编辑路由：`/test-cases/:id/edit`
- 复用TestCaseCreate组件，通过props区分模式

## 关键代码逻辑

### 表单数据构建
- 将表格形式的参数转换为对象格式存储
- JSON Body自动解析和格式化
- Form Data转换为键值对对象

### 测试请求执行
1. 构建请求参数（包含环境base_url）
2. 调用httpExecutorApi.execute()
3. 处理响应并显示结果对话框
4. 错误处理和用户提示

### 数据保存流程
1. 验证表单必填项
2. 构建提交数据
3. 保存测试用例基本信息
4. 逐个保存断言配置
5. 逐个保存数据提取配置
6. 跳转回列表页

## 已知问题和解决方案

### 问题1：断言/提取保存400错误
- 原因：提交空数据时后端验证失败
- 解决：前端判断配置数组长度，为空时跳过保存

### 问题2：URL路径不一致
- 原因：httpExecutorApi路径缺少`/v1/api-automation`前缀
- 解决：统一使用API_URL常量管理路径前缀

## 测试建议

### 功能测试
1. 创建新的测试用例
2. 编辑已有测试用例
3. 测试请求执行功能
4. 验证断言配置保存
5. 验证数据提取配置保存

### 兼容性测试
1. 不同请求方法（GET/POST/PUT/PATCH/DELETE）
2. 不同Body类型（JSON/Form/Raw）
3. 不同环境下的测试请求

### 异常测试
1. 网络错误处理
2. 无效URL处理
3. 服务器错误处理
4. 权限错误处理

## 文件清单

| 文件路径 | 说明 |
|---------|------|
| VUE3/src/modules/api-automation/views/TestCase/TestCaseCreate.vue | 测试用例编辑器主组件 |
| VUE3/src/modules/api-automation/api/httpExecutor.ts | HTTP执行API |
| VUE3/src/modules/api-automation/api/testCase.ts | 测试用例API |
| VUE3/src/modules/api-automation/api/assertion.ts | 断言API |
| VUE3/src/modules/api-automation/api/extraction.ts | 数据提取API |
| VUE3/src/modules/api-automation/components/AssertionConfig.vue | 断言配置组件 |
| VUE3/src/modules/api-automation/components/VariableExtraction.vue | 数据提取组件 |

---

*文档版本: v1.0*
*创建日期: 2025-12-23*
