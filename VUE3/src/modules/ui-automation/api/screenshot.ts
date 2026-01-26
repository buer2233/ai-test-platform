import { http } from '../../../shared/utils/http'
import type { UiScreenshot } from '../types/screenshot'

const API_URL = '/v1/ui-automation'

export const uiScreenshotApi = {
  // 获取截图列表
  getScreenshots(params?: any) {
    return http.get<{ results: UiScreenshot[], count: number }>(`${API_URL}/screenshots/`, params)
  },

  // 获取单个截图
  getScreenshot(id: number) {
    return http.get<UiScreenshot>(`${API_URL}/screenshots/${id}/`)
  },

  // 删除截图
  deleteScreenshot(id: number) {
    return http.delete(`${API_URL}/screenshots/${id}/`)
  },

  // 批量删除截图
  bulkDelete(ids: number[]) {
    return http.post<{ deleted_count: number }>(`${API_URL}/screenshots/bulk-delete/`, { ids })
  }
}
