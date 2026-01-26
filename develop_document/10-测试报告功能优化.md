# 测试报告功能优化 - 功能文档

## 1. 功能概述

将现有的仪表盘页面优化为完整的测试报告页面，提供更全面、更易用的测试报告展示和操作功能。

## 2. 功能需求

### 2.1 数据模型扩展

#### 2.1.1 ApiCollection 模型新增字段

| 字段名 | 类型 | 说明 | 是否必填 |
|--------|------|------|----------|
| owner | ForeignKey | 负责人（关联User） | 否 |
| module | CharField | 所属模块 | 否 |

```python
# ApiCollection 模型新增
owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='collections')
module = models.CharField(max_length=100, null=True, blank=True, verbose_name='所属模块')
```

#### 2.1.2 ApiTestCase 模型新增字段

| 字段名 | 类型 | 说明 | 是否必填 |
|--------|------|------|----------|
| owner | ForeignKey | 负责人（关联User） | 否 |
| module | CharField | 所属模块 | 否 |

```python
# ApiTestCase 模型新增
owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='test_cases')
module = models.CharField(max_length=100, null=True, blank=True, verbose_name='所属模块')
```

### 2.2 页面布局

#### 2.2.1 顶部筛选栏

提供多维度的筛选功能，包括：

| 筛选项 | 类型 | 说明 |
|--------|------|------|
| 项目 | 下拉选择 | 选择特定项目查看报告 |
| 集合 | 下拉选择 | 选择特定集合查看报告 |
| 负责人 | 下拉选择 | 选择特定负责人查看报告 |
| 模块 | 下拉选择 | 选择特定模块查看报告 |
| 时间范围 | 日期选择 | 选择报告的时间范围 |

#### 2.2.2 统计概览卡片

展示四个核心统计卡片，每个卡片支持点击交互：

1. **总用例数卡片**
   - 显示：当前筛选条件下的总用例数
   - 点击：显示所有测试结果列表
   - 颜色：蓝色主题

2. **通过用例卡片**
   - 显示：通过用例数和通过率
   - 点击：筛选显示通过的测试结果
   - 颜色：绿色主题

3. **失败用例卡片**
   - 显示：失败用例数和失败率
   - 点击：筛选显示失败的测试结果
   - 颜色：红色主题

4. **跳过用例卡片**
   - 显示：跳过用例数
   - 点击：筛选显示跳过的测试结果
   - 颜色：灰色主题

#### 2.2.3 图表展示区域

**柱状图** - 测试执行统计
- X轴：状态（通过、失败、跳过、错误）
- Y轴：用例数量
- 交互：点击柱状图的某个状态，筛选显示对应状态的测试结果

**饼图** - 测试执行分布
- 扇区：通过、失败、跳过、错误
- 交互：点击饼图的某个扇区，筛选显示对应状态的测试结果

#### 2.2.4 维度切换Tab

支持两个维度的报告展示：

1. **环境维度Tab**
   - 展示每个测试环境的执行情况
   - 每个环境显示：总用例数、通过数、失败数、通过率、平均响应时间
   - 支持点击环境卡片查看该环境的详细测试结果

2. **项目维度Tab**
   - 展示每个测试项目的执行情况
   - 每个项目显示：总用例数、通过数、失败数、通过率、平均响应时间
   - 支持点击项目卡片查看该项目的详细测试结果

#### 2.2.5 测试结果列表

展示符合筛选条件的测试结果详情：

| 字段 | 说明 |
|------|------|
| 测试用例名称 | 显示测试用例名称，点击可查看详情 |
| 所属集合 | 显示所属测试集合 |
| 所属项目 | 显示所属测试项目 |
| 执行状态 | 显示执行状态（通过/失败/跳过/错误） |
| 响应时间 | 显示请求响应时间 |
| 执行时间 | 显示执行时间戳 |
| 负责人 | 显示用例负责人 |
| 模块 | 显示所属模块 |

#### 2.2.6 操作按钮区域

提供两个重试按钮：

1. **一键重试所有用例按钮**
   - 位置：测试结果列表上方
   - 功能：重试当前筛选条件下的所有失败用例
   - 前置条件：存在失败用例
   - 交互：点击后弹出环境选择对话框

2. **批量重试按钮**
   - 位置：测试结果列表的复选框操作栏
   - 功能：重试用户选中的失败用例
   - 前置条件：存在选中的失败用例
   - 交互：点击后弹出环境选择对话框

### 2.3 交互逻辑

#### 2.3.1 卡片点击交互

1. 用户点击统计卡片
2. 页面自动滚动到测试结果列表区域
3. 列表自动过滤显示对应状态的数据
4. 显示当前筛选条件提示

#### 2.3.2 图表点击交互

1. 用户点击柱状图或饼图的某个元素
2. 触发与卡片点击相同的筛选逻辑
3. 高亮显示被点击的图表元素

#### 2.3.3 维度切换交互

1. 用户切换环境/项目维度Tab
2. 更新维度报告区域的内容
3. 重置测试结果列表的筛选条件
4. 重新加载对应维度的测试结果

#### 2.3.4 重试交互流程

1. 用户点击重试按钮
2. 系统检查是否满足重试前置条件
3. 弹出环境选择对话框
4. 用户选择测试环境
5. 创建新的测试执行任务
6. 跳转到测试执行详情页面

### 2.4 API接口设计

#### 2.4.1 Dashboard 概览接口（更新）

**端点**: `GET /api/v1/api-automation/dashboard/`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 否 | 项目ID筛选 |
| collection_id | integer | 否 | 集合ID筛选 |
| owner_id | integer | 否 | 负责人ID筛选 |
| module | string | 否 | 模块名称筛选 |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |

**响应数据**:
```json
{
  "overview": {
    "total_projects": 10,
    "total_collections": 50,
    "total_test_cases": 500,
    "total_executions": 1000
  },
  "test_stats": {
    "total_cases": 500,
    "passed_cases": 450,
    "failed_cases": 30,
    "skipped_cases": 15,
    "error_cases": 5,
    "pass_rate": 90.0,
    "avg_response_time": 250
  },
  "recent_results": [...]
}
```

#### 2.4.2 环境维度报告接口（更新）

**端点**: `GET /api/v1/api-automation/dashboard/environment_reports/`

**请求参数**: 同上

**响应数据**:
```json
{
  "results": [
    {
      "environment_id": 1,
      "environment_name": "测试环境1",
      "project_id": 1,
      "project_name": "项目A",
      "base_url": "https://api.example.com",
      "stats": {
        "total": 100,
        "passed": 90,
        "failed": 8,
        "skipped": 2,
        "error": 0,
        "pass_rate": 90.0
      },
      "avg_response_time": 200,
      "last_execution_time": "2024-01-01 12:00:00"
    }
  ],
  "count": 10
}
```

#### 2.4.3 项目维度报告接口（新增）

**端点**: `GET /api/v1/api-automation/dashboard/project_reports/`

**请求参数**: 同上

**响应数据**:
```json
{
  "results": [
    {
      "project_id": 1,
      "project_name": "项目A",
      "owner_id": 1,
      "owner_name": "张三",
      "stats": {
        "total": 200,
        "passed": 180,
        "failed": 15,
        "skipped": 5,
        "error": 0,
        "pass_rate": 90.0
      },
      "avg_response_time": 220,
      "last_execution_time": "2024-01-01 12:00:00"
    }
  ],
  "count": 5
}
```

#### 2.4.4 重试接口（更新）

**端点**: `POST /api/v1/api-automation/dashboard/retry_failed/`

**请求参数**:
```json
{
  "scope": "all" | "selected",
  "test_result_ids": [1, 2, 3],  // scope=selected时必填
  "environment_id": 1,
  "execution_name": "重试执行"
}
```

**响应数据**:
```json
{
  "id": 123,
  "name": "重试执行",
  "status": "PENDING"
}
```

### 2.5 前端路由

| 路径 | 组件 | 说明 |
|------|------|------|
| /reports | ReportList | 测试报告列表页（原仪表盘） |
| /reports/:id | ReportDetail | 测试报告详情页 |

### 2.6 数据流

```
用户访问报告页面
    ↓
加载筛选条件选项（项目、集合、负责人、模块）
    ↓
应用默认筛选条件（全部）
    ↓
并发请求：
    - Dashboard 概览数据
    - 环境维度报告
    - 项目维度报告
    - 图表数据
    ↓
渲染统计卡片、图表、维度报告
    ↓
用户交互（点击筛选、点击图表）
    ↓
更新筛选状态
    ↓
重新请求测试结果列表
    ↓
更新列表展示
```

## 3. 技术实现要点

### 3.1 后端实现

1. **数据库迁移**
   - 为 ApiCollection 和 ApiTestCase 添加 owner 和 module 字段
   - 创建迁移文件并执行迁移

2. **ViewSet 更新**
   - DashboardViewSet.list() 添加筛选参数处理
   - 新增 project_reports() action
   - 更新 retry_failed() action 支持 scope 参数

3. **查询优化**
   - 使用 select_related 和 prefetch_related 优化查询
   - 添加数据库索引提升查询性能

### 3.2 前端实现

1. **组件结构**
   ```
   ReportList.vue (主页面)
   ├── ReportFilter.vue (筛选组件)
   ├── StatCards.vue (统计卡片组件)
   ├── ChartPanel.vue (图表组件)
   ├── DimensionTabs.vue (维度Tab组件)
   ├── ResultList.vue (测试结果列表)
   └── RetryDialog.vue (重试对话框)
   ```

2. **状态管理**
   - 使用 reactive 管理筛选条件状态
   - 使用 computed 计算派生数据
   - 使用 watch 监听筛选条件变化

3. **图表交互**
   - ECharts 点击事件处理
   - 图表高亮状态管理
   - 图表与列表联动

## 4. 开发步骤

1. ✅ 数据库模型变更（添加字段）
2. ✅ 执行数据库迁移
3. ✅ 更新后端 API（支持筛选）
4. ✅ 开发前端筛选组件
5. ✅ 开发前端统计卡片（支持点击）
6. ✅ 开发前端图表组件（支持点击）
7. ✅ 开发维度报告Tab
8. ✅ 开发测试结果列表
9. ✅ 实现重试功能
10. ✅ 集成测试

## 5. 验收标准

1. 所有筛选功能正常工作
2. 统计卡片点击能正确筛选数据
3. 图表点击能正确筛选数据
4. 环境维度和项目维度切换正常
5. 一键重试功能正常
6. 批量重试功能正常
7. 页面加载性能良好（< 2秒）
8. 所有交互无明显延迟
