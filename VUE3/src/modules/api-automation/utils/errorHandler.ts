/**
 * API Automation - Error Handler
 * 统一错误处理工具
 */

import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

/**
 * 标准错误响应接口
 */
export interface ErrorResponse {
  code: number
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

/**
 * API 错误类
 */
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

/**
 * 处理 API 错误
 * @param error Axios 错误对象
 * @param showMessage 是否显示错误消息（默认 true）
 * @returns APIError 实例
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

  // 显示错误消息
  if (showMessage) {
    showErrorNotification(apiError)
  }

  // 记录错误到控制台
  console.error('[API Error]', apiError)

  return apiError
}

/**
 * 判断是否为 Axios 错误
 */
function isAxiosError(error: unknown): error is AxiosError<ErrorResponse> {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    'config' in error
  )
}

/**
 * 显示错误通知
 */
function showErrorNotification(error: APIError): void {
  const title = getErrorTitle(error.code)
  const message = error.message

  // 根据错误类型选择不同的显示方式
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

/**
 * 根据错误码获取错误标题
 */
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

/**
 * 判断错误是否为网络错误
 */
export function isNetworkError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return !error.response && !!error.message
  }
  return false
}

/**
 * 判断错误是否为超时错误
 */
export function isTimeoutError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return error.code === 'ECONNABORTED'
  }
  return false
}

/**
 * 判断错误是否为取消请求
 */
export function isCancelError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return error.code === 'ERR_CANCELED'
  }
  return false
}
