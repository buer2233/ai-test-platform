/**
 * 执行记录 API
 *
 * 提供 UI 自动化测试执行记录的增删改查、运行/取消、报告和截图等接口。
 */

import { http } from '../../../shared/utils/http'
import type { UiTestExecution, UiTestExecutionCreate } from '../types/execution'

/** UI自动化模块的 API 基础路径 */
const API_URL = '/v1/ui-automation'

export const uiExecutionApi = {
  /** 获取执行记录列表（支持分页和筛选） */
  getExecutions(params?: any) {
    return http.get<{ results: UiTestExecution[]; count: number }>(`${API_URL}/executions/`, params)
  },

  /** 根据 ID 获取单个执行记录详情 */
  getExecution(id: number) {
    return http.get<UiTestExecution>(`${API_URL}/executions/${id}/`)
  },

  /** 创建新的执行记录 */
  createExecution(data: UiTestExecutionCreate) {
    return http.post<UiTestExecution>(`${API_URL}/executions/`, data)
  },

  /** 局部更新执行记录（PATCH） */
  updateExecution(id: number, data: any) {
    return http.patch<UiTestExecution>(`${API_URL}/executions/${id}/`, data)
  },

  /** 删除指定执行记录 */
  deleteExecution(id: number) {
    return http.delete(`${API_URL}/executions/${id}/`)
  },

  /** 启动测试执行（后端会触发 browser_use 运行） */
  run(id: number) {
    return http.post<{
      message: string
      execution_id: number
      status: string
      success: boolean
    }>(`${API_URL}/executions/${id}/run/`)
  },

  /** 取消正在运行的测试执行 */
  cancel(id: number) {
    return http.post<{ message: string }>(`${API_URL}/executions/${id}/cancel/`)
  },

  /** 获取执行关联的 HTML 测试报告 */
  getReport(id: number) {
    return http.get<{ html_report: string }>(`${API_URL}/executions/${id}/report/`)
  },

  /** 获取执行过程中产生的截图列表 */
  getScreenshots(id: number) {
    return http.get<{ results: any[] }>(`${API_URL}/executions/${id}/screenshots/`)
  }
}
