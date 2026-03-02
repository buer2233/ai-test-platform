/**
 * 截图管理 API
 *
 * 提供 UI 自动化测试过程中截图的查询、删除和批量删除接口。
 */

import { http } from '../../../shared/utils/http'
import type { UiScreenshot } from '../types/screenshot'

/** UI自动化模块的 API 基础路径 */
const API_URL = '/v1/ui-automation'

export const uiScreenshotApi = {
  /** 获取截图列表（支持分页和筛选） */
  getScreenshots(params?: any) {
    return http.get<{ results: UiScreenshot[]; count: number }>(`${API_URL}/screenshots/`, params)
  },

  /** 根据 ID 获取单个截图详情 */
  getScreenshot(id: number) {
    return http.get<UiScreenshot>(`${API_URL}/screenshots/${id}/`)
  },

  /** 删除指定截图 */
  deleteScreenshot(id: number) {
    return http.delete(`${API_URL}/screenshots/${id}/`)
  },

  /** 批量删除截图，返回实际删除的数量 */
  bulkDelete(ids: number[]) {
    return http.post<{ deleted_count: number }>(`${API_URL}/screenshots/bulk-delete/`, { ids })
  }
}
