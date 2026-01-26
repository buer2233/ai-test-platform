import { http } from '../../../shared/utils/http'
import type { TestCaseExtraction } from '../types/testCase'

const API_URL = '/v1/api-automation'

export const extractionApi = {
  // 获取测试用例的数据提取配置列表
  getExtractions(testCaseId: number) {
    return http.get<{ results: TestCaseExtraction[], count: number }>(
      `${API_URL}/test-cases/${testCaseId}/extractions/`
    )
  },

  // 创建数据提取配置
  createExtraction(testCaseId: number, data: Partial<TestCaseExtraction>) {
    return http.post<TestCaseExtraction>(
      `${API_URL}/test-cases/${testCaseId}/extractions/`,
      data
    )
  },

  // 更新数据提取配置
  updateExtraction(testCaseId: number, extractionId: number, data: Partial<TestCaseExtraction>) {
    return http.patch<TestCaseExtraction>(
      `${API_URL}/test-cases/${testCaseId}/extractions/${extractionId}/`,
      data
    )
  },

  // 删除数据提取配置
  deleteExtraction(testCaseId: number, extractionId: number) {
    return http.delete(`${API_URL}/test-cases/${testCaseId}/extractions/${extractionId}/`)
  },

  // 批量更新数据提取配置
  batchUpdateExtractions(testCaseId: number, extractions: TestCaseExtraction[]) {
    return http.post(`${API_URL}/test-cases/${testCaseId}/extractions/batch_update/`, {
      extractions
    })
  }
}
