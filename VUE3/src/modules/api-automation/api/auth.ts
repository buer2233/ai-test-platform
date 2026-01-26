import { http } from '../../../shared/utils/http'
import type { User } from '../types/project'

export const authApi = {
  // 登录获取token
  login(username: string, password: string) {
    return http.post<{ token: string }>('/api-token-auth/', {
      username,
      password
    })
  },

  // 用户注册
  register(username: string, password: string, email: string) {
    return http.post('/v1/api-automation/users/register/', {
      username,
      password,
      email
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return http.get<User>('/v1/api-automation/auth/user/')
  },

  // 登出
  logout() {
    return http.post('/api-auth/logout/')
  }
}