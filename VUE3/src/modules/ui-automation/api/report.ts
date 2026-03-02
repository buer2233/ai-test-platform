/**
 * 测试报告 API
 *
 * 提供 UI 自动化测试报告的查询、汇总、文件读取、删除和导出等接口。
 * 包含截图 URL 构造函数（用于 <img> / <el-image> 标签的图片展示）。
 */

import { http } from '../../../shared/utils/http'
import type { UiTestReport, UiTestReportSummary } from '../types/report'

/** UI自动化模块的 API 基础路径 */
const API_URL = '/v1/ui-automation'

/**
 * 构造截图文件的 HTTP URL
 *
 * 由于 <img src> 和 <el-image> 无法携带 Authorization header，
 * 因此通过 URL 查询参数传递 token 进行认证。
 *
 * @param path - 截图在服务端的相对路径
 * @returns 完整的可访问截图 URL
 */
export function getScreenshotUrl(path: string): string {
  const token = localStorage.getItem('auth_token') || ''
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
  return `${baseUrl}${API_URL}/reports/screenshot/?path=${encodeURIComponent(path)}&token=${encodeURIComponent(token)}`
}

export const uiReportApi = {
  /** 获取报告列表（支持分页和筛选） */
  getReports(params?: any) {
    return http.get<{ results: UiTestReport[]; count: number }>(`${API_URL}/reports/`, params)
  },

  /** 根据 ID 获取单个报告详情 */
  getReport(id: number) {
    return http.get<UiTestReport>(`${API_URL}/reports/${id}/`)
  },

  /** 获取报告汇总信息（包含步骤数、截图数等统计指标） */
  getReportSummary(id: number) {
    return http.get<UiTestReportSummary>(`${API_URL}/reports/${id}/summary/`)
  },

  /** 根据文件路径读取 JSON 报告内容 */
  getReportFile(path: string) {
    return http.get<any>(`${API_URL}/reports/file/`, { path })
  },

  /** 删除指定报告 */
  deleteReport(id: number) {
    return http.delete(`${API_URL}/reports/${id}/`)
  },

  /** 导出报告为 PDF 格式，返回下载链接 */
  exportReport(id: number) {
    return http.post<{ download_url: string }>(`${API_URL}/reports/${id}/export/`)
  }
}
