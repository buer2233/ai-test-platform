# 回收站与级联删除功能文档

## 一、需求概述

### 1.1 问题描述
当前系统存在以下问题：
1. 删除测试项目后，关联的测试集合和测试用例仍然存在
2. 删除操作缺乏预览机制，用户无法知晓会删除哪些关联数据
3. 删除后的数据无法恢复
4. 缺乏数据清理机制

### 1.2 功能目标
1. 实现级联逻辑删除：删除父数据时自动逻辑删除所有子数据
2. 删除预览：显示即将被删除的关联数据详情
3. 回收站功能：支持查看、恢复、彻底删除逻辑删除的数据
4. 内部物理删除：提供专用的物理删除接口供研发运维使用

## 二、数据模型关系

### 2.1 当前关系结构
```
ApiProject (项目)
├── ApiCollection (集合) [CASCADE]
│   └── ApiTestCase (测试用例) [SET_NULL]
├── ApiTestEnvironment (环境) [CASCADE]
├── ApiTestExecution (执行) [CASCADE]
│   ├── ApiTestReport (报告) [CASCADE]
│   └── ApiTestResult (结果) [CASCADE]
└── ApiDataDriver (数据驱动) [CASCADE]

ApiTestCase
├── ApiTestCaseAssertion (断言) [CASCADE]
└── ApiTestCaseExtraction (提取) [CASCADE]
```

### 2.2 级联删除规则
| 父模型 | 子模型 | 级联操作 |
|--------|--------|----------|
| ApiProject | ApiCollection | 逻辑删除 |
| ApiProject | ApiTestEnvironment | 逻辑删除 |
| ApiProject | ApiDataDriver | 逻辑删除 |
| ApiCollection | ApiTestCase | 逻辑删除 |
| ApiTestCase | ApiTestCaseAssertion | 逻辑删除 |
| ApiTestCase | ApiTestCaseExtraction | 逻辑删除 |
| ApiTestEnvironment | ApiTestExecution | 逻辑删除 |
| ApiTestExecution | ApiTestResult | 逻辑删除 |
| ApiTestExecution | ApiTestReport | 逻辑删除 |

## 三、接口设计

### 3.1 删除预览接口

#### 预览项目删除影响
```
GET /api/v1/api-automation/projects/{id}/preview-delete/
Response: {
  "target": {"id": 1, "name": "测试项目A", "type": "project"},
  "cascade_count": {
    "collections": 5,
    "test_cases": 20,
    "environments": 3,
    "data_drivers": 2
  },
  "cascade_details": [
    {"type": "collection", "count": 5, "names": ["集合1", "集合2", ...]},
    {"type": "test_case", "count": 20},
    {"type": "environment", "count": 3, "names": ["开发环境", ...]}
  ]
}
```

#### 预览集合删除影响
```
GET /api/v1/api-automation/collections/{id}/preview-delete/
Response: {
  "target": {"id": 1, "name": "集合1", "type": "collection"},
  "cascade_count": {
    "test_cases": 10
  },
  "cascade_details": [...]
}
```

### 3.2 级联逻辑删除接口

#### 项目级联删除
```
DELETE /api/v1/api-automation/projects/{id}/?cascade=true
Response: {
  "deleted": {"id": 1, "name": "测试项目A", "type": "project"},
  "cascade_deleted": {
    "collections": 5,
    "test_cases": 20,
    "environments": 3,
    "data_drivers": 2
  }
}
```

### 3.3 回收站接口

#### 回收站列表
```
GET /api/v1/api-automation/recycle-bin/
Query: ?type=project&page=1&page_size=20
Response: {
  "results": [...],
  "count": 100
}
```

#### 恢复数据
```
POST /api/v1/api-automation/recycle-bin/{type}/{id}/restore/
Response: {
  "restored": {...},
  "cascade_restored": {...}
}
```

#### 彻底删除
```
DELETE /api/v1/api-automation/recycle-bin/{type}/{id}/permanent-delete/
Response: {
  "permanent_deleted": {...}
}
```

### 3.4 内部物理删除接口（仅供研发运维）

```
POST /api/v1/internal/cleanup/permanent-delete/
Headers: X-Internal-Auth: {internal_key}
Body: {
  "model": "ApiProject",
  "ids": [1, 2, 3],
  "cascade": true
}
```

## 四、实现思路

### 4.1 级联逻辑删除服务
创建`CascadeSoftDeleteService`服务类：
- `preview_delete(obj)`: 预览删除影响
- `cascade_delete(obj)`: 执行级联逻辑删除
- `restore(obj)`: 恢复数据及其子数据

### 4.2 回收站管理
创建`RecycleBinManager`：
- `get_deleted_items(type, user)`: 获取已删除数据
- `restore_item(type, id)`: 恢复数据
- `permanent_delete(type, id)`: 彻底删除

### 4.3 物理删除服务
创建`PhysicalDeleteService`（内部使用）：
- 验证内部权限
- 执行物理级联删除
- 记录删除日志

## 五、前端设计

### 5.1 删除确认对话框
- 显示即将删除的数据名称
- 展示级联删除的关联数据统计
- 确认后执行删除

### 5.2 回收站页面
- 支持按类型筛选（项目/集合/测试用例等）
- 支持搜索
- 支持批量恢复/删除
- 显示删除时间

## 六、权限控制

- 普通用户：只能操作自己的数据
- 超级用户：可操作所有数据
- 内部接口：需内部认证密钥
