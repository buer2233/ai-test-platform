import { test, expect, loginByUi } from './fixtures'

test.describe('视觉与响应式基线', () => {
  test.beforeEach(async ({ mockApi }) => {
    await mockApi({ authed: true })
  })

  test('登录页采用圆角卡片和浅色背景风格', async ({ page }) => {
    await page.goto('/login')

    const card = page.getByTestId('auth-card')
    await expect(card).toBeVisible()

    const radius = await card.evaluate((el) => window.getComputedStyle(el).borderRadius)
    expect(parseFloat(radius)).toBeGreaterThan(20)

    const bg = await page.getByTestId('login-root').evaluate((el) => window.getComputedStyle(el).backgroundImage)
    expect(bg).not.toBe('none')
  })

  test('桌面布局具有固定侧栏和顶部栏', async ({ page }) => {
    await loginByUi(page)

    await expect(page.getByTestId('main-sidebar')).toBeVisible()
    await expect(page.getByTestId('main-header')).toBeVisible()
  })

  test('移动端可正常渲染头部与主要内容', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await loginByUi(page)

    await expect(page.getByTestId('main-header')).toBeVisible()
    await expect(page.locator('.layout-content')).toBeVisible()
  })
})
