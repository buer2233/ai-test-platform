/**
 * 认证 API
 *
 * 处理用户登录、注册、登出以及获取当前用户信息。
 * 登录成功后返回 Token，用于后续请求的身份验证。
 */

import { http } from '../../../shared/utils/http'
import type { User } from '../types/project'

export const authApi = {
  /** 用户登录，返回认证 Token */
  login(username: string, password: string) {
    return http.post<{ token: string }>('/api-token-auth/', {
      username,
      password
    })
  },

  /** 用户注册 */
  register(username: string, password: string, email: string) {
    return http.post('/v1/api-automation/users/register/', {
      username,
      password,
      email
    })
  },

  /** 获取当前已登录用户信息 */
  getCurrentUser() {
    return http.get<User>('/v1/api-automation/auth/user/')
  },

  /** 用户登出 */
  logout() {
    return http.post('/api-auth/logout/')
  }
}