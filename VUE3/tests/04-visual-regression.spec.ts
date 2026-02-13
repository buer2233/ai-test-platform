import { test, expect, loginByUi } from './fixtures'

test.describe('视觉与响应式', () => {
  test('登录页在移动端保持布局稳定', async ({ page, mockApi }) => {
    await mockApi({ authed: false })
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/login')

    await expect(page.getByTestId('auth-card')).toBeVisible()

    const hasHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
    expect(hasHorizontalOverflow).toBeFalsy()
  })

  test('主框架具有侧边栏与卡片化背景', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await loginByUi(page)

    await expect(page.getByTestId('main-sidebar')).toBeVisible()
    await expect(page.getByTestId('main-header')).toBeVisible()

    const bodyBackground = await page.evaluate(() => getComputedStyle(document.body).backgroundImage)
    expect(bodyBackground.length).toBeGreaterThan(0)
    expect(bodyBackground).toContain('gradient')
  })
})
