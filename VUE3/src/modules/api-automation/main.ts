import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import { routes } from './router'
import { createRouter, createWebHistory } from 'vue-router'

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - API自动化测试平台` : 'API自动化测试平台'

  // 检查是否需要登录
  if (to.meta.requiresAuth !== false) {
    const token = localStorage.getItem('auth_token')
    if (!token && to.path !== '/login') {
      next('/login')
      return
    }
  }

  // 已登录用户不能访问登录页
  if (to.path === '/login') {
    const token = localStorage.getItem('auth_token')
    if (token) {
      next('/dashboard')
      return
    }
  }

  next()
})

// 创建应用实例
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 安装插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 挂载应用
app.mount('#app')
