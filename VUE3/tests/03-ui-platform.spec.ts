import { test, expect, loginByUi } from './fixtures'

test.describe('UI 自动化模块导航', () => {
  test('可切换到 UI 自动化并访问关键页面', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await loginByUi(page)

    await page.getByTestId('module-switcher').click()
    await page.getByText('AI 驱动 UI 测试').first().click()

    await expect(page).toHaveURL(/\/ui-automation\/projects$/)

    await page.getByRole('menuitem', { name: '测试用例' }).click()
    await expect(page).toHaveURL(/\/ui-automation\/test-cases$/)

    await page.getByRole('menuitem', { name: '执行监控' }).click()
    await expect(page).toHaveURL(/\/ui-automation\/executions$/)

    await page.getByRole('menuitem', { name: '测试报告' }).click()
    await expect(page).toHaveURL(/\/ui-automation\/reports$/)
  })
})
