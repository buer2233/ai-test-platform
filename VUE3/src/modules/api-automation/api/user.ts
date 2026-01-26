import { http } from '../../../shared/utils/http'

const API_URL = '/v1/api-automation'

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
  // 获取用户列表
  getUsers() {
    return http.get<{ results: User[]; count: number }>(`${API_URL}/users/`)
  },

  // 获取单个用户
  getUser(id: number) {
    return http.get<User>(`${API_URL}/users/${id}/`)
  }
}
