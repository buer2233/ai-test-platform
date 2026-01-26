// 测试用例相关的类型定义

export interface ApiTestCase {
  id: number
  name: string
  description: string | null
  project: number
  project_name?: string
  collection: number | null
  collection_name?: string
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  url: string
  headers: Record<string, any>
  params: Record<string, any>
  body: Record<string, any>
  headers_display?: Record<string, any>
  params_display?: Record<string, any>
  body_display?: Record<string, any>
  created_by: number
  created_by_name?: string
  created_time: string
  updated_time: string
  assertions?: TestCaseAssertion[]
  extractions?: TestCaseExtraction[]
}

export interface ApiTestCaseCreate {
  name: string
  description?: string
  project: number
  collection?: number | null
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  url: string
  headers?: Record<string, any>
  params?: Record<string, any>
  body?: Record<string, any>
}

export interface ApiTestCaseList {
  id: number
  name: string
  project: number
  project_name?: string
  collection: number | null
  collection_name?: string
  method: string
  url: string
  created_time: string
}

export interface TestCaseAssertion {
  id: number
  test_case: number
  assertion_type: string
  target: string | null
  operator: string
  expected_value: string | null
  is_enabled: boolean
  order: number
}

export interface TestCaseExtraction {
  id: number
  test_case: number
  variable_name: string
  extract_type: string
  extract_expression: string
  default_value: string | null
  is_enabled: boolean
  scope: string
}

// 测试执行相关类型
export interface TestCaseExecution {
  status: 'PASSED' | 'FAILED' | 'ERROR'
  test_case: {
    id: number
    name: string
    method: string
    url: string
  }
  environment: {
    id: number
    name: string
    base_url: string
  }
  request: {
    url: string
    method: string
    headers: Record<string, any>
    body: Record<string, any>
    params: Record<string, any>
  }
  response: {
    status_code: number
    headers: Record<string, any>
    body: any
    response_time: number
    size: number
  }
  assertions: TestCaseAssertionResult[]
  assertions_passed: boolean
  error_message: string | null
  start_time: string
  end_time: string
  duration: number
}

export interface TestCaseAssertionResult {
  type: string
  expected: any
  actual: any
  passed: boolean
  message: string
}

export interface RunTestRequest {
  environment_id: number
}