/**
 * 用户管理 API
 *
 * 提供平台用户的查询功能。
 * 主要用于获取用户列表（如项目分配负责人时的选择列表）。
 */

import { http } from '../../../shared/utils/http'

/** API 路由前缀 */
const API_URL = '/v1/api-automation'

/** 用户信息接口 */
export interface User {
  id: number
  username: string
  email?: string
  first_name?: string
  last_name?: string
  is_active: boolean
  date_joined?: string
}

export const userApi = {
  /** 获取用户列表 */
  getUsers() {
    return http.get<{ results: User[]; count: number }>(`${API_URL}/users/`)
  },

  /** 获取单个用户信息 */
  getUser(id: number) {
    return http.get<User>(`${API_URL}/users/${id}/`)
  }
}
