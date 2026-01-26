import { http } from '../../../shared/utils/http'

// 创建专用的API客户端
export const apiClient = http

// 导出所有API模块
export * from './project'
export * from './testCase'
export * from './execution'
export * from './report'
export * from './screenshot'
