/**
 * 数据提取配置 API
 *
 * 管理测试用例的响应数据提取规则。
 * 提取的变量可在后续测试用例中引用，实现接口间的数据传递。
 */

import { http } from '../../../shared/utils/http'
import type { TestCaseExtraction } from '../types/testCase'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const extractionApi = {
  /** 获取指定测试用例的数据提取配置列表 */
  getExtractions(testCaseId: number) {
    return http.get<{ results: TestCaseExtraction[], count: number }>(
      `${API_URL}/test-cases/${testCaseId}/extractions/`
    )
  },

  /** 为指定测试用例创建数据提取配置 */
  createExtraction(testCaseId: number, data: Partial<TestCaseExtraction>) {
    return http.post<TestCaseExtraction>(
      `${API_URL}/test-cases/${testCaseId}/extractions/`,
      data
    )
  },

  /** 更新指定数据提取配置 */
  updateExtraction(testCaseId: number, extractionId: number, data: Partial<TestCaseExtraction>) {
    return http.patch<TestCaseExtraction>(
      `${API_URL}/test-cases/${testCaseId}/extractions/${extractionId}/`,
      data
    )
  },

  /** 删除指定数据提取配置 */
  deleteExtraction(testCaseId: number, extractionId: number) {
    return http.delete(`${API_URL}/test-cases/${testCaseId}/extractions/${extractionId}/`)
  },

  /** 批量更新数据提取配置（覆盖式更新） */
  batchUpdateExtractions(testCaseId: number, extractions: TestCaseExtraction[]) {
    return http.post(`${API_URL}/test-cases/${testCaseId}/extractions/batch_update/`, {
      extractions
    })
  }
}
