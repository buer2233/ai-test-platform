import { defineStore } from 'pinia'
import { authApi } from '../api/auth'
import type { User } from '../types/project'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem('auth_token'),
    isAuthenticated: false
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated && !!state.token
  },

  actions: {
    // 登录
    async login(username: string, password: string) {
      const response = await authApi.login(username, password)
      return response
    },

    // 注册
    async register(username: string, password: string, email: string) {
      return await authApi.register(username, password, email)
    },

    // 设置token
    setToken(token: string) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },

    // 清除token
    clearToken() {
      this.token = null
      localStorage.removeItem('auth_token')
    },

    // 获取当前用户信息
    async fetchCurrentUser() {
      try {
        const user = await authApi.getCurrentUser()
        this.user = user
        this.isAuthenticated = true
        return user
      } catch (error) {
        this.clearToken()
        this.user = null
        this.isAuthenticated = false
        throw error
      }
    },

    // 登出
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.clearToken()
        this.user = null
        this.isAuthenticated = false
      }
    },

    // 初始化认证状态
    async initAuth() {
      if (this.token) {
        try {
          await this.fetchCurrentUser()
        } catch (error) {
          this.clearToken()
        }
      }
    }
  }
})