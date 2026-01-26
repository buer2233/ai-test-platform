// HTTP请求相关类型定义

export interface KeyValueItem {
  key: string
  value: string
  enabled?: boolean
}

export interface Variable {
  name: string
  value: string
  type: 'string' | 'number' | 'boolean' | 'json' | 'environment'
  enabled: boolean
  description?: string
}

export interface FileItem {
  file: File
  name: string
  size: number
  type: string
  formKey: string
  url?: string
}

export interface RequestBody {
  json: string
  form: KeyValueItem[]
  raw: string
  files: FileItem[]
}

export interface RequestSettings {
  timeout: number
  followRedirects: boolean
  verifySSL: boolean
}

export interface HttpRequest {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'
  baseUrl: string
  url: string
  params: KeyValueItem[]
  headers: KeyValueItem[]
  bodyType: 'none' | 'json' | 'form' | 'raw' | 'file'
  body: RequestBody
  variables: Variable[]
  settings: RequestSettings
  tests?: TestAssertion[]
}

export interface HttpResponse {
  status: number
  headers: Record<string, string>
  body: any
  response_time: number
  body_size: number
  error?: string
  cookies?: Record<string, string>
  request?: {
    method: string
    url: string
    headers?: KeyValueItem[]
    params?: KeyValueItem[]
    body?: any
  }
}

export interface TestAssertion {
  name?: string
  assert_type: string
  target: string
  operator: string
  expected_value: any
  enabled?: boolean
}

// 断言类型
export const ASSERTION_TYPES = {
  STATUS_CODE: 'status_code',
  RESPONSE_TIME: 'response_time',
  RESPONSE_BODY: 'response_body',
  RESPONSE_HEADERS: 'response_headers',
  JSON_VALUE: 'json_value',
  TEXT_CONTAINS: 'text_contains',
  JSON_SCHEMA: 'json_schema'
} as const

// 操作符类型
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

// 操作符显示名称
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

// 断言类型显示名称
export const ASSERTION_TYPE_LABELS = {
  [ASSERTION_TYPES.STATUS_CODE]: '状态码',
  [ASSERTION_TYPES.RESPONSE_TIME]: '响应时间',
  [ASSERTION_TYPES.RESPONSE_BODY]: '响应体',
  [ASSERTION_TYPES.RESPONSE_HEADERS]: '响应头',
  [ASSERTION_TYPES.JSON_VALUE]: 'JSON值',
  [ASSERTION_TYPES.TEXT_CONTAINS]: '文本包含',
  [ASSERTION_TYPES.JSON_SCHEMA]: 'JSON Schema'
} as const

// 常用Content-Type
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

// 常用请求头
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

// HTTP状态码分类
export const STATUS_CODE_CATEGORIES = {
  '1xx': { label: '信息响应', color: 'info' },
  '2xx': { label: '成功', color: 'success' },
  '3xx': { label: '重定向', color: 'warning' },
  '4xx': { label: '客户端错误', color: 'danger' },
  '5xx': { label: '服务器错误', color: 'danger' }
} as const

// 常用HTTP状态码
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

// HTTP执行记录相关类型定义
export type ExecutionStatus = 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'ERROR' | 'PENDING'
export type ExecutionSource = 'MANUAL' | 'SCHEDULED' | 'BATCH' | 'API' | 'DIRECT_HTTP'

export interface AssertionResult {
  assertion_id: number
  assertion_type: string
  expected: any
  actual: any
  passed: boolean
  error_message?: string
}

export interface ExtractionResult {
  path: string
  value: any
  type: string
}

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

  // 请求信息
  request_method: string
  request_url: string
  request_base_url: string
  request_path: string
  request_headers: Record<string, string>
  request_params: Record<string, any>
  request_body: any
  request_size: number
  request_size_formatted?: string

  // 时间信息
  request_time: string
  response_time: string
  duration: number
  duration_formatted?: string

  // 响应信息
  response_status: number | null
  response_status_text: string
  response_headers: Record<string, string>
  response_body: any
  response_body_text: string | null
  response_size: number
  response_size_formatted?: string
  response_encoding: string

  // 状态信息
  status: ExecutionStatus
  error_type?: string
  error_message?: string
  stack_trace?: string

  // 断言结果
  assertion_results: AssertionResult[]
  assertions_passed: number
  assertions_failed: number

  // 数据提取
  extraction_results: Record<string, ExtractionResult>
  extracted_variables: Record<string, any>

  // 其他
  is_favorite: boolean
  retry_count: number
  metadata: Record<string, any>
  executed_by: number
  executed_by_name?: string
  created_time: string
  updated_time: string
}

export interface HttpExecutionRecordListResponse {
  count: number
  next: string | null
  previous: string | null
  results: HttpExecutionRecord[]
}

export interface HttpExecutionRecordStatistics {
  total: number
  success: number
  failed: number
  timeout: number
  error: number
  favorite: number
}

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

export interface BatchDeleteRequest {
  ids?: number[]
  filters?: {
    status?: ExecutionStatus
    date_before?: string
    environment?: number
    project?: number
  }
}