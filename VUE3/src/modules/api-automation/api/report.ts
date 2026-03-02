/**
 * 测试报告 API
 *
 * 管理测试执行生成的报告，支持查询和导出。
 * 报告包含执行概览、通过率统计、图表数据等。
 */

import { http } from '../../../shared/utils/http'
import type { ApiTestReport } from '../types/report'

export const reportApi = {
  /** 获取报告列表（支持分页和筛选） */
  getReports(params?: any) {
    return http.get<{ results: ApiTestReport[], count: number }>('/reports/', params)
  },

  /** 获取单个报告详情 */
  getReport(id: number) {
    return http.get<ApiTestReport>(`/reports/${id}/`)
  },

  /** 导出报告为文件（支持 PDF 和 Excel 格式） */
  exportReport(id: number, format: 'pdf' | 'excel' = 'pdf') {
    return http.get(`/reports/${id}/export/?format=${format}`, {
      responseType: 'blob'
    })
  }
}