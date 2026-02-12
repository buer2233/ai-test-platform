import { test, expect } from './fixtures'

test.describe('登录与基础导航', () => {
  test('未登录访问首页会跳转到登录页', async ({ page, mockApi }) => {
    await mockApi({ authed: false })
    await page.goto('/')
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'API 自动化测试平台' })).toBeVisible()
  })

  test('登录页可切换到注册Tab并返回登录', async ({ page, mockApi }) => {
    await mockApi({ authed: false })
    await page.goto('/login')

    await page.getByTestId('register-tab').click()
    await expect(page.getByRole('button', { name: '注册账号' })).toBeVisible()

    await page.getByTestId('login-tab').click()
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })
})
