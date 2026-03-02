/**
 * 核心路由配置
 *
 * 职责：
 * 1. 合并各业务模块（API 自动化、UI 自动化）的路由定义
 * 2. 配置全局路由守卫（页面标题、认证检查）
 * 3. 导出异步路由创建函数供 main.ts 使用
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// ---- 业务模块路由导入 ----
import { routes as apiAutomationRoutes } from '@api-automation/router'
// 使用相对路径避免别名解析问题
import { routes as uiAutomationRoutes } from '../../modules/ui-automation/router/index.ts'

/**
 * 设置全局路由守卫
 *
 * - 根据路由 meta.title 动态设置浏览器标签页标题
 * - 检查 localStorage 中的认证令牌，未登录时重定向到登录页
 *
 * @param router - Vue Router 实例
 */
function setupRouterGuard(router: ReturnType<typeof createRouter>): void {
  router.beforeEach((to, _from, next) => {
    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - 测试平台`
    }

    // 认证检查：meta.requiresAuth 未明确设为 false 时均需要登录
    const token = localStorage.getItem('auth_token')
    if (to.meta.requiresAuth !== false && !token && to.path !== '/login') {
      next('/login')
    } else {
      next()
    }
  })
}

/**
 * 异步创建路由实例
 *
 * 合并所有业务模块路由，并设置 404 兜底重定向。
 * 使用异步函数以便未来支持路由的动态加载。
 *
 * @returns 配置完成的 Vue Router 实例
 */
export async function createRouterAsync(): Promise<ReturnType<typeof createRouter>> {
  const routes: RouteRecordRaw[] = [
    // API 自动化测试模块路由
    ...apiAutomationRoutes,

    // UI 自动化测试模块路由
    ...(uiAutomationRoutes || []),

    // 兜底路由：未匹配的路径重定向到项目列表页
    {
      path: '/:pathMatch(.*)*',
      redirect: '/projects'
    }
  ]

  const router = createRouter({
    history: createWebHistory(),
    routes
  })

  setupRouterGuard(router)

  return router
}
