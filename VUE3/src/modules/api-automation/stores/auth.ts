/**
 * 认证 Store
 *
 * 管理用户登录状态、Token 存储、以及当前用户信息。
 * Token 持久化到 localStorage，页面刷新后自动恢复登录态。
 */

import { defineStore } from 'pinia'
import { authApi } from '../api/auth'
import type { User } from '../types/project'

/** 认证状态接口 */
interface AuthState {
  /** 当前登录用户信息 */
  user: User | null
  /** 认证 Token（从 localStorage 初始化） */
  token: string | null
  /** 是否已通过认证验证 */
  isAuthenticated: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: localStorage.getItem('auth_token'),
    isAuthenticated: false
  }),

  getters: {
    /** 获取当前用户信息 */
    currentUser: (state) => state.user,
    /** 判断用户是否已登录（需同时满足认证标记和有效 Token） */
    isLoggedIn: (state) => state.isAuthenticated && !!state.token
  },

  actions: {
    /** 调用登录 API */
    async login(username: string, password: string) {
      const response = await authApi.login(username, password)
      return response
    },

    /** 调用注册 API */
    async register(username: string, password: string, email: string) {
      return await authApi.register(username, password, email)
    },

    /** 保存 Token 到状态和 localStorage */
    setToken(token: string) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },

    /** 清除 Token（登出或 Token 失效时调用） */
    clearToken() {
      this.token = null
      localStorage.removeItem('auth_token')
    },

    /** 从后端获取当前用户信息，更新认证状态 */
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

    /** 登出并清除所有认证状态 */
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.clearToken()
        this.user = null
        this.isAuthenticated = false
      }
    },

    /** 应用启动时调用，检查 Token 有效性并恢复登录态 */
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