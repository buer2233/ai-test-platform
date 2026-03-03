import path from 'path'
import type { Page } from '@playwright/test'
import { test, expect } from './fixtures'

async function prepareAuth(page: Page) {
  await page.goto('/login')
  await page.evaluate(() => {
    localStorage.setItem('auth_token', 'mock-token')
  })
}

async function gotoTrafficCapturePage(page: Page) {
  await page.goto('/projects/1/traffic-capture')
  await expect(page).toHaveURL(/projects\/1\/traffic-capture/)
}

test.describe('流量录制生成用例', () => {
  test('E2E-TRAFFIC-001 项目内上传录制文件并解析', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await prepareAuth(page)
    await page.goto('/projects/1')
    await expect(page.getByRole('button', { name: '流量录制生成' })).toBeVisible()
    await page.getByRole('button', { name: '流量录制生成' }).click()
    await expect(page).toHaveURL(/projects\/1\/traffic-capture/)

    const filePath = path.resolve(__dirname, 'fixtures/traffic-sample.json')
    await page.setInputFiles('[data-testid="traffic-upload-input"]', filePath)
    await page.getByTestId('traffic-upload-button').click()

    await expect(page.getByTestId('traffic-capture-table')).toBeVisible()
    await page.getByTestId('traffic-parse-button').first().click()
    await expect(page.getByTestId('traffic-session-table')).toContainText('session-901')
  })

  test('E2E-TRAFFIC-002 进入预览并编辑变量断言', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await prepareAuth(page)
    await gotoTrafficCapturePage(page)

    await page.getByTestId('traffic-generate-button').first().click()
    await page.getByTestId('traffic-preview-button').first().click()
    await expect(page.getByRole('dialog')).toBeVisible()

    await page.locator('[data-testid="traffic-preview-textarea"] textarea').fill(JSON.stringify({
      steps: [
        {
          step_order: 1,
          name: 'POST /api/login',
          assertions: [{ assertion_type: 'status_code', operator: 'equals', expected_value: 200 }]
        }
      ],
      variables: [
        { variable_name: 'auth_token', source_type: 'JSONPATH', expression: '$.token', target_scope: 'SCENARIO' }
      ]
    }, null, 2))
    await page.getByTestId('traffic-preview-save-button').click()
    await page.getByRole('button', { name: '关闭' }).click()
  })

  test('E2E-TRAFFIC-003 试运行通过后允许提交', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await prepareAuth(page)
    await gotoTrafficCapturePage(page)

    await page.getByTestId('traffic-trial-button').first().click()
    await expect(page.getByTestId('traffic-commit-button').first()).toBeEnabled()
  })

  test('E2E-TRAFFIC-004 试运行失败时提交门禁生效', async ({ page, mockApi }) => {
    await mockApi({ authed: true })
    await prepareAuth(page)
    await gotoTrafficCapturePage(page)

    await page.getByTestId('traffic-trial-fail-button').first().click()
    await expect(page.getByTestId('traffic-commit-button').first()).toBeDisabled()
  })
})
