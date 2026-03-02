/**
 * UI自动化测试用例相关类型定义
 *
 * 包含测试用例模型、创建参数、更新参数和 Agent 历史记录。
 * 测试用例的核心是 test_task 字段，即自然语言描述的测试任务，
 * 由 browser_use 的 AI Agent 解析并自动执行。
 */

/** 测试用例完整信息（对应后端 UiTestCase 模型） */
export interface UiTestCase {
  id: number
  /** 所属项目 ID */
  project: number
  project_name?: string
  name: string
  description: string | null
  /** 自然语言描述的测试任务（AI Agent 的执行指令） */
  test_task: string
  /** 用例标签（用于分类和筛选） */
  tags: string[]
  /** 浏览器运行模式 */
  browser_mode: 'headless' | 'headed'
  /** 执行超时时间（秒） */
  timeout: number
  /** 失败后重试次数 */
  retry_count: number
  /** 是否启用 */
  is_active: boolean
  created_at: string
  updated_at: string
  /** 关联的执行记录数量（后端聚合字段） */
  executions_count?: number
  /** 最近一次执行的状态 */
  last_execution_status?: string
  /** 最近一次执行的时间 */
  last_execution_time?: string
}

/** 创建测试用例所需参数 */
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

/** 更新测试用例所需参数（所有字段可选） */
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

/** Agent 执行历史单条记录 */
export interface AgentHistory {
  timestamp: string
  action: string
  state?: Record<string, unknown>
}
