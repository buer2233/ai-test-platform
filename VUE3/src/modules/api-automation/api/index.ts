/**
 * API 模块统一入口
 *
 * 本文件导出共享的 HTTP 客户端实例，以及所有子模块的 API 接口。
 * 各子模块按功能职责划分，分别处理认证、项目、集合、测试用例等业务领域。
 */

import { http } from '../../../shared/utils/http'

/** 供子模块（如 httpExecutor）复用的 API 客户端实例 */
export const apiClient = http

// ==================== 导出所有 API 子模块 ====================

/** 认证相关 API（登录、注册、登出） */
export * from './auth'
/** 项目管理 API */
export * from './project'
/** 集合管理 API */
export * from './collection'
/** 测试用例 API */
export * from './testCase'
/** 测试环境 API */
export * from './environment'
/** 测试执行 API */
export * from './execution'
/** 测试结果 API */
export * from './testResult'
/** 测试报告 API */
export * from './report'
/** 断言配置 API */
export * from './assertion'
/** 数据提取配置 API */
export * from './extraction'
/** 数据驱动 API */
export * from './dataDriver'
/** 仪表盘 API */
export * from './dashboard'
/** 回收站 API */
export * from './recycleBin'
/** HTTP 执行器 API */
export * from './httpExecutor'