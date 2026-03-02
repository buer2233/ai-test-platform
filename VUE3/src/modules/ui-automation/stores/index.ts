/**
 * UI自动化模块 Pinia 状态管理统一导出
 *
 * 各 Store 职责：
 * - project   项目列表与当前项目状态
 * - testCase  测试用例列表与当前用例状态
 * - execution 执行记录列表、运行状态和 WebSocket 进度
 * - report    测试报告列表与统计指标
 */

export * from './project'
export * from './testCase'
export * from './execution'
export * from './report'
