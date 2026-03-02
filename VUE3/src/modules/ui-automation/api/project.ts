/**
 * 项目管理 API
 *
 * 提供 UI 自动化测试项目的增删改查、统计信息，
 * 以及项目下测试用例和执行记录的关联查询接口。
 */

import { http } from '../../../shared/utils/http'
import type { UiProject, UiProjectCreate, UiProjectStatistics } from '../types/project'

/** UI自动化模块的 API 基础路径 */
const API_URL = '/v1/ui-automation'

export const uiProjectApi = {
  /** 获取项目列表（支持分页和筛选） */
  getProjects(params?: any) {
    return http.get<{ results: UiProject[]; count: number }>(`${API_URL}/projects/`, params)
  },

  /** 根据 ID 获取单个项目详情 */
  getProject(id: number) {
    return http.get<UiProject>(`${API_URL}/projects/${id}/`)
  },

  /** 创建新项目 */
  createProject(data: UiProjectCreate) {
    return http.post<UiProject>(`${API_URL}/projects/`, data)
  },

  /** 局部更新项目信息（PATCH） */
  updateProject(id: number, data: Partial<UiProjectCreate>) {
    return http.patch<UiProject>(`${API_URL}/projects/${id}/`, data)
  },

  /** 删除指定项目（级联删除关联的用例和执行记录） */
  deleteProject(id: number) {
    return http.delete(`${API_URL}/projects/${id}/`)
  },

  /** 获取项目统计信息（用例数、执行数、成功率等） */
  getProjectStatistics(id: number) {
    return http.get<UiProjectStatistics>(`${API_URL}/projects/${id}/statistics/`)
  },

  /** 获取项目下的测试用例列表 */
  getProjectTestCases(id: number, params?: any) {
    return http.get<{ results: any[]; count: number }>(`${API_URL}/projects/${id}/test_cases/`, params)
  },

  /** 获取项目下的执行记录列表 */
  getProjectExecutions(id: number, params?: any) {
    return http.get<{ results: any[]; count: number }>(`${API_URL}/projects/${id}/executions/`, params)
  }
}
