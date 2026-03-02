/**
 * UI自动化模块类型定义统一导出
 *
 * 集中导出所有类型定义，方便其他模块按需引入。
 * 各类型文件按业务领域划分：
 * - project     项目相关类型
 * - testCase    测试用例相关类型
 * - execution   执行记录相关类型
 * - report      测试报告相关类型（含 browser_use JSON 报告结构）
 * - screenshot  截图相关类型
 */

export * from './project'
export * from './testCase'
export * from './execution'
export * from './report'
export * from './screenshot'
