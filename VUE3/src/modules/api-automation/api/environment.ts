import { http } from '../../../shared/utils/http'
import type { ApiTestEnvironment } from '../types/environment'

const API_URL = '/v1/api-automation'

export const environmentApi = {
  // 获取环境列表
  getEnvironments(params?: any) {
    return http.get<{ results: ApiTestEnvironment[], count: number }>(`${API_URL}/environments/`, params)
  },

  // 获取单个环境
  getEnvironment(id: number) {
    return http.get<ApiTestEnvironment>(`${API_URL}/environments/${id}/`)
  },

  // 创建环境
  createEnvironment(data: any) {
    return http.post<ApiTestEnvironment>(`${API_URL}/environments/`, data)
  },

  // 更新环境
  updateEnvironment(id: number, data: Partial<ApiTestEnvironment>) {
    return http.patch<ApiTestEnvironment>(`${API_URL}/environments/${id}/`, data)
  },

  // 删除环境
  deleteEnvironment(id: number) {
    return http.delete(`${API_URL}/environments/${id}/`)
  },

  // 设置为默认环境
  setDefault(id: number) {
    return http.post(`${API_URL}/environments/${id}/set_default/`)
  },

  // 切换收藏状态
  toggleFavorite(id: number) {
    return http.post<{ message: string; is_favorite: boolean }>(`${API_URL}/environments/${id}/toggle-favorite/`)
  },

  // 测试环境连接
  testConnection(id: number) {
    return http.get(`${API_URL}/environments/${id}/test-connection/`)
  }
}