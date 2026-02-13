import { test, expect } from './fixtures'

test.describe('认证与基础壳层', () => {
  test('未登录访问受保护页面跳转登录页', async ({ page, mockApi }) => {
    await mockApi({ authed: false })
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByTestId('login-root')).toBeVisible()
  })

  test('登录页可在登录/注册视图切换', async ({ page, mockApi }) => {
    await mockApi({ authed: false })
    await page.goto('/login')

    await page.getByTestId('register-tab').click()
    await expect(page.getByRole('button', { name: '注册账号' })).toBeVisible()

    await page.getByTestId('login-tab').click()
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })

  test('登录成功后进入平台主界面', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await page.goto('/login')

    const loginRoot = page.getByTestId('login-root')
    await loginRoot.locator('input[placeholder=\"请输入用户名\"]').first().fill('admin')
    await loginRoot.locator('input[placeholder=\"请输入密码\"]').first().fill('admin123')
    await page.getByTestId('login-submit').click()

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByTestId('main-sidebar')).toBeVisible()
    await expect(page.getByTestId('main-header')).toBeVisible()
  })
})
