/**
 * 测试结果 API
 *
 * 查询测试执行产生的结果数据。
 * 支持按执行任务 ID 或测试用例 ID 筛选结果。
 */

import { http } from '../../../shared/utils/http'
import type { TestResult } from '../types/report'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const testResultApi = {
  /** 获取测试结果列表（支持分页和筛选） */
  getTestResults(params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, params)
  },

  /** 获取单个测试结果详情 */
  getTestResult(id: number) {
    return http.get<TestResult>(`${API_URL}/test-results/${id}/`)
  },

  /** 按执行任务 ID 获取测试结果列表 */
  getResultsByExecution(executionId: number, params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, {
      execution: executionId,
      ...params
    })
  },

  /** 按测试用例 ID 获取测试结果列表 */
  getResultsByTestCase(testCaseId: number, params?: any) {
    return http.get<{ results: TestResult[], count: number }>(`${API_URL}/test-results/`, {
      test_case: testCaseId,
      ...params
    })
  }
}
