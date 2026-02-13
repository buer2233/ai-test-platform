import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

/**
 * 标准错误响应接口
 */
export interface ErrorResponse {
  code: number
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

// 创建axios实例
const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Token ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // 直接返回响应数据
    return response.data
  },
  (error) => {
    // 处理错误
    let message = '请求失败'

    if (error.response) {
      const data = error.response.data as ErrorResponse | undefined

      // 使用后端返回的标准错误格式
      if (data?.message) {
        message = data.message
      } else {
        // 兼容旧格式
        switch (error.response.status) {
          case 400:
            message = (data as any)?.detail || error.response.data?.message || '请求参数错误'
            break
          case 401:
            message = '未授权，请重新登录'
            // 清除token并跳转到登录页
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
      // 请求已发送但没有收到响应
      message = '网络连接异常，请检查网络'
    } else {
      // 请求配置错误
      message = error.message || '请求配置错误'
    }

    // 显示错误提示
    ElMessage.error(message)

    // 返回错误对象
    return Promise.reject(error)
  }
)

// 扩展axios方法，使其支持params参数
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
