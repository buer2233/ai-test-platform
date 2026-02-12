import { test as base, expect, type Page } from '@playwright/test'

interface MockApiOptions {
  authed?: boolean
}

const DEFAULT_USER = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com'
}

async function fulfillJson(route: any, data: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(data)
  })
}

async function setupApiMocks(page: Page, options: MockApiOptions = {}) {
  const { authed = false } = options

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const pathname = url.pathname

    if (pathname.endsWith('/api/api-token-auth/') && request.method() === 'POST') {
      await fulfillJson(route, { token: 'mock-token' })
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/auth/user/')) {
      if (authed || request.headers()['authorization']) {
        await fulfillJson(route, DEFAULT_USER)
      } else {
        await fulfillJson(route, { detail: 'Unauthorized' }, 401)
      }
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/dashboard/overview/')) {
      await fulfillJson(route, {
        test_stats: {
          total_cases: 32,
          passed_cases: 25,
          failed_cases: 5,
          skipped_cases: 1,
          error_cases: 1,
          pass_rate: 78,
          avg_response_time: 120
        }
      })
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/dashboard/test-results/')) {
      await fulfillJson(route, {
        count: 1,
        results: [
          {
            id: 1,
            test_case_name: '登录接口',
            collection_name: '认证集合',
            project_name: '核心项目',
            status: 'PASSED',
            response_time: 110,
            start_time: '2026-02-12T08:00:00Z'
          }
        ]
      })
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/projects/')) {
      await fulfillJson(route, {
        count: 1,
        results: [{ id: 1, name: '核心项目', owner_name: 'admin', description: 'mock', collection_count: 3, test_case_count: 9 }]
      })
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/collections/')) {
      await fulfillJson(route, { count: 1, results: [{ id: 1, name: '认证集合', module: 'auth' }] })
      return
    }

    if (pathname.endsWith('/api/v1/api-automation/users/')) {
      await fulfillJson(route, { count: 1, results: [{ id: 1, username: 'admin' }] })
      return
    }

    if (pathname.includes('/api/v1/ui-automation/projects/')) {
      await fulfillJson(route, {
        count: 1,
        results: [{ id: 1, name: 'UI项目A', description: 'mock ui', owner: { username: 'admin' }, test_cases_count: 5, executions_count: 2, is_active: true, created_at: '2026-02-12T08:00:00Z' }]
      })
      return
    }

    if (pathname.includes('/api/v1/ui-automation/test-cases/')) {
      await fulfillJson(route, { count: 0, results: [] })
      return
    }

    if (pathname.includes('/api/v1/ui-automation/executions/')) {
      await fulfillJson(route, { count: 0, results: [] })
      return
    }

    if (pathname.includes('/api/v1/ui-automation/reports/')) {
      await fulfillJson(route, { count: 0, results: [] })
      return
    }

    await fulfillJson(route, { count: 0, results: [] })
  })
}

async function loginByUi(page: Page) {
  await page.goto('/login')
  await page.getByPlaceholder('请输入用户名').fill('admin')
  await page.getByPlaceholder('请输入密码').fill('admin123')
  await page.getByTestId('login-submit').click()
}

const test = base.extend<{ mockApi: (opts?: MockApiOptions) => Promise<void> }>({
  mockApi: async ({ page }, use) => {
    await use((opts?: MockApiOptions) => setupApiMocks(page, opts))
  }
})

export { test, expect, loginByUi }
