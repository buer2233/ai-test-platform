import { http } from '../../../shared/utils/http'
import type { ApiCollection, ApiCollectionCreate, ApiCollectionDetail } from '../types/collection'
import type { CascadePreviewResponse } from './recycleBin'

const API_URL = '/v1/api-automation'

export const collectionApi = {
  // 获取集合列表
  getCollections(params?: any) {
    return http.get<{ results: ApiCollection[], count: number }>(`${API_URL}/collections/`, params)
  },

  // 获取单个集合
  getCollection(id: number) {
    return http.get<ApiCollectionDetail>(`${API_URL}/collections/${id}/`)
  },

  // 创建集合
  createCollection(data: ApiCollectionCreate) {
    return http.post<ApiCollection>(`${API_URL}/collections/`, data)
  },

  // 更新集合
  updateCollection(id: number, data: Partial<ApiCollectionCreate>) {
    return http.patch<ApiCollection>(`${API_URL}/collections/${id}/`, data)
  },

  // 删除集合
  deleteCollection(id: number) {
    return http.delete(`${API_URL}/collections/${id}/`)
  },

  // 预览删除影响
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/collections/${id}/preview_delete/`)
  },

  // 获取集合的测试用例
  getCollectionTestCases(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/collections/${id}/test_cases/`, params)
  },

  // ========== 批量操作相关 ==========

  // 批量添加测试用例到集合
  batchAddTestCases(collectionId: number, testCaseIds: number[]) {
    return http.post(`${API_URL}/collections/${collectionId}/batch_add_test_cases/`, {
      test_case_ids: testCaseIds
    })
  },

  // 批量从集合中移除测试用例
  batchRemoveTestCases(collectionId: number, testCaseIds: number[]) {
    return http.post(`${API_URL}/collections/${collectionId}/batch_remove_test_cases/`, {
      test_case_ids: testCaseIds
    })
  },

  // 按集合执行测试
  execute(collectionId: number, environmentId: number, executionName?: string) {
    return http.post(`${API_URL}/collections/${collectionId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}