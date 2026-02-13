/**
 * UI自动化测试用例类型定义
 */

export interface UiTestCase {
  id: number
  project: number
  project_name?: string
  name: string
  description: string | null
  test_task: string
  tags: string[]
  browser_mode: 'headless' | 'headed'
  timeout: number
  retry_count: number
  is_active: boolean
  created_at: string
  updated_at: string
  executions_count?: number
  last_execution_status?: string
  last_execution_time?: string
}

export interface UiTestCaseCreate {
  project: number
  name: string
  description?: string
  test_task: string
  tags?: string[]
  browser_mode?: 'headless' | 'headed'
  timeout?: number
  retry_count?: number
  is_active?: boolean
}

export interface UiTestCaseUpdate {
  name?: string
  description?: string
  test_task?: string
  tags?: string[]
  browser_mode?: 'headless' | 'headed'
  timeout?: number
  retry_count?: number
  is_active?: boolean
}

export interface AgentHistory {
  timestamp: string
  action: string
  state?: Record<string, unknown>
}
