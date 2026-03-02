/**
 * UI自动化模块 API 层统一导出
 *
 * 集中导出所有 API 模块，方便上层组件按需引入。
 * 底层 HTTP 客户端复用项目共享的 http 工具（自动携带认证信息）。
 */

import { http } from '../../../shared/utils/http'

/** 模块专用的 API 客户端（复用共享 http 实例） */
export const apiClient = http

/* ---------- 按业务模块导出 ---------- */
export * from './project'
export * from './testCase'
export * from './execution'
export * from './report'
export * from './screenshot'
