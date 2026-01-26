/**
 * UI自动化测试执行类型定义
 */

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface UiTestExecution {
  id: number
  project: number
  project_name?: string
  test_case: number
  test_case_name?: string
  status: ExecutionStatus
  browser_mode: 'headless' | 'headed'
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  error_message: string | null
  agent_history: string
  report: number | null
  json_report_path?: string | null
  screenshots_count?: number
  created_at: string
  updated_at: string
}

export interface UiTestExecutionCreate {
  project: number
  test_case: number
  browser_mode?: 'headless' | 'headed'
}

export interface ExecutionProgress {
  execution_id: number
  message: string
  data: {
    status: ExecutionStatus
    step?: AgentStep
    screenshot?: string
    timestamp: string
  }
}

export interface AgentStep {
  action: string
  timestamp: string
  details?: Record<string, unknown>
}

export interface ExecutionSummary {
  total: number
  pending: number
  running: number
  completed: number
  failed: number
  cancelled: number
}
