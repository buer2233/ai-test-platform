# 仪表盘测试报告展示功能

## 功能概述

在仪表盘页面展示接口自动化测试报告，支持多维度查看测试结果、图表展示和快速执行操作。

## 一、页面布局设计

### 1.1 页面结构

| 区域 | 内容 | 说明 |
|------|------|------|
| 统计概览 | 测试概况数据 | 总用例数、通过率、失败数、平均响应时间 |
| 环境维度 | 按环境分组的测试报告 | Tab切换不同环境，显示各环境测试结果 |
| 集合维度 | 按集合分组的测试报告 | Tab切换不同集合，显示各集合测试结果 |
| 图表展示 | 可视化图表 | 通过率饼图、用例分布柱状图、响应时间趋势图 |
| 测试结果列表 | 用例执行详情 | 支持筛选、排序、点击跳转用例详情 |

### 1.2 环境维度视图

```
┌─────────────────────────────────────────────────────────────┐
│ 测试报告 - 环境维度                          [环境] [集合] │
├─────────────────────────────────────────────────────────────┤
│ [开发环境] [测试环境] [预发布环境] [生产环境]              │
├─────────────────────────────────────────────────────────────┤
│ 统计卡片: 总用例50 | 通过42 | 失败5 | 跳过3 | 通过率84%    │
├─────────────────────────────────────────────────────────────┤
│ 图表区域:                                                  │
│ - 通过率饼图                                               │
│ - 用例状态柱状图                                           │
│ - 响应时间分布图                                           │
├─────────────────────────────────────────────────────────────┤
│ 操作按钮: [全部执行] [重试失败] [导出报告]                │
├─────────────────────────────────────────────────────────────┤
│ 用例列表: [全部] [通过] [失败] [跳过]                      │
│ ┌──────┬────────┬────────┬────────┬────────┬────────┐    │
│ │用例名│状态    │响应时间│操作    │        │        │    │
│ ├──────┼────────┼────────┼────────┼────────┼────────┤    │
│ │...   │...     │...     │查看详情 │        │        │    │
│ └──────┴────────┴────────┴────────┴────────┴────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 集合维度视图

```
┌─────────────────────────────────────────────────────────────┐
│ 测试报告 - 集合维度                          [环境] [集合] │
├─────────────────────────────────────────────────────────────┤
│ [用户管理] [订单接口] [支付接口] [商品接口]                 │
├─────────────────────────────────────────────────────────────┤
│ 统计卡片: 总用例20 | 通过18 | 失败2 | 跳过0 | 通过率90%    │
├─────────────────────────────────────────────────────────────┤
│ 图表和用例列表（同上）                                       │
└─────────────────────────────────────────────────────────────┘
```

## 二、数据模型设计

### 2.1 仪表盘数据结构

```typescript
// 仪表盘统计数据
interface DashboardStats {
  totalCases: number        // 总用例数
  passedCases: number       // 通过用例数
  failedCases: number       // 失败用例数
  skippedCases: number      // 跳过用例数
  passRate: number          // 通过率(百分比)
  avgResponseTime: number   // 平均响应时间
  totalExecutions: number   // 总执行次数
}

// 环境维度报告
interface EnvironmentReport {
  environmentId: number
  environmentName: string
  stats: DashboardStats
  recentExecution: ApiTestExecution | null
  testResults: ApiTestResult[]
}

// 集合维度报告
interface CollectionReport {
  collectionId: number
  collectionName: string
  stats: DashboardStats
  recentExecution: ApiTestExecution | null
  testResults: ApiTestResult[]
}

// 图表数据
interface ChartData {
  passRatePie: {
    passed: number
    failed: number
    skipped: number
  }
  statusDistribution: {
    passed: number
    failed: number
    skipped: number
    error: number
  }
  responseTimeTrend: {
    timestamps: string[]
    avgTimes: number[]
  }
  methodDistribution: {
    GET: number
    POST: number
    PUT: number
    DELETE: number
    PATCH: number
  }
}
```

## 三、功能实现

### 3.1 后端API设计

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/api-automation/dashboard/stats/` | GET | 获取仪表盘总体统计数据 |
| `/api/v1/api-automation/dashboard/environment-reports/` | GET | 按环境维度获取测试报告 |
| `/api/v1/api-automation/dashboard/collection-reports/` | GET | 按集合维度获取测试报告 |
| `/api/v1/api-automation/dashboard/chart-data/` | GET | 获取图表数据 |
| `/api/v1/api-automation/dashboard/execute-environment/` | POST | 执行指定环境的所有用例 |
| `/api/v1/api-automation/dashboard/execute-collection/` | POST | 执行指定集合的所有用例 |
| `/api/v1/api-automation/dashboard/retry-failed/` | POST | 重试失败的用例 |

### 3.2 前端组件设计

| 组件 | 功能 |
|------|------|
| `DashboardOverview.vue` | 概览统计卡片组件 |
| `EnvironmentReports.vue` | 环境维度报告组件 |
| `CollectionReports.vue` | 集合维度报告组件 |
| `TestResultCharts.vue` | 图表展示组件 |
| `TestResultList.vue` | 测试结果列表组件 |
| `ExecutionActions.vue` | 执行操作组件 |

### 3.3 图表展示

**通过率饼图**
- 使用 echarts 或 vue-echarts
- 显示通过、失败、跳过的比例
- 点击扇区可筛选对应状态的用例

**用例状态柱状图**
- X轴：测试环境/集合
- Y轴：用例数量
- 分组显示：通过、失败、跳过

**响应时间趋势图**
- X轴：执行时间
- Y轴：平均响应时间
- 折线图展示

### 3.4 一键执行功能

**执行环境所有用例**
```
POST /api/v1/api-automation/dashboard/execute-environment/
Body: {
  environment_id: number,
  include_all: boolean
}
```

**执行集合所有用例**
```
POST /api/v1/api-automation/dashboard/execute-collection/
Body: {
  collection_id: number,
  environment_id: number
}
```

**重试失败用例**
```
POST /api/v1/api-automation/dashboard/retry-failed/
Body: {
  execution_id: number,  // 执行记录ID
  environment_id: number,
  scope: 'environment' | 'collection'
}
```

## 四、跳转功能

### 4.1 点击跳转逻辑

| 点击位置 | 跳转目标 | 说明 |
|----------|----------|------|
| 用例名称 | 测试用例详情页 | `/test-cases/:id` |
| 查看详情 | 测试结果详情页 | `/executions/:id/results/:result_id` |
| 集合名称 | 集合详情页 | `/collections/:id` |
| 环境名称 | 环境详情页 | `/environments/:id` |
| 统计卡片 | 对应列表页 | 根据卡片类型跳转 |

### 4.2 测试用例详情页

显示内容：
- 用例基本信息（名称、方法、URL）
- 请求配置（Headers、Params、Body）
- 断言配置
- 数据提取配置
- 执行历史

## 五、数据刷新策略

- **自动刷新**：每30秒自动刷新仪表盘数据
- **手动刷新**：提供刷新按钮
- **实时更新**：WebSocket连接（可选，用于执行状态实时推送）

## 六、性能优化

- 分页加载测试结果（每页20条）
- 图表数据缓存（5分钟）
- 虚拟滚动处理大量用例
- 懒加载图表组件
