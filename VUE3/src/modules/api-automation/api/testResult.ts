import { http } from '../../../shared/utils/http'
import type { TestResult } from '../types/report'

const API_URL = '/v1/api-automation'

export const testResultApi = {
  // 获取测试结果列表
  getTestResults(params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, params)
  },

  // 获取单个测试结果
  getTestResult(id: number) {
    return http.get<TestResult>(`${API_URL}/test-results/${id}/`)
  },

  // 按执行ID获取测试结果
  getResultsByExecution(executionId: number, params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, {
      execution: executionId,
      ...params
    })
  },

  // 按测试用例ID获取测试结果
  getResultsByTestCase(testCaseId: number, params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, {
      test_case: testCaseId,
      ...params
    })
  }
}
