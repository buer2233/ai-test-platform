/**
 * HTTP 请求工具模块
 *
 * 基于 axios 封装，提供：
 * 1. 统一的请求基础配置（baseURL、超时、Content-Type）
 * 2. 请求拦截器：自动附加认证令牌
 * 3. 响应拦截器：自动解包响应数据、统一错误处理与用户提示
 * 4. 简化的 API 方法（get / post / patch / put / delete）
 */
import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

/* ========== 类型定义 ========== */

/** 后端标准错误响应格式 */
export interface ErrorResponse {
  code: number
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

/* ========== Axios 实例创建 ========== */

const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/* ========== 请求拦截器 ========== */

/**
 * 在每个请求发送前，从 localStorage 读取认证令牌并附加到请求头。
 * 令牌格式为 Django REST Framework 的 Token 认证。
 */
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/* ========== 响应拦截器 ========== */

/**
 * 响应处理逻辑：
 * - 成功时：直接返回 response.data（去掉 axios 外层包装）
 * - 失败时：根据 HTTP 状态码提取错误信息，通过 ElMessage 提示用户
 *   - 401 未授权：自动清除令牌并跳转到登录页
 *   - 其他状态码：优先使用后端标准格式的 message 字段
 *   - 网络异常或配置错误：显示对应的友好提示
 */
http.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    let message = '请求失败'

    if (error.response) {
      const data = error.response.data as ErrorResponse | undefined

      // 优先使用后端标准错误格式
      if (data?.message) {
        message = data.message
      } else {
        // 兼容旧版接口的错误格式
        switch (error.response.status) {
          case 400:
            message = (data as any)?.detail || error.response.data?.message || '请求参数错误'
            break
          case 401:
            message = '未授权，请重新登录'
            localStorage.removeItem('auth_token')
            window.location.href = '/login'
            break
          case 403:
            message = data?.message || '拒绝访问'
            break
          case 404:
            message = data?.message || '请求地址不存在'
            break
          case 500:
            message = data?.message || '服务器内部错误'
            break
          default:
            message = data?.message || `系统错误: ${error.response.status}`
        }
      }
    } else if (error.request) {
      // 请求已发出但未收到响应（网络问题）
      message = '网络连接异常，请检查网络'
    } else {
      // 请求尚未发出（配置错误）
      message = error.message || '请求配置错误'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/* ========== 对外暴露的请求方法 ========== */

/**
 * 封装 axios 方法，简化调用方式：
 * - get 的第二个参数直接传 params 对象（无需包装在 config 内）
 * - 所有方法均返回 Promise<T>（T 为实际业务数据类型）
 */
const extendedHttp = {
  get<T = any>(url: string, params?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return http.get(url, { ...(config || {}), params })
  },

  post<T = any>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return http.post(url, data, config)
  },

  patch<T = any>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return http.patch(url, data, config)
  },

  put<T = any>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return http.put(url, data, config)
  },

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return http.delete(url, config)
  }
}

export { extendedHttp as http }
export type { AxiosRequestConfig, AxiosResponse }
