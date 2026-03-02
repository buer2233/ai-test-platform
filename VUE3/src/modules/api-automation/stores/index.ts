/**
 * Store 模块统一入口
 *
 * 导出所有 Pinia Store，按业务领域分别管理：
 * - 认证（auth）：登录状态、用户信息、Token 管理
 * - 项目（project）：项目列表和详情
 * - 集合（collection）：集合列表和详情
 * - 测试用例（testCase）：用例的增删改查和统计
 * - 测试环境（environment）：环境配置管理
 * - 测试执行（execution）：执行任务的状态和进度
 * - 测试报告（report）：报告的查看和导出
 * - 数据驱动（dataDriver）：参数化测试数据源配置
 */

export { useAuthStore } from './auth'
export { useProjectStore } from './project'
export { useCollectionStore } from './collection'
export { useTestCaseStore } from './testCase'
export { useEnvironmentStore } from './environment'
export { useExecutionStore } from './execution'
export { useReportStore } from './report'
export { useDataDriverStore } from './dataDriver'