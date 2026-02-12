import { test, expect, loginByUi } from './fixtures'

test.describe('API 平台主流程', () => {
  test.beforeEach(async ({ mockApi }) => {
    await mockApi({ authed: true })
  })

  test('登录后进入仪表盘并展示核心模块', async ({ page }) => {
    await loginByUi(page)
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByText('测试报告仪表盘')).toBeVisible()

    await expect(page.getByRole('menuitem', { name: /项目管理/ })).toBeVisible()
    await expect(page.getByRole('menuitem', { name: /集合管理/ })).toBeVisible()
    await expect(page.getByRole('menuitem', { name: /HTTP 执行器/ })).toBeVisible()
  })

  test('可从侧栏进入项目管理页', async ({ page }) => {
    await loginByUi(page)
    await page.getByRole('menuitem', { name: /项目管理/ }).click()
    await expect(page).toHaveURL(/\/projects$/)
    await expect(page.getByRole('heading', { name: '项目管理' })).toBeVisible()
  })
})
