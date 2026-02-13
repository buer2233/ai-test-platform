import { test, expect, type ConsoleMessage, type Response } from '@playwright/test'

function shouldIgnoreApiError(url: string, status: number) {
  // 登录页初始化阶段可能触发未登录态探测
  if (url.includes('/api/v1/api-automation/auth/user/') && status === 401) {
    return true
  }
  return false
}

test.describe('探索性巡检 - 全页面点击与报错采集', () => {
  test('登录后遍历 API/UI 页面并检查前端与接口报错', async ({ page }) => {
    const consoleErrors: string[] = []
    const pageErrors: string[] = []
    const apiErrors: string[] = []

    page.on('console', (msg: ConsoleMessage) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    page.on('pageerror', (err: Error) => {
      pageErrors.push(err.message)
    })

    page.on('response', async (response: Response) => {
      const url = response.url()
      if (!url.includes('/api/')) {
        return
      }
      const status = response.status()
      if (status >= 400 && !shouldIgnoreApiError(url, status)) {
        apiErrors.push(`${status} ${url}`)
      }
    })

    await page.goto('/login')
    await expect(page.getByTestId('login-root')).toBeVisible()

    await page.locator('input[placeholder="请输入用户名"]').first().fill('admin')
    await page.locator('input[placeholder="请输入密码"]').first().fill('admin123')
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByTestId('main-sidebar')).toBeVisible()

    const apiMenuOrder = [
      '仪表盘',
      '项目管理',
      '集合管理',
      '测试用例',
      '环境管理',
      'HTTP 执行器',
      '测试报告',
      '回收站'
    ]

    for (const label of apiMenuOrder) {
      await page.getByRole('menuitem', { name: label }).click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
    }

    await page.getByTestId('module-switcher').click()
    await page.getByText('AI 驱动 UI 测试').first().click()
    await expect(page).toHaveURL(/\/ui-automation\/projects$/)

    const uiMenuOrder = ['项目管理', '测试用例', '执行监控', '测试报告']
    for (const label of uiMenuOrder) {
      await page.getByRole('menuitem', { name: label }).click()
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
    }

    // 巡检无侧栏直达入口但在路由中存在的关键页面
    const directRoutes = [
      '/http-execution-records',
      '/test-cases/create',
      '/ui-automation/test-cases/create'
    ]
    for (const path of directRoutes) {
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
    }

    const mergedErrors = [
      ...consoleErrors.map((item) => `console: ${item}`),
      ...pageErrors.map((item) => `pageerror: ${item}`),
      ...apiErrors.map((item) => `api: ${item}`)
    ]

    expect(
      mergedErrors,
      `巡检发现前端/接口错误:\n${mergedErrors.join('\n')}`
    ).toEqual([])
  })
})
