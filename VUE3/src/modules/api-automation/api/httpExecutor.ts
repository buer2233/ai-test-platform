/**
 * HTTP 执行器 API
 *
 * 提供直接执行 HTTP 请求的能力（类似 Postman），包括：
 * - 单次 / 批量执行请求
 * - 请求历史管理
 * - 请求导入 / 导出
 * - 执行记录的查询、统计、收藏、批量删除等
 */

import { apiClient } from './index'
import type { HttpResponse, HttpRequest } from '../types/http'
import type {
  HttpExecutionRecord,
  HttpExecutionRecordListResponse,
  HttpExecutionRecordStatistics,
  HttpExecutionRecordQuery,
  BatchDeleteRequest
} from '../types/http'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

/**
 * 将后端响应格式转换为前端统一的 HttpResponse 结构。
 * 兼容新格式（data 嵌套）和旧格式（扁平结构）。
 */
function transformResponse(apiResponse: any): HttpResponse {
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
  return {
    status: apiResponse.status_code || apiResponse.status || 200,
    headers: apiResponse.headers || {},
    body: apiResponse.body,
    response_time: apiResponse.response_time || 0,
    body_size: apiResponse.body_size || 0,
    error: apiResponse.error
  }
}

// ==================== HTTP 执行器 API ====================

export const httpExecutorApi = {
  /** 执行单个 HTTP 请求，返回标准化的响应对象 */
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

  /** 批量执行多个 HTTP 请求 */
  executeBatch: async (requests: HttpRequest[]): Promise<HttpResponse[]> => {
    const response = await apiClient.post(`${API_URL}/test-execute/batch/`, {
      requests
    })
    return response
  },

  /** 取消正在执行的请求 */
  cancel: async (executionId: string): Promise<void> => {
    await apiClient.post(`${API_URL}/test-execute/${executionId}/cancel/`)
  },

  /** 获取请求执行历史 */
  getHistory: async (params?: any) => {
    const response = await apiClient.get(`${API_URL}/test-execute/history/`, params)
    return response
  },

  /** 保存当前请求到历史记录 */
  saveToHistory: async (request: HttpRequest, name: string) => {
    const response = await apiClient.post(`${API_URL}/test-execute/history/`, {
      name,
      request
    })
    return response
  },

  /** 删除指定历史记录 */
  deleteHistory: async (id: number) => {
    await apiClient.delete(`${API_URL}/test-execute/history/${id}/`)
  },

  /** 导出请求配置为文件 */
  exportRequest: async (request: HttpRequest) => {
    const response = await apiClient.post(`${API_URL}/test-execute/export/`, request, {
      responseType: 'blob'
    })
    return response
  },

  /** 从文件导入请求配置 */
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

// ==================== HTTP 执行记录 API ====================

export const httpExecutionRecordApi = {
  /** 获取执行记录列表（支持分页、筛选、排序） */
  getList: async (query?: HttpExecutionRecordQuery): Promise<HttpExecutionRecordListResponse> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/`, query)
    return response
  },

  /** 获取单条执行记录的完整详情 */
  getDetail: async (id: number): Promise<HttpExecutionRecord> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/${id}/`)
    return response
  },

  /** 删除单条执行记录 */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_URL}/http-execution-records/${id}/`)
  },

  /** 获取执行记录的汇总统计信息 */
  getStatistics: async (): Promise<HttpExecutionRecordStatistics> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/statistics/`)
    return response
  },

  /** 批量删除执行记录（支持按 ID 或筛选条件） */
  batchDelete: async (request: BatchDeleteRequest): Promise<{ deleted_count: number }> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/batch_delete/`, request)
    return response
  },

  /** 切换执行记录的收藏状态 */
  toggleFavorite: async (id: number): Promise<{ message: string; is_favorite: boolean }> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/${id}/toggle_favorite/`)
    return response
  },

  /** 获取指定测试用例的执行历史记录 */
  getByTestCase: async (testCaseId: number, limit: number = 20): Promise<HttpExecutionRecord[]> => {
    const response = await apiClient.get(`${API_URL}/http-execution-records/by_test_case/`, {
      test_case: testCaseId,
      limit
    })
    return response
  },

  /** 根据历史记录重新执行请求 */
  reExecute: async (id: number): Promise<any> => {
    const response = await apiClient.post(`${API_URL}/http-execution-records/${id}/re_execute/`)
    return response
  }
}