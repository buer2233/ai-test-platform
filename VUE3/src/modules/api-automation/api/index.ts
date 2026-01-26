import { http } from '../../../shared/utils/http'

// 创建专用的API客户端
export const apiClient = http

// 导出所有API模块
export * from './auth'
export * from './project'
export * from './collection'
export * from './testCase'
export * from './environment'
export * from './execution'
export * from './testResult'
export * from './report'
export * from './assertion'
export * from './extraction'
export * from './dataDriver'
export * from './dashboard'
export * from './recycleBin'
export * from './httpExecutor'