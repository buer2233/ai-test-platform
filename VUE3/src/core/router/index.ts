import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// 导入API自动化模块路由
import { routes as apiAutomationRoutes } from '@api-automation/router'

// 导入UI自动化模块路由 (使用相对路径避免别名解析问题)
import { routes as uiAutomationRoutes } from '../../modules/ui-automation/router/index.ts'

// 路由守卫函数
function setupRouterGuard(router: ReturnType<typeof createRouter>) {
  router.beforeEach((to, from, next) => {
    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - 测试平台`
    }

    // 认证检查（如果需要）
    const token = localStorage.getItem('auth_token')
    if (to.meta.requiresAuth !== false && !token && to.path !== '/login') {
      // 未登录，跳转到登录页
      next('/login')
    } else {
      next()
    }
  })
}

// 导出创建路由器的函数（异步，保持向后兼容）
export async function createRouterAsync() {
  // 合并所有路由
  const routes: RouteRecordRaw[] = [
    // API自动化测试模块路由
    ...apiAutomationRoutes,

    // UI自动化测试模块路由
    ...(uiAutomationRoutes || []),

    // 404重定向
    {
      path: '/:pathMatch(.*)*',
      redirect: '/projects'
    }
  ]

  const router = createRouter({
    history: createWebHistory(),
    routes
  })

  // 设置路由守卫
  setupRouterGuard(router)

  return router
}

// 同步创建路由器（包含所有模块，用于向后兼容）
const router = createRouter({
  history: createWebHistory(),
  routes: [
    // API自动化测试模块路由
    ...apiAutomationRoutes,

    // UI自动化测试模块路由
    ...uiAutomationRoutes,

    // 404重定向
    {
      path: '/:pathMatch(.*)*',
      redirect: '/projects'
    }
  ]
})

// 设置路由守卫
setupRouterGuard(router)

export default router
