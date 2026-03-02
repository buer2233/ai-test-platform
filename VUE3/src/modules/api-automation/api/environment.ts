/**
 * 测试环境 API
 *
 * 管理测试环境配置（Base URL、全局请求头、全局变量等）。
 * 支持设置默认环境、收藏、连接测试等操作。
 */

import { http } from '../../../shared/utils/http'
import type { ApiTestEnvironment } from '../types/environment'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const environmentApi = {
  /** 获取环境列表（支持分页和筛选） */
  getEnvironments(params?: any) {
    return http.get<{ results: ApiTestEnvironment[], count: number }>(`${API_URL}/environments/`, params)
  },

  /** 获取单个环境详情 */
  getEnvironment(id: number) {
    return http.get<ApiTestEnvironment>(`${API_URL}/environments/${id}/`)
  },

  /** 创建新的测试环境 */
  createEnvironment(data: any) {
    return http.post<ApiTestEnvironment>(`${API_URL}/environments/`, data)
  },

  /** 更新环境配置 */
  updateEnvironment(id: number, data: Partial<ApiTestEnvironment>) {
    return http.patch<ApiTestEnvironment>(`${API_URL}/environments/${id}/`, data)
  },

  /** 删除测试环境 */
  deleteEnvironment(id: number) {
    return http.delete(`${API_URL}/environments/${id}/`)
  },

  /** 设为当前项目的默认环境（同一项目只能有一个默认环境） */
  setDefault(id: number) {
    return http.post(`${API_URL}/environments/${id}/set_default/`)
  },

  /** 切换环境的收藏状态 */
  toggleFavorite(id: number) {
    return http.post<{ message: string; is_favorite: boolean }>(`${API_URL}/environments/${id}/toggle-favorite/`)
  },

  /** 向目标 Base URL 发送测试请求，验证环境连通性 */
  testConnection(id: number) {
    return http.get(`${API_URL}/environments/${id}/test-connection/`)
  }
}