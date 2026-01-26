import { http } from '../../../shared/utils/http'
import type { ApiTestReport } from '../types/report'

export const reportApi = {
  // 获取报告列表
  getReports(params?: any) {
    return http.get<{ results: ApiTestReport[], count: number }>('/reports/', params)
  },

  // 获取单个报告
  getReport(id: number) {
    return http.get<ApiTestReport>(`/reports/${id}/`)
  },

  // 导出报告
  exportReport(id: number, format: 'pdf' | 'excel' = 'pdf') {
    return http.get(`/reports/${id}/export/?format=${format}`, {
      responseType: 'blob'
    })
  }
}