/**
 * 测试用例（TestCase）类型定义
 *
 * 测试用例定义了一次 API 请求的完整配置：
 * - HTTP 方法和 URL
 * - 请求头、查询参数、请求体
 * - 断言规则（验证响应是否符合预期）
 * - 数据提取规则（从响应中提取变量供后续使用）
 */

// ==================== 测试用例 ====================

/** 测试用例完整信息 */
export interface ApiTestCase {
  id: number
  name: string
  description: string | null
  /** 所属项目 ID */
  project: number
  project_name?: string
  /** 所属集合 ID（可为空，未分组的用例） */
  collection: number | null
  collection_name?: string
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  url: string
  headers: Record<string, any>
  params: Record<string, any>
  body: Record<string, any>
  /** 前端展示用的格式化数据（后端可选返回） */
  headers_display?: Record<string, any>
  params_display?: Record<string, any>
  body_display?: Record<string, any>
  created_by: number
  created_by_name?: string
  created_time: string
  updated_time: string
  /** 关联的断言配置列表 */
  assertions?: TestCaseAssertion[]
  /** 关联的数据提取配置列表 */
  extractions?: TestCaseExtraction[]
}

/** 创建测试用例时的请求参数 */
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

/** 测试用例列表项（精简字段，用于列表展示） */
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

// ==================== 断言与数据提取 ====================

/** 测试用例的断言配置 */
export interface TestCaseAssertion {
  id: number
  test_case: number
  /** 断言类型（如 status_code、json_value 等） */
  assertion_type: string
  /** 断言目标路径（如 JSON Path 表达式） */
  target: string | null
  /** 比较操作符（如 equals、contains 等） */
  operator: string
  /** 期望值 */
  expected_value: string | null
  is_enabled: boolean
  /** 排序序号（控制断言执行顺序） */
  order: number
}

/** 测试用例的数据提取配置 */
export interface TestCaseExtraction {
  id: number
  test_case: number
  /** 提取后的变量名（在后续用例中通过 ${变量名} 引用） */
  variable_name: string
  /** 提取方式（如 json_path、regex、header 等） */
  extract_type: string
  /** 提取表达式 */
  extract_expression: string
  /** 提取失败时使用的默认值 */
  default_value: string | null
  is_enabled: boolean
  /** 变量作用域（如 global、execution 等） */
  scope: string
}

// ==================== 测试执行结果 ====================

/** 单次测试用例执行的完整结果 */
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
  /** 每个断言的执行结果列表 */
  assertions: TestCaseAssertionResult[]
  /** 所有断言是否全部通过 */
  assertions_passed: boolean
  error_message: string | null
  start_time: string
  end_time: string
  /** 执行耗时（毫秒） */
  duration: number
}

/** 单个断言的执行结果 */
export interface TestCaseAssertionResult {
  type: string
  expected: any
  actual: any
  passed: boolean
  message: string
}

/** 执行测试用例时的请求参数 */
export interface RunTestRequest {
  environment_id: number
}