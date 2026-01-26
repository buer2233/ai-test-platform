/**
 * UI自动化测试项目类型定义
 */

export interface UiProject {
  id: number
  name: string
  description: string | null
  owner: UiUser
  owner_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
  test_cases_count?: number
  executions_count?: number
}

export interface UiProjectCreate {
  name: string
  description?: string
  is_active?: boolean
}

export interface UiUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface UiProjectStatistics {
  total_test_cases: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
}
