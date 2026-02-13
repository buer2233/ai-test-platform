import { test, expect, loginByUi } from './fixtures'

test.describe('API 自动化模块导航', () => {
  test('可在核心菜单中切换页面', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await loginByUi(page)

    await expect(page).toHaveURL(/\/dashboard$/)

    await page.getByRole('menuitem', { name: '项目管理' }).click()
    await expect(page).toHaveURL(/\/projects$/)

    await page.getByRole('menuitem', { name: '集合管理' }).click()
    await expect(page).toHaveURL(/\/collections$/)

    await page.getByRole('menuitem', { name: '测试用例' }).click()
    await expect(page).toHaveURL(/\/test-cases$/)

    await page.getByRole('menuitem', { name: '环境管理' }).click()
    await expect(page).toHaveURL(/\/environments$/)

    await page.getByRole('menuitem', { name: 'HTTP 执行器' }).click()
    await expect(page).toHaveURL(/\/http-executor$/)

    await page.getByRole('menuitem', { name: '测试报告' }).click()
    await expect(page).toHaveURL(/\/reports$/)

    await page.getByRole('menuitem', { name: '回收站' }).click()
    await expect(page).toHaveURL(/\/recycle-bin$/)
  })
})
