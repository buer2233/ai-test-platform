/**
 * 应用入口文件
 *
 * 负责：
 * 1. 创建 Vue 应用实例
 * 2. 注册全局插件（Pinia 状态管理、Vue Router、Element Plus 及其图标）
 * 3. 挂载应用到 DOM
 */

// ---- Vue 核心 ----
import { createApp } from 'vue'
import { createPinia } from 'pinia'

// ---- Element Plus 及图标 ----
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// ---- 全局样式（设计系统） ----
import './assets/styles/global.css'

// ---- 应用根组件与路由 ----
import App from './App.vue'
import { createRouterAsync } from '@core/router'

/**
 * 异步初始化并挂载应用
 *
 * 使用异步函数是因为路由创建过程（createRouterAsync）可能需要
 * 等待模块路由的动态加载完成后才能合并所有路由配置。
 */
async function initApp(): Promise<void> {
  // 创建包含所有模块路由的路由实例
  const router = await createRouterAsync()

  const app = createApp(App)

  // 批量注册 Element Plus 图标为全局组件
  for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(name, component)
  }

  // 注册全局插件
  app.use(createPinia())
  app.use(router)
  app.use(ElementPlus)

  // 挂载到 #app 节点
  app.mount('#app')
}

// 启动应用，捕获顶层初始化异常
initApp().catch((error) => {
  console.error('[Main] 应用初始化失败:', error)
})
