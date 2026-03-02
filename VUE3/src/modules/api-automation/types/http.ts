/**
 * HTTP 请求/响应相关类型定义
 *
 * 本文件定义了 HTTP 执行器的核心数据结构，包括：
 * - 请求配置（方法、URL、参数、请求体、变量等）
 * - 响应结构（状态码、响应头、响应体等）
 * - 断言和操作符常量
 * - 常用 HTTP 头和状态码参考
 * - 执行记录相关类型
 */

// ==================== 基础数据结构 ====================

/** 通用键值对（用于请求头、查询参数、表单数据等） */
export interface KeyValueItem {
  key: string
  value: string
  /** 是否启用（禁用的项在发送请求时会被过滤掉） */
  enabled?: boolean
}

/** 变量定义（用于请求中的动态值替换） */
export interface Variable {
  name: string
  value: string
  type: 'string' | 'number' | 'boolean' | 'json' | 'environment'
  enabled: boolean
  description?: string
}

/** 上传文件项 */
export interface FileItem {
  file: File
  name: string
  size: number
  type: string
  /** 表单字段名（对应 multipart 的 key） */
  formKey: string
  url?: string
}

// ==================== 请求配置 ====================

/** 请求体结构（根据 bodyType 使用不同字段） */
export interface RequestBody {
  json: string
  form: KeyValueItem[]
  raw: string
  files: FileItem[]
}

/** 请求高级设置 */
export interface RequestSettings {
  /** 超时时间（毫秒） */
  timeout: number
  /** 是否自动跟随重定向 */
  followRedirects: boolean
  /** 是否验证 SSL 证书 */
  verifySSL: boolean
}

/** HTTP 请求完整配置 */
export interface HttpRequest {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'
  /** 环境 Base URL */
  baseUrl: string
  /** 请求路径（拼接在 baseUrl 之后） */
  url: string
  /** 查询参数 */
  params: KeyValueItem[]
  /** 请求头 */
  headers: KeyValueItem[]
  /** 请求体类型 */
  bodyType: 'none' | 'json' | 'form' | 'raw' | 'file'
  body: RequestBody
  /** 自定义变量（在请求中通过 ${变量名} 引用） */
  variables: Variable[]
  settings: RequestSettings
  /** 断言配置（可选） */
  tests?: TestAssertion[]
}

// ==================== 响应结构 ====================

/** HTTP 响应结果 */
export interface HttpResponse {
  status: number
  headers: Record<string, string>
  body: any
  /** 响应时间（毫秒） */
  response_time: number
  /** 响应体大小（字节） */
  body_size: number
  error?: string
  cookies?: Record<string, string>
  /** 原始请求信息（用于结果展示） */
  request?: {
    method: string
    url: string
    headers?: KeyValueItem[]
    params?: KeyValueItem[]
    body?: any
  }
}

// ==================== 断言配置 ====================

/** 测试断言定义 */
export interface TestAssertion {
  name?: string
  assert_type: string
  target: string
  operator: string
  expected_value: any
  enabled?: boolean
}

// ==================== 断言与操作符常量 ====================

/** 断言类型枚举 */
export const ASSERTION_TYPES = {
  STATUS_CODE: 'status_code',
  RESPONSE_TIME: 'response_time',
  RESPONSE_BODY: 'response_body',
  RESPONSE_HEADERS: 'response_headers',
  JSON_VALUE: 'json_value',
  TEXT_CONTAINS: 'text_contains',
  JSON_SCHEMA: 'json_schema'
} as const

/** 比较操作符枚举 */
export const OPERATORS = {
  EQUALS: 'equals',
  NOT_EQUALS: 'not_equals',
  GREATER_THAN: 'greater_than',
  LESS_THAN: 'less_than',
  GREATER_EQUAL: 'greater_equal',
  LESS_EQUAL: 'less_equal',
  CONTAINS: 'contains',
  NOT_CONTAINS: 'not_contains',
  STARTS_WITH: 'starts_with',
  ENDS_WITH: 'ends_with',
  MATCHES: 'matches',
  EXISTS: 'exists',
  NOT_EXISTS: 'not_exists',
  IS_EMPTY: 'is_empty',
  IS_NOT_EMPTY: 'is_not_empty'
} as const

/** 操作符的中文显示标签 */
export const OPERATOR_LABELS = {
  [OPERATORS.EQUALS]: '等于',
  [OPERATORS.NOT_EQUALS]: '不等于',
  [OPERATORS.GREATER_THAN]: '大于',
  [OPERATORS.LESS_THAN]: '小于',
  [OPERATORS.GREATER_EQUAL]: '大于等于',
  [OPERATORS.LESS_EQUAL]: '小于等于',
  [OPERATORS.CONTAINS]: '包含',
  [OPERATORS.NOT_CONTAINS]: '不包含',
  [OPERATORS.STARTS_WITH]: '以...开始',
  [OPERATORS.ENDS_WITH]: '以...结束',
  [OPERATORS.MATCHES]: '匹配正则',
  [OPERATORS.EXISTS]: '存在',
  [OPERATORS.NOT_EXISTS]: '不存在',
  [OPERATORS.IS_EMPTY]: '为空',
  [OPERATORS.IS_NOT_EMPTY]: '不为空'
} as const

/** 断言类型的中文显示标签 */
export const ASSERTION_TYPE_LABELS = {
  [ASSERTION_TYPES.STATUS_CODE]: '状态码',
  [ASSERTION_TYPES.RESPONSE_TIME]: '响应时间',
  [ASSERTION_TYPES.RESPONSE_BODY]: '响应体',
  [ASSERTION_TYPES.RESPONSE_HEADERS]: '响应头',
  [ASSERTION_TYPES.JSON_VALUE]: 'JSON值',
  [ASSERTION_TYPES.TEXT_CONTAINS]: '文本包含',
  [ASSERTION_TYPES.JSON_SCHEMA]: 'JSON Schema'
} as const

// ==================== HTTP 常用参考数据 ====================

/** 常用 Content-Type 类型选项 */
export const COMMON_CONTENT_TYPES = [
  { value: 'application/json', label: 'JSON' },
  { value: 'application/x-www-form-urlencoded', label: '表单编码' },
  { value: 'multipart/form-data', label: '多部分表单' },
  { value: 'text/plain', label: '纯文本' },
  { value: 'text/html', label: 'HTML' },
  { value: 'text/xml', label: 'XML' },
  { value: 'application/xml', label: 'XML (application)' },
  { value: 'application/javascript', label: 'JavaScript' },
  { value: 'application/pdf', label: 'PDF' },
  { value: 'image/png', label: 'PNG图片' },
  { value: 'image/jpeg', label: 'JPEG图片' },
  { value: 'image/gif', label: 'GIF图片' }
] as const

/** 常用请求头预设（供下拉选择使用） */
export const COMMON_HEADERS = [
  { key: 'Accept', value: 'application/json' },
  { key: 'Accept', value: 'text/html' },
  { key: 'Accept', value: 'application/xml' },
  { key: 'Accept-Language', value: 'zh-CN,zh;q=0.9,en;q=0.8' },
  { key: 'Authorization', value: 'Bearer ${token}' },
  { key: 'Authorization', value: 'Basic ${base64}' },
  { key: 'Cache-Control', value: 'no-cache' },
  { key: 'Content-Type', value: 'application/json' },
  { key: 'Content-Type', value: 'application/x-www-form-urlencoded' },
  { key: 'Content-Type', value: 'multipart/form-data' },
  { key: 'User-Agent', value: 'API-Automation-Platform/1.0' },
  { key: 'X-Requested-With', value: 'XMLHttpRequest' }
] as const

/** HTTP 状态码分类及对应的 UI 颜色标识 */
export const STATUS_CODE_CATEGORIES = {
  '1xx': { label: '信息响应', color: 'info' },
  '2xx': { label: '成功', color: 'success' },
  '3xx': { label: '重定向', color: 'warning' },
  '4xx': { label: '客户端错误', color: 'danger' },
  '5xx': { label: '服务器错误', color: 'danger' }
} as const

/** 常用 HTTP 状态码参考 */
export const COMMON_STATUS_CODES = [
  { code: 200, name: 'OK' },
  { code: 201, name: 'Created' },
  { code: 204, name: 'No Content' },
  { code: 301, name: 'Moved Permanently' },
  { code: 302, name: 'Found' },
  { code: 400, name: 'Bad Request' },
  { code: 401, name: 'Unauthorized' },
  { code: 403, name: 'Forbidden' },
  { code: 404, name: 'Not Found' },
  { code: 405, name: 'Method Not Allowed' },
  { code: 408, name: 'Request Timeout' },
  { code: 409, name: 'Conflict' },
  { code: 422, name: 'Unprocessable Entity' },
  { code: 429, name: 'Too Many Requests' },
  { code: 500, name: 'Internal Server Error' },
  { code: 502, name: 'Bad Gateway' },
  { code: 503, name: 'Service Unavailable' },
  { code: 504, name: 'Gateway Timeout' }
] as const

// ==================== 执行记录相关类型 ====================

/** 执行结果状态 */
export type ExecutionStatus = 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'ERROR' | 'PENDING'

/** 执行来源（手动、定时、批量、API 调用、直接 HTTP） */
export type ExecutionSource = 'MANUAL' | 'SCHEDULED' | 'BATCH' | 'API' | 'DIRECT_HTTP'

/** 单个断言的执行结果 */
export interface AssertionResult {
  assertion_id: number
  assertion_type: string
  expected: any
  actual: any
  passed: boolean
  error_message?: string
}

/** 数据提取的执行结果 */
export interface ExtractionResult {
  path: string
  value: any
  type: string
}

/** HTTP 执行记录完整信息 */
export interface HttpExecutionRecord {
  id: number
  project: number
  project_name?: string
  test_case: number
  test_case_name?: string
  execution: number | null
  environment: number | null
  environment_name?: string
  execution_source: ExecutionSource
  execution_batch: string | null

  /** 请求信息 */
  request_method: string
  request_url: string
  request_base_url: string
  request_path: string
  request_headers: Record<string, string>
  request_params: Record<string, any>
  request_body: any
  request_size: number
  request_size_formatted?: string

  /** 时间信息 */
  request_time: string
  response_time: string
  duration: number
  duration_formatted?: string

  /** 响应信息 */
  response_status: number | null
  response_status_text: string
  response_headers: Record<string, string>
  response_body: any
  response_body_text: string | null
  response_size: number
  response_size_formatted?: string
  response_encoding: string

  /** 状态和错误信息 */
  status: ExecutionStatus
  error_type?: string
  error_message?: string
  stack_trace?: string

  /** 断言执行结果 */
  assertion_results: AssertionResult[]
  assertions_passed: number
  assertions_failed: number

  /** 数据提取结果 */
  extraction_results: Record<string, ExtractionResult>
  extracted_variables: Record<string, any>

  /** 其他元数据 */
  is_favorite: boolean
  retry_count: number
  metadata: Record<string, any>
  executed_by: number
  executed_by_name?: string
  created_time: string
  updated_time: string
}

/** 执行记录列表分页响应 */
export interface HttpExecutionRecordListResponse {
  count: number
  next: string | null
  previous: string | null
  results: HttpExecutionRecord[]
}

/** 执行记录汇总统计 */
export interface HttpExecutionRecordStatistics {
  total: number
  success: number
  failed: number
  timeout: number
  error: number
  favorite: number
}

/** 执行记录查询参数 */
export interface HttpExecutionRecordQuery {
  page?: number
  page_size?: number
  test_case?: number
  execution?: number
  project?: number
  environment?: number
  status?: ExecutionStatus
  execution_source?: ExecutionSource
  is_favorite?: boolean
  start_date?: string
  end_date?: string
  search?: string
  ordering?: string
}

/** 批量删除请求参数（支持按 ID 或筛选条件） */
export interface BatchDeleteRequest {
  ids?: number[]
  filters?: {
    status?: ExecutionStatus
    date_before?: string
    environment?: number
    project?: number
  }
}