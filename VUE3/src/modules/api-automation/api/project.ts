/**
 * 项目管理 API
 *
 * 项目是 API 自动化测试的顶层组织单元。
 * 支持项目的增删改查、克隆、级联删除预览、以及按项目执行测试。
 */

import { http } from '../../../shared/utils/http'
import type { ApiProject, ApiProjectCreate } from '../types/project'
import type { CascadePreviewResponse } from './recycleBin'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

export const projectApi = {
  /** 获取项目列表（支持分页和筛选） */
  getProjects(params?: any) {
    return http.get<{ results: ApiProject[], count: number }>(`${API_URL}/projects/`, params)
  },

  /** 获取单个项目详情 */
  getProject(id: number) {
    return http.get<ApiProject>(`${API_URL}/projects/${id}/`)
  },

  /** 创建新项目 */
  createProject(data: ApiProjectCreate) {
    return http.post<ApiProject>(`${API_URL}/projects/`, data)
  },

  /** 更新项目信息 */
  updateProject(id: number, data: Partial<ApiProjectCreate>) {
    return http.patch<ApiProject>(`${API_URL}/projects/${id}/`, data)
  },

  /** 软删除项目（可从回收站恢复） */
  deleteProject(id: number) {
    return http.delete(`${API_URL}/projects/${id}/`)
  },

  /** 预览删除影响范围，展示级联删除的关联数据 */
  previewDelete(id: number) {
    return http.get<CascadePreviewResponse>(`${API_URL}/projects/${id}/preview_delete/`)
  },

  /** 获取项目下的集合列表 */
  getProjectCollections(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/collections/`, params)
  },

  /** 获取项目下的测试用例列表 */
  getProjectTestCases(id: number, params?: any) {
    return http.get<{ results: any[], count: number }>(`${API_URL}/projects/${id}/test_cases/`, params)
  },

  /** 克隆项目（包括其下所有集合和测试用例） */
  cloneProject(id: number, data: { name: string }) {
    return http.post<ApiProject>(`${API_URL}/projects/${id}/clone/`, data)
  },

  // ==================== 批量执行 ====================

  /** 按项目执行测试（需指定运行环境） */
  execute(projectId: number, environmentId: number, executionName?: string) {
    return http.post(`${API_URL}/projects/${projectId}/execute/`, {
      environment_id: environmentId,
      execution_name: executionName
    })
  }
}

/** 导出回收站 API（供其他模块引用级联删除预览类型） */
export * from './recycleBin'