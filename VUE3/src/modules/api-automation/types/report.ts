/**
 * 测试报告（Report）类型定义
 *
 * 报告是测试执行完成后生成的汇总文档，包含：
 * - 执行概览和统计（通过率、耗时等）
 * - 每个测试用例的详细执行结果
 * - 图表可视化数据
 * - 请求/响应的分级存储信息
 */

// ==================== 报告相关类型 ====================

/** 测试报告基础信息 */
export interface ApiTestReport {
  id: number
  /** 关联的执行任务 ID */
  execution: number
  name: string
  project_name: string
  execution_name: string
  /** 报告统计摘要 */
  summary: ReportSummary
  test_results: any[]
  /** 图表可视化数据 */
  charts_data: ChartsData
  created_time: string
  updated_time: string
}

/** 报告统计摘要 */
export interface ReportSummary {
  total: number
  passed: number
  failed: number
  skipped: number
  /** 通过率（0-100） */
  pass_rate: number
  /** 总执行耗时（秒） */
  duration: number
  start_time: string | null
  end_time: string | null
}

/** 报告图表数据结构 */
export interface ChartsData {
  /** 状态分布饼图 */
  status_pie: {
    labels: string[]
    data: number[]
  }
  /** 响应时间分布图 */
  response_time: {
    labels: string[]
    data: number[]
  }
}

/** 报告详情（包含完整的测试结果列表） */
export interface ReportDetail extends ApiTestReport {
  test_results: TestResult[]
}

// ==================== 测试结果相关类型 ====================

/** 单个测试用例的执行结果 */
export interface TestResult {
  id: number
  execution: number
  test_case: number
  test_case_name: string
  test_case_method: string
  test_case_url: string
  status: 'PASSED' | 'FAILED' | 'SKIPPED' | 'ERROR'
  response_status: number | null
  /** 响应时间（毫秒） */
  response_time: number
  error_message: string | null
  start_time: string
  end_time: string
  created_time: string
  updated_time: string

  /**
   * 以下为数据分级存储字段：
   * - 成功场景（HTTP 2xx）：仅存储摘要信息（request_summary / response_summary）
   * - 失败场景（HTTP 非 2xx）：存储完整信息（request_full / response_full）
   */
  request_summary?: RequestSummary
  response_summary?: ResponseSummary
  request_full?: RequestFull
  response_full?: ResponseFull
  error_info?: Record<string, any>
  assertion_results?: AssertionResult[]
  extracted_variables?: Record<string, any>
}

/** 请求摘要信息（成功场景下使用） */
export interface RequestSummary {
  method?: string
  url?: string
  headers?: Record<string, string>
  content_type?: string
}

/** 响应摘要信息（成功场景下使用） */
export interface ResponseSummary {
  status_code?: number
  response_time?: number
  content_length?: number
  content_type?: string
}

/** 完整请求信息（失败场景下使用，便于问题排查） */
export interface RequestFull {
  method?: string
  url?: string
  base_url?: string
  path?: string
  headers?: Record<string, string>
  params?: Record<string, any>
  body?: Record<string, any>
}

/** 完整响应信息（失败场景下使用，便于问题排查） */
export interface ResponseFull {
  status_code?: number
  status_text?: string
  response_time?: number
  headers?: Record<string, string>
  body?: Record<string, any>
  content_length?: number
}

/** 断言执行结果 */
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