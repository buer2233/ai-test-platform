import { http } from '../../../shared/utils/http'
import type { UiTestCase, UiTestCaseCreate, UiTestCaseUpdate } from '../types/testCase'

const API_URL = '/v1/ui-automation'

export const uiTestCaseApi = {
  // 获取测试用例列表
  getTestCases(params?: any) {
    return http.get<{ results: UiTestCase[], count: number }>(`${API_URL}/test-cases/`, params)
  },

  // 获取单个测试用例
  getTestCase(id: number) {
    return http.get<UiTestCase>(`${API_URL}/test-cases/${id}/`)
  },

  // 创建测试用例
  createTestCase(data: UiTestCaseCreate) {
    return http.post<UiTestCase>(`${API_URL}/test-cases/`, data)
  },

  // 更新测试用例
  updateTestCase(id: number, data: UiTestCaseUpdate) {
    return http.patch<UiTestCase>(`${API_URL}/test-cases/${id}/`, data)
  },

  // 删除测试用例
  deleteTestCase(id: number) {
    return http.delete(`${API_URL}/test-cases/${id}/`)
  },

  // 复制测试用例
  copyTestCase(id: number) {
    return http.post<UiTestCase>(`${API_URL}/test-cases/${id}/copy/`)
  },

  // 获取用例的执行历史
  getTestCaseExecutions(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/test-cases/${id}/executions/`, params)
  },

  // 直接运行测试用例（创建执行记录并启动）
  run(id: number, data?: { browser_mode?: string }) {
    return http.post<{
      message: string
      execution: any
      status: string
    }>(`${API_URL}/test-cases/${id}/run/`, data || {})
  }
}
