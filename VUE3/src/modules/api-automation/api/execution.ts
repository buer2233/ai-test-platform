import { http } from '../../../shared/utils/http'
import type { ApiTestExecution } from '../types/execution'

const API_URL = '/v1/api-automation'

export const executionApi = {
  // 获取执行列表
  getExecutions(params?: any) {
    return http.get<{ results: ApiTestExecution[], count: number }>(`${API_URL}/executions/`, params)
  },

  // 获取单个执行
  getExecution(id: number) {
    return http.get<ApiTestExecution>(`${API_URL}/executions/${id}/`)
  },

  // 创建执行
  createExecution(data: any) {
    return http.post<ApiTestExecution>(`${API_URL}/executions/`, data)
  },

  // 更新执行
  updateExecution(id: number, data: Partial<ApiTestExecution>) {
    return http.patch<ApiTestExecution>(`${API_URL}/executions/${id}/`, data)
  },

  // 删除执行
  deleteExecution(id: number) {
    return http.delete(`${API_URL}/executions/${id}/`)
  },

  // 执行测试
  execute(id: number) {
    return http.post(`${API_URL}/executions/${id}/execute/`)
  },

  // 取消执行
  cancel(id: number) {
    return http.post(`${API_URL}/executions/${id}/cancel/`)
  },

  // 获取执行统计
  getStatistics() {
    return http.get(`${API_URL}/executions/statistics/`)
  },

  // ========== 批量执行相关 ==========

  // 按项目执行
  executeByProject(projectId: number, environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/projects/${projectId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  },

  // 按集合执行
  executeByCollection(collectionId: number, environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/collections/${collectionId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  },

  // 按手动选择执行
  executeBySelection(testCaseIds: number[], environmentId: number, executionName?: string) {
    return http.post<ApiTestExecution>(`${API_URL}/test-cases/batch_execute/`, {
      test_case_ids: testCaseIds,
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}