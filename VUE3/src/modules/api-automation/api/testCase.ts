/**
 * 测试用例 API
 *
 * 管理 API 测试用例的全生命周期：增删改查、克隆、统计、执行。
 * 测试用例定义了具体的 HTTP 请求配置和预期断言。
 */

import { http } from '../../../shared/utils/http'
import type { ApiTestCase, ApiTestCaseCreate, ApiTestCaseList, TestCaseExecution, RunTestRequest } from '../types/testCase'
import type { CascadePreviewResponse } from './recycleBin'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const testCaseApi = {
  /** 获取测试用例列表（支持分页和筛选） */
  getTestCases(params?: any) {
    return http.get<{ results: ApiTestCaseList[], count: number }>(`${API_URL}/test-cases/`, params)
  },

  /** 获取单个测试用例详情（包含断言和数据提取配置） */
  getTestCase(id: number) {
    return http.get<ApiTestCase>(`${API_URL}/test-cases/${id}/`)
  },

  /** 创建新的测试用例 */
  createTestCase(data: ApiTestCaseCreate) {
    return http.post<ApiTestCase>(`${API_URL}/test-cases/`, data)
  },

  /** 更新测试用例配置 */
  updateTestCase(id: number, data: Partial<ApiTestCaseCreate>) {
    return http.patch<ApiTestCase>(`${API_URL}/test-cases/${id}/`, data)
  },

  /** 软删除测试用例（可从回收站恢复） */
  deleteTestCase(id: number) {
    return http.delete(`${API_URL}/test-cases/${id}/`)
  },

  /** 预览删除影响范围，展示级联删除的关联数据 */
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/test-cases/${id}/preview_delete/`)
  },

  /** 克隆测试用例（生成副本） */
  cloneTestCase(id: number, data: { name: string }) {
    return http.post<ApiTestCase>(`${API_URL}/test-cases/${id}/clone/`, data)
  },

  /** 获取测试用例的全局统计数据 */
  getTestCaseStatistics() {
    return http.get<any>(`${API_URL}/test-cases/statistics/`)
  },

  /** 在指定环境中执行单个测试用例 */
  runTestCase(id: number, data: RunTestRequest) {
    return http.post<TestCaseExecution>(`${API_URL}/test-cases/${id}/run_test/`, data)
  }
}