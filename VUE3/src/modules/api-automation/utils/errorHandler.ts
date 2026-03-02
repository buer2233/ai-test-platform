/**
 * 统一错误处理工具
 *
 * 提供 API 错误的标准化处理流程：
 * 1. 将各种错误类型（Axios、原生 Error、未知错误）统一转换为 APIError
 * 2. 根据错误码选择合适的 UI 提示方式（通知 / 消息）
 * 3. 提供网络错误、超时、请求取消等场景的判断方法
 */

import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

// ==================== 错误类型定义 ====================

/** 后端标准错误响应结构 */
export interface ErrorResponse {
  code: number
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

/** 自定义 API 错误类，封装后端返回的错误信息 */
export class APIError extends Error {
  code: number
  details?: Record<string, unknown>

  constructor(error: ErrorResponse) {
    super(error.message)
    this.name = 'APIError'
    this.code = error.code
    this.details = error.details
  }
}

// ==================== 核心错误处理 ====================

/**
 * 处理 API 错误：将各种错误统一转换为 APIError 并可选地显示 UI 提示。
 * @param error - 任意类型的错误对象
 * @param showMessage - 是否显示 UI 错误提示（默认 true）
 * @returns 标准化的 APIError 实例
 */
export function handleApiError(error: unknown, showMessage = true): APIError {
  let apiError: APIError

  if (isAxiosError(error)) {
    const response = error.response?.data as ErrorResponse | undefined

    apiError = new APIError({
      code: response?.code || error.response?.status || 500,
      message: response?.message || '请求失败，请稍后重试',
      details: response?.details,
      timestamp: response?.timestamp || new Date().toISOString()
    })
  } else if (error instanceof Error) {
    apiError = new APIError({
      code: 500,
      message: error.message || '未知错误',
      timestamp: new Date().toISOString()
    })
  } else {
    apiError = new APIError({
      code: 500,
      message: '未知错误',
      timestamp: new Date().toISOString()
    })
  }

  if (showMessage) {
    showErrorNotification(apiError)
  }

  console.error('[API Error]', apiError)

  return apiError
}

// ==================== 内部辅助函数 ====================

/** 判断是否为 Axios 错误（通过检查对象特征属性） */
function isAxiosError(error: unknown): error is AxiosError<ErrorResponse> {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    'config' in error
  )
}

/**
 * 根据错误码选择合适的 UI 提示方式：
 * - 5xx 服务端错误：使用 Notification 强提示
 * - 401 未授权：提示登录
 * - 403 权限不足 / 404 资源不存在：使用 Message 轻提示
 * - 其他错误：使用 Message 通用提示
 */
function showErrorNotification(error: APIError): void {
  const title = getErrorTitle(error.code)
  const message = error.message

  if (error.code >= 500) {
    ElNotification({
      title,
      message,
      type: 'error',
      duration: 5000
    })
  } else if (error.code === 401) {
    ElNotification({
      title: '未授权',
      message: '请先登录',
      type: 'warning',
      duration: 3000
    })
  } else if (error.code === 403) {
    ElMessage({
      message: '没有权限执行此操作',
      type: 'warning',
      duration: 3000
    })
  } else if (error.code === 404) {
    ElMessage({
      message: '请求的资源不存在',
      type: 'warning',
      duration: 3000
    })
  } else {
    ElMessage({
      message,
      type: 'error',
      duration: 3000
    })
  }
}

/** 根据 HTTP 状态码返回对应的中文错误标题 */
function getErrorTitle(code: number): string {
  const titles: Record<number, string> = {
    400: '请求错误',
    401: '未授权',
    403: '权限不足',
    404: '资源不存在',
    500: '服务器错误',
    502: '网关错误',
    503: '服务不可用'
  }
  return titles[code] || '错误'
}

// ==================== 错误类型判断工具 ====================

/** 判断是否为网络连接错误（如断网、DNS 解析失败等） */
export function isNetworkError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return !error.response && !!error.message
  }
  return false
}

/** 判断是否为请求超时错误 */
export function isTimeoutError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return error.code === 'ECONNABORTED'
  }
  return false
}

/** 判断是否为手动取消的请求 */
export function isCancelError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return error.code === 'ERR_CANCELED'
  }
  return false
}
