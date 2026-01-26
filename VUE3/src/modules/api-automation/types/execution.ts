export interface ApiTestExecution {
  id: number
  name: string
  description: string
  project: number
  project_name: string
  environment: number | null
  environment_name: string | null
  test_cases: number[]
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  total_count: number
  passed_count: number
  failed_count: number
  skipped_count: number
  start_time: string | null
  end_time: string | null
  duration: number | null
  created_by: number
  created_by_name: string
  created_time: string
  updated_time: string
}

export interface ExecutionCreate {
  name: string
  description?: string
  project: number
  environment?: number
  test_cases: number[]
}

export interface ExecutionDetail extends ApiTestExecution {
  test_results: any[]
  report?: any
}