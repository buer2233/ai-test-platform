import { test, expect, loginByUi } from './fixtures'

test.describe('UI 报告截图展示', () => {
  test.beforeEach(async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await loginByUi(page)
    // 切换到 UI 自动化模块
    await page.getByTestId('module-switcher').click()
    await page.getByText('AI 驱动 UI 测试').first().click()
    await expect(page).toHaveURL(/\/ui-automation\/projects$/)
  })

  test('报告详情页展示步骤时间线和截图', async ({ page }) => {
    // 直接导航到报告详情页
    await page.goto('/ui-automation/reports/701')
    await page.waitForLoadState('networkidle')

    // 应能看到报告标题
    await expect(page.getByText('测试报告 #701')).toBeVisible()

    // 应显示执行概览
    await expect(page.getByText('执行概览')).toBeVisible()
    await expect(page.getByText('2 步骤')).toBeVisible()

    // 应显示步骤列表
    await expect(page.getByText('执行步骤')).toBeVisible()
    // 使用 step-goal 类来精确定位步骤目标文本
    await expect(page.locator('.step-goal', { hasText: '打开首页' })).toBeVisible()
    await expect(page.locator('.step-goal', { hasText: '校验标题' })).toBeVisible()

    // 展开第一个步骤查看截图（最后一步默认展开）
    const firstStep = page.locator('.step-item').first()
    await firstStep.locator('.step-header').click()

    // 应有截图区域（el-image 元素）
    await expect(firstStep.locator('.screenshot-thumb')).toBeVisible()

    // 应显示最终结果
    await expect(page.locator('.final-result').getByText('标题验证通过')).toBeVisible()
  })

  test('执行监控页显示已完成执行的截图', async ({ page }) => {
    // 导航到执行详情页
    await page.goto('/ui-automation/executions/601')
    await page.waitForLoadState('networkidle')

    // 应能看到执行监控标题
    await expect(page.getByText('执行监控 #601')).toBeVisible()

    // 应显示测试用例名称
    await expect(page.getByText('首页烟雾测试').first()).toBeVisible()

    // 截图区域应显示加载的截图（从报告获取）
    const screenshotContainer = page.locator('.screenshot-container')
    // 截图数量应为 2（从 mock 报告中有 2 个带 screenshot_path 的步骤）
    const screenshotItems = screenshotContainer.locator('.screenshot-item')
    await expect(screenshotItems).toHaveCount(2, { timeout: 10000 })
  })

  test('报告文件不存在时不渲染步骤', async ({ page }) => {
    // 重新设置 mock：report file 返回 404
    await page.route('**/api/v1/ui-automation/reports/file**', async (route) => {
      return route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error: '报告文件不存在: test-report.json',
          message: '报告文件不存在: test-report.json',
          error_code: 'REPORT_NOT_FOUND'
        })
      })
    })

    // 监听 file 请求响应
    const fileResponsePromise = page.waitForResponse(
      resp => resp.url().includes('/reports/file') && resp.status() === 404
    )

    await page.goto('/ui-automation/reports/701')
    const fileResponse = await fileResponsePromise
    expect(fileResponse.status()).toBe(404)

    // 报告文件加载失败后，不应渲染步骤时间线
    await expect(page.locator('.step-item')).toHaveCount(0)
  })

  test('报告解析失败时不渲染步骤', async ({ page }) => {
    // 重新设置 mock：report file 返回 422 解析错误
    await page.route('**/api/v1/ui-automation/reports/file**', async (route) => {
      return route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          error: '报告文件格式错误: Expecting value',
          message: '报告文件格式错误: Expecting value',
          error_code: 'REPORT_PARSE_ERROR'
        })
      })
    })

    // 监听 file 请求响应
    const fileResponsePromise = page.waitForResponse(
      resp => resp.url().includes('/reports/file') && resp.status() === 422
    )

    await page.goto('/ui-automation/reports/701')
    const fileResponse = await fileResponsePromise
    expect(fileResponse.status()).toBe(422)

    // 报告解析失败后，不应渲染步骤时间线
    await expect(page.locator('.step-item')).toHaveCount(0)
  })

  test('执行出错时显示错误信息', async ({ page }) => {
    // Mock 执行详情返回 error 状态
    await page.route('**/api/v1/ui-automation/executions/602/**', async (route) => {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 602,
          test_case: 501,
          test_case_name: '首页烟雾测试',
          project: 1,
          project_name: 'UI 项目 A',
          status: 'error',
          browser_mode: 'headed',
          duration_seconds: 5,
          started_at: '2026-02-12T08:00:00Z',
          completed_at: '2026-02-12T08:00:05Z',
          error_message: 'OPENAI_API_KEY 环境变量未设置',
          agent_history: '',
          report: null,
          created_at: '2026-02-12T08:00:00Z'
        })
      })
    })

    await page.goto('/ui-automation/executions/602')
    await page.waitForLoadState('networkidle')

    // 应显示错误信息卡片
    await expect(page.getByText('错误信息')).toBeVisible()
    await expect(page.getByText('OPENAI_API_KEY 环境变量未设置')).toBeVisible()
  })
})
