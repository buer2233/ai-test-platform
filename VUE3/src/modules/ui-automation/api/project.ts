import { http } from '../../../shared/utils/http'
import type { UiProject, UiProjectCreate, UiProjectStatistics } from '../types/project'

const API_URL = '/v1/ui-automation'

export const uiProjectApi = {
  // 获取项目列表
  getProjects(params?: any) {
    return http.get<{ results: UiProject[], count: number }>(`${API_URL}/projects/`, params)
  },

  // 获取单个项目
  getProject(id: number) {
    return http.get<UiProject>(`${API_URL}/projects/${id}/`)
  },

  // 创建项目
  createProject(data: UiProjectCreate) {
    return http.post<UiProject>(`${API_URL}/projects/`, data)
  },

  // 更新项目
  updateProject(id: number, data: Partial<UiProjectCreate>) {
    return http.patch<UiProject>(`${API_URL}/projects/${id}/`, data)
  },

  // 删除项目
  deleteProject(id: number) {
    return http.delete(`${API_URL}/projects/${id}/`)
  },

  // 获取项目统计信息
  getProjectStatistics(id: number) {
    return http.get<UiProjectStatistics>(`${API_URL}/projects/${id}/statistics/`)
  },

  // 获取项目下的测试用例
  getProjectTestCases(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/test_cases/`, params)
  },

  // 获取项目下的执行记录
  getProjectExecutions(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/executions/`, params)
  }
}
