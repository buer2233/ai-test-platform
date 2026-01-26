import { http } from '../../../shared/utils/http'
import type { ApiTestCase, ApiTestCaseCreate, ApiTestCaseList, TestCaseExecution, RunTestRequest } from '../types/testCase'
import type { CascadePreviewResponse } from './recycleBin'

const API_URL = '/v1/api-automation'

export const testCaseApi = {
  // 获取测试用例列表
  getTestCases(params?: any) {
    return http.get<{ results: ApiTestCaseList[], count: number }>(`${API_URL}/test-cases/`, params)
  },

  // 获取单个测试用例
  getTestCase(id: number) {
    return http.get<ApiTestCase>(`${API_URL}/test-cases/${id}/`)
  },

  // 创建测试用例
  createTestCase(data: ApiTestCaseCreate) {
    return http.post<ApiTestCase>(`${API_URL}/test-cases/`, data)
  },

  // 更新测试用例
  updateTestCase(id: number, data: Partial<ApiTestCaseCreate>) {
    return http.patch<ApiTestCase>(`${API_URL}/test-cases/${id}/`, data)
  },

  // 删除测试用例
  deleteTestCase(id: number) {
    return http.delete(`${API_URL}/test-cases/${id}/`)
  },

  // 预览删除影响
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/test-cases/${id}/preview_delete/`)
  },

  // 克隆测试用例
  cloneTestCase(id: number, data: { name: string }) {
    return http.post<ApiTestCase>(`${API_URL}/test-cases/${id}/clone/`, data)
  },

  // 获取测试用例统计
  getTestCaseStatistics() {
    return http.get<any>(`${API_URL}/test-cases/statistics/`)
  },

  // 执行单个测试用例
  runTestCase(id: number, data: RunTestRequest) {
    return http.post<TestCaseExecution>(`${API_URL}/test-cases/${id}/run_test/`, data)
  }
}