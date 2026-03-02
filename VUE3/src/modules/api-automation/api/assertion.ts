/**
 * 断言配置 API
 *
 * 管理测试用例的断言规则，包括增删改查及批量更新。
 * 断言用于验证 API 响应是否符合预期（如状态码、响应体内容等）。
 */

import { http } from '../../../shared/utils/http'
import type { TestCaseAssertion } from '../types/testCase'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const assertionApi = {
  /** 获取指定测试用例的断言列表 */
  getAssertions(testCaseId: number) {
    return http.get<{ results: TestCaseAssertion[], count: number }>(
      `${API_URL}/test-cases/${testCaseId}/assertions/`
    )
  },

  /** 为指定测试用例创建断言 */
  createAssertion(testCaseId: number, data: Partial<TestCaseAssertion>) {
    return http.post<TestCaseAssertion>(
      `${API_URL}/test-cases/${testCaseId}/assertions/`,
      data
    )
  },

  /** 更新指定断言的配置 */
  updateAssertion(testCaseId: number, assertionId: number, data: Partial<TestCaseAssertion>) {
    return http.patch<TestCaseAssertion>(
      `${API_URL}/test-cases/${testCaseId}/assertions/${assertionId}/`,
      data
    )
  },

  /** 删除指定断言 */
  deleteAssertion(testCaseId: number, assertionId: number) {
    return http.delete(`${API_URL}/test-cases/${testCaseId}/assertions/${assertionId}/`)
  },

  /** 批量更新断言（覆盖式更新） */
  batchUpdateAssertions(testCaseId: number, assertions: TestCaseAssertion[]) {
    return http.post(`${API_URL}/test-cases/${testCaseId}/assertions/batch_update/`, {
      assertions
    })
  }
}
