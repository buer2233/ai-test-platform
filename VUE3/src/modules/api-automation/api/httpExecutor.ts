import { apiClient } from './index'
import type { HttpResponse, HttpRequest } from '../types/http'
import type {
  HttpExecutionRecord,
  HttpExecutionRecordListResponse,
  HttpExecutionRecordStatistics,
  HttpExecutionRecordQuery,
  BatchDeleteRequest
} from '../types/http'

const API_URL = '/v1/api-automation'

// 处理后端响应格式，转换为HttpResponse
const transformResponse = (apiResponse: any): HttpResponse => {
  // 后端返回格式: {code, message, data: {status_code, headers, body, response_time, body_size, error}}
  if (apiResponse && apiResponse.data) {
    const data = apiResponse.data
    return {
      status: data.status_code || 200,
      headers: data.headers || {},
      body: data.body,
      response_time: data.response_time || 0,
      body_size: data.body_size || 0,
      error: data.error
    }
  }
  // 如果直接返回的是数据（兼容旧格式）
  return {
    status: apiResponse.status_code || apiResponse.status || 200,
    headers: apiResponse.headers || {},
    body: apiResponse.body,
    response_time: apiResponse.response_time || 0,
    body_size: apiResponse.body_size || 0,
    error: apiResponse.error
  }
}

export const httpExecutorApi = {
  // 执行HTTP请求
  execute: async (request: HttpRequest): Promise<HttpResponse> => {
    const response = await apiClient.post(`${API_URL}/test-execute/`, {
      method: request.method,
      url: request.url,
      headers: request.headers?.filter(h => h.enabled !== false) || [],
      params: request.params?.filter(p => p.enabled !== false) || [],
      body: request.body,
      variables: request.variables?.filter(v => v.enabled) || [],
      settings: request.settings
    })
    // 构建完整的响应对象，包含请求信息
    const result = transformResponse(response)
    return {
      ...result,
      request: {
        method: request.method,
        url: (request.baseUrl || '') + request.url,
        headers: request.headers,
        params: request.params,
        body: request.body
      }
    } as HttpResponse
  },

  // 批量执行请求
  executeBatch: async (requests: HttpRequest[]): Promise<HttpResponse[]> => {
    const response = await apiClient.post(`${API_URL}/test-execute/batch/`, {
      requests
    })
    return response
  },

  // 取消请求
  cancel: async (executionId: string): Promise<void> => {
    await apiClient.post(`${API_URL}/test-execute/${executionId}/cancel/`)
  },

  // 获取请求历史
  getHistory: async (params?: any) => {
    const response = await apiClient.get(`${API_URL}/test-execute/history/`, params)
    return response
  },

  // 保存请求到历史
  saveToHistory: async (request: HttpRequest, name: string) => {
    const response = await apiClient.post(`${API_URL}/test-execute/history/`, {
      name,
      request
    })
    return response
  },

  // 删除历史记录
  deleteHistory: async (id: number) => {
    await apiClient.delete(`${API_URL}/test-execute/history/${id}/`)
  },

  // 导出请求
  exportRequest: async (request: HttpRequest) => {
    const response = await apiClient.post(`${API_URL}/test-execute/export/`, request, {
      responseType: 'blob'
    })
    return response
  },

  // 导入请求
  importRequest: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await apiClient.post(`${API_URL}/test-execute/import/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response
  }
}

// HTTP执行记录API
export const httpExecutionRecordApi = {
  // 获取执行记录列表
  getList: async (query?: HttpExecutionRecordQuery): Promise<HttpExecutionRecordListResponse> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/`, query)
    return response
  },

  // 获取单个执行记录详情
  getDetail: async (id: number): Promise<HttpExecutionRecord> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/${id}/`)
    return response
  },

  // 删除单个执行记录
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_URL}/http-execution-records/${id}/`)
  },

  // 获取统计信息
  getStatistics: async (): Promise<HttpExecutionRecordStatistics> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/statistics/`)
    return response
  },

  // 批量删除
  batchDelete: async (request: BatchDeleteRequest): Promise<{ deleted_count: number }> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/batch_delete/`, request)
    return response
  },

  // 切换收藏状态
  toggleFavorite: async (id: number): Promise<{ message: string; is_favorite: boolean }> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/${id}/toggle_favorite/`)
    return response
  },

  // 获取测试用例的执行历史
  getByTestCase: async (testCaseId: number, limit: number = 20): Promise<HttpExecutionRecord[]> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/by_test_case/`, {
      test_case: testCaseId,
      limit
    })
    return response
  },

  // 重新执行
  reExecute: async (id: number): Promise<any> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/${id}/re_execute/`)
    return response
  }
}