import { http } from '../../../shared/utils/http'
import type { TestCaseAssertion } from '../types/testCase'

const API_URL = '/v1/api-automation'

export const assertionApi = {
  // 获取测试用例的断言列表
  getAssertions(testCaseId: number) {
    return http.get<{ results: TestCaseAssertion[], count: number }>(
      `${API_URL}/test-cases/${testCaseId}/assertions/`
    )
  },

  // 创建断言
  createAssertion(testCaseId: number, data: Partial<TestCaseAssertion>) {
    return http.post<TestCaseAssertion>(
      `${API_URL}/test-cases/${testCaseId}/assertions/`,
      data
    )
  },

  // 更新断言
  updateAssertion(testCaseId: number, assertionId: number, data: Partial<TestCaseAssertion>) {
    return http.patch<TestCaseAssertion>(
      `${API_URL}/test-cases/${testCaseId}/assertions/${assertionId}/`,
      data
    )
  },

  // 删除断言
  deleteAssertion(testCaseId: number, assertionId: number) {
    return http.delete(`${API_URL}/test-cases/${testCaseId}/assertions/${assertionId}/`)
  },

  // 批量更新断言
  batchUpdateAssertions(testCaseId: number, assertions: TestCaseAssertion[]) {
    return http.post(`${API_URL}/test-cases/${testCaseId}/assertions/batch_update/`, {
      assertions
    })
  }
}
