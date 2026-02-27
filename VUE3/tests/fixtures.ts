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

    // UI automation: screenshot endpoint
    if (pathname.includes('/api/v1/ui-automation/reports/screenshot')) {
      // Return a 1x1 transparent PNG
      const pngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
      return route.fulfill({
        status: 200,
        contentType: 'image/png',
        body: Buffer.from(pngBase64, 'base64')
      })
    }

    // UI automation: report file content (JSON report)
    if (pathname.includes('/api/v1/ui-automation/reports/file')) {
      return jsonResponse(route, {
        history: [
          {
            model_output: {
              evaluation_previous_goal: null,
              memory: '开始测试',
              next_goal: '打开首页',
              action: [{ navigate: { url: 'https://example.com' } }]
            },
            result: [{ is_done: false, success: true }],
            state: {
              url: 'https://example.com',
              title: '示例首页',
              tabs: [{ url: 'https://example.com', title: '示例首页', target_id: '1', parent_target_id: null }],
              screenshot_path: 'D:/mock/screenshots/step1.png'
            },
            metadata: { step_number: 1, step_start_time: 1700000000, step_end_time: 1700000005, step_interval: 5 },
            state_message: ''
          },
          {
            model_output: {
              evaluation_previous_goal: '已打开首页',
              memory: '首页已加载',
              next_goal: '校验标题',
              action: [{ done: { text: '标题验证成功', success: true } }]
            },
            result: [{ is_done: true, success: true, extracted_content: '标题验证通过' }],
            state: {
              url: 'https://example.com',
              title: '示例首页',
              tabs: [{ url: 'https://example.com', title: '示例首页', target_id: '1', parent_target_id: null }],
              screenshot_path: 'D:/mock/screenshots/step2.png'
            },
            metadata: { step_number: 2, step_start_time: 1700000005, step_end_time: 1700000010, step_interval: 5 },
            state_message: ''
          }
        ]
      })
    }

    // UI automation: report summary (detail route with /summary/)
    if (pathname.match(/\/api\/v1\/ui-automation\/reports\/\d+\/summary\//)) {
      return jsonResponse(route, {
        id: 701,
        execution_id: 601,
        project_id: 1,
        project_name: 'UI 项目 A',
        test_case_name: '首页烟雾测试',
        browser_mode: 'headed',
        status: 'passed',
        started_at: '2026-02-12T08:00:00Z',
        completed_at: '2026-02-12T08:00:12Z',
        duration_seconds: 12,
        json_report_path: 'D:/mock/report/test-report.json',
        summary: '测试成功',
        final_result: '标题验证通过',
        error_message: '',
        metrics: {
          total_steps: 2,
          failed_steps: 0,
          success_steps: 2,
          screenshot_count: 2
        }
      })
    }

    // UI automation: execution detail
    if (pathname.match(/\/api\/v1\/ui-automation\/executions\/\d+\/$/)) {
      return jsonResponse(route, {
        id: 601,
        test_case: 501,
        test_case_name: '首页烟雾测试',
        project: 1,
        project_name: 'UI 项目 A',
        status: 'passed',
        browser_mode: 'headed',
        duration_seconds: 12,
        started_at: '2026-02-12T08:00:00Z',
        completed_at: '2026-02-12T08:00:12Z',
        error_message: null,
        agent_history: '',
        report: { id: 701 },
        created_at: '2026-02-12T08:00:00Z'
      })
    }

    if (pathname.includes('/api/v1/ui-automation/executions/')) {
      return jsonResponse(route, paged([
        {
          id: 601,
          test_case_name: '首页烟雾测试',
          status: 'passed',
          duration_seconds: 12,
          created_at: '2026-02-12T08:00:00Z'
        }
      ]))
    }

    // UI automation: report detail
    if (pathname.match(/\/api\/v1\/ui-automation\/reports\/\d+\/$/)) {
      return jsonResponse(route, {
        id: 701,
        execution: 601,
        total_steps: 2,
        completed_steps: 2,
        failed_steps: 0,
        summary: '测试成功',
        json_report_path: 'D:/mock/report/test-report.json',
        created_at: '2026-02-12T08:00:00Z'
      })
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
