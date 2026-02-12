import { test, expect, loginByUi } from './fixtures'

test.describe('UI 自动化平台流程', () => {
  test.beforeEach(async ({ mockApi }) => {
    await mockApi({ authed: true })
  })

  test('可从模块切换下拉进入 UI 自动化项目页', async ({ page }) => {
    await loginByUi(page)
    await page.getByTestId('module-switcher').click()
    await page.getByText('AI 驱动 UI 测试').first().click()

    await expect(page).toHaveURL(/\/ui-automation\/projects$/)
    await expect(page.getByRole('heading', { name: 'UI测试项目' })).toBeVisible()
  })

  test('UI 平台侧栏菜单可访问执行与报告', async ({ page }) => {
    await loginByUi(page)
    await page.getByTestId('module-switcher').click()
    await page.getByText('AI 驱动 UI 测试').first().click()

    await page.getByRole('menuitem', { name: /执行监控/ }).click()
    await expect(page).toHaveURL(/\/ui-automation\/executions$/)

    await page.getByRole('menuitem', { name: /测试报告/ }).click()
    await expect(page).toHaveURL(/\/ui-automation\/reports$/)
  })
})
