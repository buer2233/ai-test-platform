/**
 * 测试用例 API
 *
 * 提供 UI 自动化测试用例的增删改查、复制、执行历史查询和直接运行等接口。
 */

import { http } from '../../../shared/utils/http'
import type { UiTestCase, UiTestCaseCreate, UiTestCaseUpdate } from '../types/testCase'

/** UI自动化模块的 API 基础路径 */
const API_URL = '/v1/ui-automation'

export const uiTestCaseApi = {
  /** 获取测试用例列表（支持分页、项目筛选和关键词搜索） */
  getTestCases(params?: any) {
    return http.get<{ results: UiTestCase[]; count: number }>(`${API_URL}/test-cases/`, params)
  },

  /** 根据 ID 获取单个测试用例详情 */
  getTestCase(id: number) {
    return http.get<UiTestCase>(`${API_URL}/test-cases/${id}/`)
  },

  /** 创建新的测试用例 */
  createTestCase(data: UiTestCaseCreate) {
    return http.post<UiTestCase>(`${API_URL}/test-cases/`, data)
  },

  /** 局部更新测试用例（PATCH） */
  updateTestCase(id: number, data: UiTestCaseUpdate) {
    return http.patch<UiTestCase>(`${API_URL}/test-cases/${id}/`, data)
  },

  /** 删除指定测试用例 */
  deleteTestCase(id: number) {
    return http.delete(`${API_URL}/test-cases/${id}/`)
  },

  /** 复制测试用例（后端生成副本并返回） */
  copyTestCase(id: number) {
    return http.post<UiTestCase>(`${API_URL}/test-cases/${id}/copy/`)
  },

  /** 获取指定用例的执行历史记录 */
  getTestCaseExecutions(id: number, params?: any) {
    return http.get<{ results: any[]; count: number }>(`${API_URL}/test-cases/${id}/executions/`, params)
  },

  /**
   * 直接运行测试用例
   * 后端自动创建执行记录并启动 browser_use 测试流程
   */
  run(id: number, data?: { browser_mode?: string }) {
    return http.post<{
      message: string
      execution: any
      status: string
    }>(`${API_URL}/test-cases/${id}/run/`, data || {})
  }
}
