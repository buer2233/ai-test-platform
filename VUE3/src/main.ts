import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Import Design System
import './assets/styles/global.css'

import App from './App.vue'
import { createRouterAsync } from '@core/router'

// 异步初始化应用
async function initApp() {
  try {
    // 创建包含所有路由的路由器
    const router = await createRouterAsync()

    const app = createApp(App)

    // 注册 Element Plus 图标
    for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
      app.component(key, component)
    }

    app.use(createPinia())
    app.use(router)
    app.use(ElementPlus)

    app.mount('#app')
  } catch (error) {
    console.error('[Main] Failed to initialize app:', error)
    throw error
  }
}

// 启动应用
initApp().catch((error) => {
  console.error('[Main] Failed to initialize app:', error)
})
