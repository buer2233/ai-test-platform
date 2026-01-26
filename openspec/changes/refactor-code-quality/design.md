# Design: 代码质量优化

## Context

项目已完成核心功能开发，但代码存在质量债务需要处理。主要问题包括：
- 后端 views.py 文件过大（1777行）
- 前端5个组件超过300行限制
- 缺少数据库索引导致性能问题
- TypeScript 类型定义不完善
- 错误处理机制不统一

## Goals / Non-Goals

### Goals
- 拆分大文件为符合单一职责原则的小文件
- 优化数据库查询性能
- 完善类型定义和错误处理
- 统一代码规范

### Non-Goals
- 不添加新功能
- 不改变现有 API 接口
- 不改变现有业务逻辑
- 不进行大规模架构重构

## Decisions

### 决策1: 后端 views.py 拆分策略

**选择**：按业务领域拆分为独立的视图模块

**原因**：
- 按业务域拆分更符合团队认知模型
- 便于多人并行开发
- 降低文件间的耦合度

**方案**：
```
api_automation/
├── views/
│   ├── __init__.py          # 导出所有视图
│   ├── base.py              # 基础视图类
│   ├── project.py           # 项目相关视图
│   ├── collection.py        # 集合相关视图
│   ├── test_case.py         # 测试用例视图
│   ├── environment.py       # 环境视图
│   ├── execution.py         # 执行视图
│   ├── report.py            # 报告视图
│   └── dashboard.py         # 仪表盘视图
```

### 决策2: 前端大组件拆分策略

**选择**：组合式组件 + Composables

**原因**：
- Vue 3 Composition API 更适合逻辑复用
- Composables 可以跨组件复用逻辑
- 组件拆分后便于测试和维护

**方案**：
- 使用 `<script setup>` 语法
- 抽取可复用逻辑到 composables
- 拆分为多个子组件组合使用

### 决策3: 数据库索引策略

**选择**：为外键和常用查询字段添加复合索引

**索引设计**：
```python
class Meta:
    indexes = [
        # 项目相关
        models.Index(fields=['owner', 'is_deleted']),
        models.Index(fields=['created_time']),

        # 集合相关
        models.Index(fields=['project', 'is_deleted']),
        models.Index(fields=['project', 'name']),

        # 用例相关
        models.Index(fields=['collection', 'is_deleted']),
        models.Index(fields=['collection', 'created_time']),

        # 执行相关
        models.Index(fields=['environment', 'created_time']),
        models.Index(fields=['status', 'created_time']),
    ]
```

### 决策4: TypeScript 类型策略

**选择**：定义严格的类型接口，移除所有 `any`

**方案**：
- 为 API 响应定义具体类型
- 使用泛型增强类型复用
- 启用 TypeScript 严格模式

### 决策5: 错误处理策略

**后端**：实现统一异常处理中间件

```python
# middleware/exception_handler.py
class GlobalExceptionHandler:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        # 统一异常处理逻辑
        pass
```

**前端**：实现错误边界和全局错误处理器

```typescript
// utils/errorHandler.ts
export interface ErrorResponse {
    code: number;
    message: string;
    details?: unknown;
}

export function handleApiError(error: AxiosError<ErrorResponse>): void
```

## Risks / Trade-offs

### 风险1: 文件拆分可能导致 Git 历史丢失

**缓解措施**：
- 使用 `git mv` 而非删除后新建
- 在提交信息中注明文件来源

### 风险2: 拆分过程中可能引入 Bug

**缓解措施**：
- 保持 API 接口不变
- 完整的测试覆盖
- 逐步迁移而非一次性重写

### 风险3: 索引可能影响写入性能

**缓解措施**：
- 只为频繁查询的字段添加索引
- 使用复合索引减少索引数量
- 监控数据库性能

## Migration Plan

### 阶段1: 后端优化（第1-2周）
1. 创建 views/ 目录结构
2. 使用 git mv 迁移代码到新文件
3. 更新导入和路由
4. 添加数据库索引
5. 创建基类序列化器
6. 测试验证

### 阶段2: 前端优化（第2-3周）
1. 拆分 RealtimeExecutionStatus.vue
2. 拆分其他超大组件
3. 完善 TypeScript 类型
4. 统一错误处理
5. 创建可复用 composables
6. 测试验证

### 阶段3: 性能优化（第3-4周）
1. 优化后端查询（select_related, prefetch_related）
2. 优化前端计算属性和 watch
3. 性能测试和对比

### 阶段4: 代码规范（持续）
1. 配置 ESLint + Prettier
2. 添加必要的注释和文档
3. 代码审查

### 回滚计划
- 每个阶段完成后创建 Git 标签
- 如有问题可回滚到上一个稳定版本
- 保持向后兼容的 API

## Open Questions

1. **问**: 是否需要立即优化所有5个大组件？
   **答**: 优先处理最大的 RealtimeExecutionStatus.vue，其他可分阶段进行

2. **问**: 索引数量是否会影响数据库性能？
   **答**: 会持续监控，根据实际查询模式调整

3. **问**: TypeScript 严格模式是否会影响现有代码？
   **答**: 会逐步迁移，先修复类型再启用严格模式
