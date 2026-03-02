/**
 * 集合管理 API
 *
 * 集合是测试用例的逻辑分组，隶属于某个项目。
 * 支持集合的增删改查、级联删除预览、批量操作测试用例、以及按集合执行测试。
 */

import { http } from '../../../shared/utils/http'
import type { ApiCollection, ApiCollectionCreate, ApiCollectionDetail } from '../types/collection'
import type { CascadePreviewResponse } from './recycleBin'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const collectionApi = {
  /** 获取集合列表（支持分页和筛选） */
  getCollections(params?: any) {
    return http.get<{ results: ApiCollection[], count: number }>(`${API_URL}/collections/`, params)
  },

  /** 获取单个集合详情（包含关联的测试用例） */
  getCollection(id: number) {
    return http.get<ApiCollectionDetail>(`${API_URL}/collections/${id}/`)
  },

  /** 创建新集合 */
  createCollection(data: ApiCollectionCreate) {
    return http.post<ApiCollection>(`${API_URL}/collections/`, data)
  },

  /** 更新集合信息 */
  updateCollection(id: number, data: Partial<ApiCollectionCreate>) {
    return http.patch<ApiCollection>(`${API_URL}/collections/${id}/`, data)
  },

  /** 软删除集合（可从回收站恢复） */
  deleteCollection(id: number) {
    return http.delete(`${API_URL}/collections/${id}/`)
  },

  /** 预览删除影响范围，展示级联删除的关联数据 */
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/collections/${id}/preview_delete/`)
  },

  /** 获取集合下的测试用例列表 */
  getCollectionTestCases(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/collections/${id}/test_cases/`, params)
  },

  // ==================== 批量操作 ====================

  /** 批量添加测试用例到集合 */
  batchAddTestCases(collectionId: number, testCaseIds: number[]) {
    return http.post(`${API_URL}/collections/${collectionId}/batch_add_test_cases/`, {
      test_case_ids: testCaseIds
    })
  },

  /** 批量从集合中移除测试用例 */
  batchRemoveTestCases(collectionId: number, testCaseIds: number[]) {
    return http.post(`${API_URL}/collections/${collectionId}/batch_remove_test_cases/`, {
      test_case_ids: testCaseIds
    })
  },

  /** 按集合执行测试（需指定运行环境） */
  execute(collectionId: number, environmentId: number, executionName?: string) {
    return http.post(`${API_URL}/collections/${collectionId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}