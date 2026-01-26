export interface ApiTestReport {
  id: number
  execution: number
  name: string
  project_name: string
  execution_name: string
  summary: ReportSummary
  test_results: any[]
  charts_data: ChartsData
  created_time: string
  updated_time: string
}

export interface ReportSummary {
  total: number
  passed: number
  failed: number
  skipped: number
  pass_rate: number
  duration: number
  start_time: string | null
  end_time: string | null
}

export interface ChartsData {
  status_pie: {
    labels: string[]
    data: number[]
  }
  response_time: {
    labels: string[]
    data: number[]
  }
}

export interface ReportDetail extends ApiTestReport {
  test_results: TestResult[]
}

export interface TestResult {
  id: number
  execution: number
  test_case: number
  test_case_name: string
  test_case_method: string
  test_case_url: string
  status: 'PASSED' | 'FAILED' | 'SKIPPED' | 'ERROR'
  response_status: number | null
  response_time: number
  error_message: string | null
  start_time: string
  end_time: string
  created_time: string
  updated_time: string
  // 数据分级存储字段
  request_summary?: RequestSummary
  response_summary?: ResponseSummary
  request_full?: RequestFull
  response_full?: ResponseFull
  error_info?: Record<string, any>
  assertion_results?: AssertionResult[]
  extracted_variables?: Record<string, any>
}

// 请求摘要信息（HTTP 200情况）
export interface RequestSummary {
  method?: string
  url?: string
  headers?: Record<string, string>
  content_type?: string
}

// 响应摘要信息（HTTP 200情况）
export interface ResponseSummary {
  status_code?: number
  response_time?: number
  content_length?: number
  content_type?: string
}

// 完整请求信息（HTTP 非200情况）
export interface RequestFull {
  method?: string
  url?: string
  base_url?: string
  path?: string
  headers?: Record<string, string>
  params?: Record<string, any>
  body?: Record<string, any>
}

// 完整响应信息（HTTP 非200情况）
export interface ResponseFull {
  status_code?: number
  status_text?: string
  response_time?: number
  headers?: Record<string, string>
  body?: Record<string, any>
  content_length?: number
}

// 断言结果
export interface AssertionResult {
  id: number
  assertion_type: string
  target?: string
  operator: string
  expected_value?: string | number
  actual_value?: string | number
  passed: boolean
  error_message?: string
}