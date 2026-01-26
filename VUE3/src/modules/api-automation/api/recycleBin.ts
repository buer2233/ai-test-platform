import { http } from '../../../shared/utils/http'

const API_URL = '/v1/api-automation'

export interface RecycleBinItem {
  id: number
  name: string
  type: string
  display_type: string
  created_time: string
  updated_time: string
  [key: string]: any
}

export interface RecycleBinStats {
  stats: Record<string, { display_name: string; count: number }>
  total_count: number
}

export interface RecycleBinListResponse {
  results: RecycleBinItem[]
  count: number
  page?: number
  page_size?: number
  total_pages?: number
}

export interface CascadePreviewResponse {
  target: {
    id: number
    name: string
    type: string
    display_type: string
  }
  cascade_count: Record<string, number>
  cascade_details: Array<{
    type: string
    display_type: string
    count: number
    names?: string[]
  }>
}

export const recycleBinApi = {
  // 获取回收站列表
  getDeletedItems(params?: {
    type?: string
    search?: string
    page?: number
    page_size?: number
  }) {
    return http.get<RecycleBinListResponse>(`${API_URL}/recycle-bin/`, params)
  },

  // 获取回收站统计
  getStats() {
    return http.get<RecycleBinStats>(`${API_URL}/recycle-bin/stats/`)
  },

  // 恢复单个数据
  restoreItem(type: string, id: number) {
    return http.post(`${API_URL}/recycle-bin/restore/${type}/${id}/`)
  },

  // 批量恢复
  batchRestore(type: string, ids: number[]) {
    return http.post(`${API_URL}/recycle-bin/batch_restore/`, { type, ids })
  },

  // 彻底删除单个数据
  permanentDeleteItem(type: string, id: number) {
    return http.post(`${API_URL}/recycle-bin/permanent-delete/${type}/${id}/`)
  },

  // 批量彻底删除
  batchPermanentDelete(type: string, ids: number[]) {
    return http.post(`${API_URL}/recycle-bin/batch_permanent_delete/`, { type, ids })
  }
}

export const cascadeDeleteApi = {
  // 预览项目删除
  previewProjectDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/projects/${id}/preview_delete/`)
  },

  // 预览集合删除
  previewCollectionDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/collections/${id}/preview_delete/`)
  },

  // 预览测试用例删除
  previewTestCaseDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/test-cases/${id}/preview_delete/`)
  }
}
