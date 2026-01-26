import { http } from '../../../shared/utils/http'
import type { UiTestExecution, UiTestExecutionCreate } from '../types/execution'

const API_URL = '/v1/ui-automation'

export const uiExecutionApi = {
  // 获取执行记录列表
  getExecutions(params?: any) {
    return http.get<{ results: UiTestExecution[], count: number }>(`${API_URL}/executions/`, params)
  },

  // 获取单个执行记录
  getExecution(id: number) {
    return http.get<UiTestExecution>(`${API_URL}/executions/${id}/`)
  },

  // 创建执行记录
  createExecution(data: UiTestExecutionCreate) {
    return http.post<UiTestExecution>(`${API_URL}/executions/`, data)
  },

  // 更新执行记录
  updateExecution(id: number, data: any) {
    return http.patch<UiTestExecution>(`${API_URL}/executions/${id}/`, data)
  },

  // 删除执行记录
  deleteExecution(id: number) {
    return http.delete(`${API_URL}/executions/${id}/`)
  },

  // 运行测试
  run(id: number) {
    return http.post<{
      message: string
      execution_id: number
      status: string
      success: boolean
    }>(`${API_URL}/executions/${id}/run/`)
  },

  // 取消执行
  cancel(id: number) {
    return http.post<{ message: string }>(`${API_URL}/executions/${id}/cancel/`)
  },

  // 获取测试报告
  getReport(id: number) {
    return http.get<{ html_report: string }>(`${API_URL}/executions/${id}/report/`)
  },

  // 获取执行截图
  getScreenshots(id: number) {
    return http.get<{ results: any[] }>(`${API_URL}/executions/${id}/screenshots/`)
  }
}
