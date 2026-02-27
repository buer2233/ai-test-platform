import { http } from '../../../shared/utils/http'
import type { UiTestReport, UiTestReportSummary } from '../types/report'

const API_URL = '/v1/ui-automation'

/**
 * 构造截图文件的 HTTP URL
 * 因为 <img src> 和 <el-image> 无法携带 Authorization header，
 * 所以通过 token 查询参数认证。
 */
export function getScreenshotUrl(path: string): string {
  const token = localStorage.getItem('auth_token') || ''
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${baseUrl}${API_URL}/reports/screenshot/?path=${encodeURIComponent(path)}&token=${encodeURIComponent(token)}`
}

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

  // 获取 JSON 报告文件内容
  getReportFile(path: string) {
    return http.get<any>(`${API_URL}/reports/file/`, { path })
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
