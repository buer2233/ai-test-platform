# Tasks: 代码质量优化

## 1. 后端优化

### 1.1 Views 模块拆分
- [ ] 1.1.1 创建 `api_automation/views/` 目录
- [ ] 1.1.2 创建 `views/__init__.py` 导出所有视图
- [ ] 1.1.3 创建 `views/base.py` 基础视图类
- [ ] 1.1.4 使用 git mv 迁移项目相关代码到 `views/project.py`
- [ ] 1.1.5 使用 git mv 迁移集合相关代码到 `views/collection.py`
- [ ] 1.1.6 使用 git mv 迁移用例相关代码到 `views/test_case.py`
- [ ] 1.1.7 使用 git mv 迁移环境相关代码到 `views/environment.py`
- [ ] 1.1.8 使用 git mv 迁移执行相关代码到 `views/execution.py`
- [ ] 1.1.9 使用 git mv 迁移报告相关代码到 `views/report.py`
- [ ] 1.1.10 使用 git mv 迁移仪表盘相关代码到 `views/dashboard.py`
- [ ] 1.1.11 更新 `urls.py` 中的导入路径
- [ ] 1.1.12 删除原 `views.py` 文件
- [ ] 1.1.13 运行测试验证功能正确性

### 1.2 数据库索引优化
- [x] 1.2.1 分析当前查询模式，识别需要索引的字段
- [x] 1.2.2 为 ApiProject 添加索引（owner, is_deleted, created_time）
- [x] 1.2.3 为 ApiCollection 添加索引（project, is_deleted, name）
- [x] 1.2.4 为 ApiTestCase 添加索引（collection, is_deleted, created_time）
- [x] 1.2.5 为 ApiTestEnvironment 添加索引（project, is_deleted）
- [x] 1.2.6 为 ApiTestExecution 添加索引（environment, status, created_time）
- [x] 1.2.7 为 ApiTestResult 添加索引（execution, status）
- [x] 1.2.8 生成数据库迁移文件 `python manage.py makemigrations`
- [x] 1.2.9 应用数据库迁移 `python manage.py migrate`
- [x] 1.2.10 验证索引是否正确创建

### 1.3 查询优化
- [ ] 1.3.1 审查所有列表接口，识别 N+1 查询
- [ ] 1.3.2 添加 select_related 优化外键查询
- [ ] 1.3.3 添加 prefetch_related 优化多对多查询
- [ ] 1.3.4 测试查询性能对比

### 1.4 统一错误处理
- [x] 1.4.1 创建 `api_automation/exceptions.py` 自定义异常类
- [x] 1.4.2 创建 `api_automation/middleware/exception_handler.py`
- [x] 1.4.3 实现全局异常处理中间件
- [x] 1.4.4 更新 settings.py 注册中间件
- [x] 1.4.5 定义统一错误响应格式
- [x] 1.4.6 测试错误处理功能

### 1.5 抽取基类减少重复
- [ ] 1.5.1 创建 `serializers/base.py` 基础序列化器
- [ ] 1.5.2 抽取公共字段到基础序列化器
- [ ] 1.5.3 创建 `validators/base.py` 公共验证器
- [ ] 1.5.4 更新现有序列化器继承基类
- [ ] 1.5.5 测试验证功能正确性

## 2. 前端优化

### 2.1 拆分 RealtimeExecutionStatus.vue
- [ ] 2.1.1 分析组件结构，识别可拆分的子模块
- [ ] 2.1.2 创建 `components/RealtimeExecution/` 目录
- [ ] 2.1.3 创建 ExecutionHeader.vue 头部组件
- [ ] 2.1.4 创建 ExecutionProgress.vue 进度组件
- [ ] 2.1.5 创建 ExecutionLog.vue 日志组件
- [ ] 2.1.6 创建 ExecutionChart.vue 图表组件
- [ ] 2.1.7 创建 ExecutionShortcuts.vue 快捷键组件
- [ ] 2.1.8 创建 useExecutionLog.ts composable
- [ ] 2.1.9 创建 useExecutionChart.ts composable
- [ ] 2.1.10 创建 useKeyboardShortcuts.ts composable
- [ ] 2.1.11 更新主组件使用子组件
- [ ] 2.1.12 测试功能正确性

### 2.2 拆分其他超大组件
- [ ] 2.2.1 拆分 EnhancedReportViewer.vue（1803行）
- [ ] 2.2.2 拆分 VariableExtraction.vue（1199行）
- [ ] 2.2.3 拆分 TestCaseEditor.vue（1174行）
- [ ] 2.2.4 拆分 AssertionConfig.vue（1096行）

### 2.3 完善 TypeScript 类型
- [ ] 2.3.1 审计所有 `any` 类型使用
- [ ] 2.3.2 为 API 响应定义具体类型接口
- [ ] 2.3.3 更新 `types/` 目录下类型定义
- [x] 2.3.4 替换 http.ts 中的默认泛型
- [ ] 2.3.5 配置 TypeScript 严格模式
- [ ] 2.3.6 修复类型错误

### 2.4 统一错误处理
- [x] 2.4.1 创建 `utils/errorHandler.ts` 统一错误处理
- [x] 2.4.2 定义 ErrorResponse 接口
- [x] 2.4.3 实现 handleApiError 函数
- [x] 2.4.4 创建 ErrorBoundary.vue 错误边界组件
- [x] 2.4.5 更新 API 调用使用统一错误处理
- [x] 2.4.6 测试错误处理功能

### 2.5 抽取可复用逻辑
- [ ] 2.5.1 创建 composables/ 目录
- [ ] 2.5.2 抽取 useTableLogic.ts 表格逻辑
- [ ] 2.5.3 抽取 useFormValidation.ts 表单验证逻辑
- [ ] 2.5.4 抽取 useApiCall.ts API 调用逻辑
- [ ] 2.5.5 创建通用 BaseTable.vue 组件
- [ ] 2.5.6 创建通用 BaseForm.vue 组件

## 3. 性能优化

### 3.1 后端性能优化
- [ ] 3.1.1 优化仪表盘数据查询（使用聚合）
- [ ] 3.1.2 添加 Redis 缓存配置
- [ ] 3.1.3 为频繁访问的数据添加缓存
- [ ] 3.1.4 性能测试和对比

### 3.2 前端性能优化
- [ ] 3.2.1 审查所有计算属性，优化依赖
- [ ] 3.2.2 合并可合并的 watch
- [ ] 3.2.3 使用 v-once 优化静态内容
- [ ] 3.2.4 实现虚拟滚动（如需要）
- [ ] 3.2.5 性能测试和对比

## 4. 代码规范

### 4.1 后端代码规范
- [ ] 4.1.1 运行 black 格式化所有 Python 代码
- [ ] 4.1.2 运行 isort 整理导入
- [ ] 4.1.3 添加必要的 docstring
- [ ] 4.1.4 运行 pylint 检查代码质量

### 4.2 前端代码规范
- [ ] 4.2.1 配置 ESLint 规则
- [ ] 4.2.2 配置 Prettier 格式化
- [ ] 4.2.3 运行 eslint --fix 修复问题
- [ ] 4.2.4 添加必要的注释

## 5. 测试验证

### 5.1 后端测试
- [ ] 5.1.1 运行单元测试 `python manage.py test`
- [ ] 5.1.2 运行测试覆盖率 `coverage run --source='.' manage.py test`
- [ ] 5.1.3 验证覆盖率 >= 80%
- [ ] 5.1.4 手动测试 API 接口

### 5.2 前端测试
- [ ] 5.2.1 运行单元测试 `npm run test`
- [ ] 5.2.2 运行类型检查 `npm run type-check`
- [ ] 5.2.3 运行 lint 检查 `npm run lint`
- [ ] 5.2.4 手动测试所有页面功能

### 5.3 集成测试
- [ ] 5.3.1 测试项目创建流程
- [ ] 5.3.2 测试用例执行流程
- [ ] 5.3.3 测试报告查看流程
- [ ] 5.3.4 测试实时推送功能

## 6. 文档更新
- [ ] 6.1 更新 project_info.md
- [ ] 6.2 更新 CLAUDE.md
- [ ] 6.3 更新 README.md
- [ ] 6.4 更新 API 文档
