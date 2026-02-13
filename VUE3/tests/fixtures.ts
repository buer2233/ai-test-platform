import { test as base, expect, type Page, type Route } from '@playwright/test'

interface MockApiOptions {
  authed?: boolean
}

const DEFAULT_USER = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com'
}

function jsonResponse(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(data)
  })
}

const paged = <T>(results: T[]) => ({
  count: results.length,
  next: null,
  previous: null,
  results
})

async function setupApiMocks(page: Page, options: MockApiOptions = {}) {
  const { authed = false } = options

  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const pathname = url.pathname

    if (pathname.endsWith('/api/api-token-auth/') && request.method() === 'POST') {
      return jsonResponse(route, { token: 'mock-token' })
    }

    if (pathname.endsWith('/api/v1/api-automation/auth/register/') && request.method() === 'POST') {
      return jsonResponse(route, { message: 'ok' })
    }

    if (pathname.endsWith('/api/v1/api-automation/auth/user/')) {
      if (authed || request.headers().authorization) {
        return jsonResponse(route, DEFAULT_USER)
      }
      return jsonResponse(route, { detail: 'Unauthorized' }, 401)
    }

    if (pathname.endsWith('/api/v1/api-automation/dashboard/overview/')) {
      return jsonResponse(route, {
        test_stats: {
          total_cases: 32,
          passed_cases: 26,
          failed_cases: 4,
          skipped_cases: 1,
          error_cases: 1,
          pass_rate: 81,
          avg_response_time: 118
        }
      })
    }

    if (pathname.endsWith('/api/v1/api-automation/dashboard/test-results/')) {
      return jsonResponse(route, paged([
        {
          id: 101,
          test_case_name: '登录接口',
          collection_name: '认证集合',
          project_name: '核心项目',
          status: 'PASSED',
          response_time: 120,
          start_time: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.endsWith('/api/v1/api-automation/projects/')) {
      return jsonResponse(route, paged([
        {
          id: 1,
          name: '核心项目',
          description: 'mock project',
          owner_name: 'admin',
          owner: { id: 1, username: 'admin' },
          collection_count: 3,
          test_case_count: 9,
          created_at: '2026-02-12T08:00:00Z',
          updated_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/api-automation/projects/') && pathname !== '/api/v1/api-automation/projects/') {
      return jsonResponse(route, {
        id: 1,
        name: '核心项目',
        description: 'mock project',
        owner_name: 'admin',
        owner: { id: 1, username: 'admin' },
        collections_count: 3,
        test_cases_count: 9
      })
    }

    if (pathname.endsWith('/api/v1/api-automation/collections/')) {
      return jsonResponse(route, paged([
        {
          id: 11,
          name: '认证集合',
          project: 1,
          project_name: '核心项目',
          description: 'mock collection',
          module: 'auth',
          test_case_count: 4,
          created_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/api-automation/collections/') && pathname !== '/api/v1/api-automation/collections/') {
      return jsonResponse(route, {
        id: 11,
        name: '认证集合',
        project: 1,
        project_name: '核心项目',
        description: 'mock collection',
        module: 'auth',
        test_case_count: 4
      })
    }

    if (pathname.endsWith('/api/v1/api-automation/test-cases/')) {
      return jsonResponse(route, paged([
        {
          id: 201,
          name: '登录接口用例',
          project: 1,
          project_name: '核心项目',
          collection: 11,
          collection_name: '认证集合',
          method: 'POST',
          url: '/api/login',
          description: 'mock test case',
          is_active: true,
          created_at: '2026-02-12T08:00:00Z',
          updated_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/api-automation/test-cases/') && pathname !== '/api/v1/api-automation/test-cases/') {
      return jsonResponse(route, {
        id: 201,
        name: '登录接口用例',
        project: 1,
        project_name: '核心项目',
        collection: 11,
        collection_name: '认证集合',
        method: 'POST',
        url: '/api/login',
        headers: [],
        query_params: [],
        body: '{"username":"admin"}',
        expected_status_code: 200,
        assertions: []
      })
    }

    if (pathname.endsWith('/api/v1/api-automation/reports/')) {
      return jsonResponse(route, paged([
        {
          id: 301,
          name: '日报告',
          status: 'COMPLETED',
          summary: { passed: 10, failed: 1 },
          created_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/api-automation/reports/') && pathname !== '/api/v1/api-automation/reports/') {
      return jsonResponse(route, {
        id: 301,
        name: '日报告',
        status: 'COMPLETED',
        summary: { passed: 10, failed: 1 },
        details: []
      })
    }

    if (pathname.endsWith('/api/v1/api-automation/environments/')) {
      return jsonResponse(route, paged([
        {
          id: 401,
          name: '测试环境',
          base_url: 'http://127.0.0.1:8000',
          project: 1,
          project_name: '核心项目',
          variables: []
        }
      ]))
    }

    if (pathname.includes('/api/v1/api-automation/http-executor')) {
      return jsonResponse(route, {
        success: true,
        status_code: 200,
        response_time: 95,
        response_data: { ok: true },
        response_headers: { 'content-type': 'application/json' }
      })
    }

    if (pathname.includes('/api/v1/api-automation/recycle-bin')) {
      return jsonResponse(route, paged([]))
    }

    if (pathname.includes('/api/v1/ui-automation/projects/')) {
      return jsonResponse(route, paged([
        {
          id: 1,
          name: 'UI 项目 A',
          description: 'mock ui project',
          owner: { id: 1, username: 'admin' },
          owner_name: 'admin',
          test_cases_count: 6,
          executions_count: 2,
          reports_count: 1,
          is_active: true,
          created_at: '2026-02-12T08:00:00Z',
          updated_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/ui-automation/test-cases/')) {
      return jsonResponse(route, paged([
        {
          id: 501,
          name: '首页烟雾测试',
          project: 1,
          project_name: 'UI 项目 A',
          description: 'mock ui case',
          browser_mode: 'headed',
          is_enabled: true,
          tags: ['smoke'],
          test_task: '打开首页并校验标题',
          executions_count: 1,
          created_at: '2026-02-12T08:00:00Z',
          updated_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/ui-automation/executions/')) {
      return jsonResponse(route, paged([
        {
          id: 601,
          test_case_name: '首页烟雾测试',
          status: 'SUCCESS',
          duration_seconds: 12,
          created_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/ui-automation/reports/')) {
      return jsonResponse(route, paged([
        {
          id: 701,
          name: 'UI 每日报告',
          status: 'COMPLETED',
          created_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    if (pathname.includes('/api/v1/')) {
      return jsonResponse(route, paged([]))
    }

    return route.continue()
  })
}

async function loginByUi(page: Page) {
  await page.goto('/login')
  const loginRoot = page.getByTestId('login-root')
  await loginRoot.locator('input[placeholder=\"请输入用户名\"]').first().fill('admin')
  await loginRoot.locator('input[placeholder=\"请输入密码\"]').first().fill('admin123')
  await page.getByTestId('login-submit').click()
}

const test = base.extend<{ mockApi: (opts?: MockApiOptions) => Promise<void> }>({
  mockApi: async ({ page }, use) => {
    await use((opts?: MockApiOptions) => setupApiMocks(page, opts))
  }
})

export { test, expect, loginByUi }
