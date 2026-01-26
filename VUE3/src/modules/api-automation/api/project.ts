import { http } from '../../../shared/utils/http'
import type { ApiProject, ApiProjectCreate } from '../types/project'
import type { CascadePreviewResponse } from './recycleBin'

const API_URL = '/v1/api-automation'

export const projectApi = {
  // 获取项目列表
  getProjects(params?: any) {
    return http.get<{ results: ApiProject[], count: number }>(`${API_URL}/projects/`, params)
  },

  // 获取单个项目
  getProject(id: number) {
    return http.get<ApiProject>(`${API_URL}/projects/${id}/`)
  },

  // 创建项目
  createProject(data: ApiProjectCreate) {
    return http.post<ApiProject>(`${API_URL}/projects/`, data)
  },

  // 更新项目
  updateProject(id: number, data: Partial<ApiProjectCreate>) {
    return http.patch<ApiProject>(`${API_URL}/projects/${id}/`, data)
  },

  // 删除项目
  deleteProject(id: number) {
    return http.delete(`${API_URL}/projects/${id}/`)
  },

  // 预览删除影响
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/projects/${id}/preview_delete/`)
  },

  // 获取项目的集合
  getProjectCollections(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/collections/`, params)
  },

  // 获取项目的测试用例
  getProjectTestCases(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/test_cases/`, params)
  },

  // 克隆项目
  cloneProject(id: number, data: { name: string }) {
    return http.post<ApiProject>(`${API_URL}/projects/${id}/clone/`, data)
  },

  // ========== 批量执行相关 ==========

  // 按项目执行测试
  execute(projectId: number, environmentId: number, executionName?: string) {
    return http.post(`${API_URL}/projects/${projectId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}

// 导出回收站API
export * from './recycleBin'