/**
 * API 自动化测试模块 - 应用入口
 *
 * 负责创建和配置 Vue 应用实例：
 * 1. 注册路由（含路由守卫：页面标题、登录验证）
 * 2. 注册 Pinia 状态管理
 * 3. 注册 Element Plus UI 框架及图标
 * 4. 挂载到 DOM
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import { routes } from './router'

// ==================== 路由配置 ====================

const router = createRouter({
  history: createWebHistory(),
  routes
})

/** 全局路由守卫：设置页面标题、检查登录状态 */
router.beforeEach(async (to, from, next) => {
  // 设置浏览器标签页标题
  document.title = to.meta.title ? `${to.meta.title} - API自动化测试平台` : 'API自动化测试平台'

  // 需要认证的页面，未登录则跳转到登录页
  if (to.meta.requiresAuth !== false) {
    const token = localStorage.getItem('auth_token')
    if (!token && to.path !== '/login') {
      next('/login')
      return
    }
  }

  // 已登录用户访问登录页时，重定向到仪表盘
  if (to.path === '/login') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      next('/dashboard')
      return
    }
  }

  next()
})

// ==================== 应用初始化 ====================

const app = createApp(App)

// 注册 Element Plus 图标组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 安装插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')
