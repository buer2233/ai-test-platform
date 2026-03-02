/**
 * 测试执行 API
 *
 * 管理测试执行任务的全生命周期：创建、运行、取消、统计。
 * 支持按项目、集合、手动选择等多种维度批量执行测试用例。
 */

import { http } from '../../../shared/utils/http'
import type { ApiTestExecution } from '../types/execution'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const executionApi = {
  /** 获取执行任务列表（支持分页和筛选） */
  getExecutions(params?: any) {
    return http.get<{ results: ApiTestExecution[], count: number }>(`${API_URL}/executions/`, params)
  },

  /** 获取单个执行任务详情 */
  getExecution(id: number) {
    return http.get<ApiTestExecution>(`${API_URL}/executions/${id}/`)
  },

  /** 创建新的执行任务 */
  createExecution(data: any) {
    return http.post<ApiTestExecution>(`${API_URL}/executions/`, data)
  },

  /** 更新执行任务信息 */
  updateExecution(id: number, data: Partial<ApiTestExecution>) {
    return http.patch<ApiTestExecution>(`${API_URL}/executions/${id}/`, data)
  },

  /** 删除执行任务 */
  deleteExecution(id: number) {
    return http.delete(`${API_URL}/executions/${id}/`)
  },

  /** 触发执行任务开始运行 */
  execute(id: number) {
    return http.post(`${API_URL}/executions/${id}/execute/`)
  },

  /** 取消正在运行的执行任务 */
  cancel(id: number) {
    return http.post(`${API_URL}/executions/${id}/cancel/`)
  },

  /** 获取执行任务的全局统计信息 */
  getStatistics() {
    return http.get(`${API_URL}/executions/statistics/`)
  },

  // ==================== 批量执行 ====================

  /** 按项目批量执行所有测试用例 */
  executeByProject(projectId: number, environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/projects/${projectId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  },

  /** 按集合批量执行测试用例 */
  executeByCollection(collectionId: number, environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/collections/${collectionId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  },

  /** 按手动选择的测试用例批量执行 */
  executeBySelection(testCaseIds: number[], environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/test-cases/batch_execute/`, {
      test_case_ids: testCaseIds,
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}