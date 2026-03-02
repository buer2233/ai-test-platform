/**
 * 回收站 API
 *
 * 管理软删除数据的恢复和彻底删除。
 * 同时提供级联删除预览功能，用于在删除前展示关联数据的影响范围。
 */

import { http } from '../../../shared/utils/http'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

// ==================== 类型定义 ====================

/** 回收站中的单条数据项 */
export interface RecycleBinItem {
  id: number
  name: string
  type: string
  display_type: string
  created_time: string
  updated_time: string
  [key: string]: any
}

/** 回收站统计信息（按类型分组的计数） */
export interface RecycleBinStats {
  stats: Record<string, { display_name: string; count: number }>
  total_count: number
}

/** 回收站列表的分页响应 */
export interface RecycleBinListResponse {
  results: RecycleBinItem[]
  count: number
  page?: number
  page_size?: number
  total_pages?: number
}

/** 级联删除预览响应（展示删除目标及其关联数据） */
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

// ==================== 回收站 API ====================

export const recycleBinApi = {
  /** 获取回收站列表（支持按类型筛选和搜索） */
  getDeletedItems(params?: {
    type?: string
    search?: string
    page?: number
    page_size?: number
  }) {
    return http.get<RecycleBinListResponse>(`${API_URL}/recycle-bin/`, params)
  },

  /** 获取回收站各类型数据的统计计数 */
  getStats() {
    return http.get<RecycleBinStats>(`${API_URL}/recycle-bin/stats/`)
  },

  /** 恢复回收站中的单条数据 */
  restoreItem(type: string, id: number) {
    return http.post(`${API_URL}/recycle-bin/restore/${type}/${id}/`)
  },

  /** 批量恢复回收站中的数据 */
  batchRestore(type: string, ids: number[]) {
    return http.post(`${API_URL}/recycle-bin/batch_restore/`, { type, ids })
  },

  /** 彻底删除回收站中的单条数据（不可恢复） */
  permanentDeleteItem(type: string, id: number) {
    return http.post(`${API_URL}/recycle-bin/permanent-delete/${type}/${id}/`)
  },

  /** 批量彻底删除回收站中的数据（不可恢复） */
  batchPermanentDelete(type: string, ids: number[]) {
    return http.post(`${API_URL}/recycle-bin/batch_permanent_delete/`, { type, ids })
  }
}

// ==================== 级联删除预览 API ====================

export const cascadeDeleteApi = {
  /** 预览删除项目时的关联数据影响 */
  previewProjectDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/projects/${id}/preview_delete/`)
  },

  /** 预览删除集合时的关联数据影响 */
  previewCollectionDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/collections/${id}/preview_delete/`)
  },

  /** 预览删除测试用例时的关联数据影响 */
  previewTestCaseDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/test-cases/${id}/preview_delete/`)
  }
}
