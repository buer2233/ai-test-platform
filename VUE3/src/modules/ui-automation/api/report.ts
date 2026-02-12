import { http } from '../../../shared/utils/http'
import type { UiTestReport, UiTestReportSummary } from '../types/report'

const API_URL = '/v1/ui-automation'

export const uiReportApi = {
  // 获取报告列表
  getReports(params?: any) {
    return http.get<{ results: UiTestReport[], count: number }>(`${API_URL}/reports/`, params)
  },

  // 获取单个报告
  getReport(id: number) {
    return http.get<UiTestReport>(`${API_URL}/reports/${id}/`)
  },

  // 获取报告汇总（含报告文件统计）
  getReportSummary(id: number) {
    return http.get<UiTestReportSummary>(`${API_URL}/reports/${id}/summary/`)
  },

  // 删除报告
  deleteReport(id: number) {
    return http.delete(`${API_URL}/reports/${id}/`)
  },

  // 导出报告为PDF
  exportReport(id: number) {
    return http.post<{ download_url: string }>(`${API_URL}/reports/${id}/export/`)
  }
}
