/**
 * UI自动化测试执行相关类型定义
 *
 * 包含执行记录、执行创建参数、WebSocket 进度推送、
 * Agent 步骤信息以及执行状态汇总等类型。
 */

/** 执行状态枚举：待执行 | 执行中 | 通过 | 失败 | 错误 | 已取消 */
export type ExecutionStatus = 'pending' | 'running' | 'passed' | 'failed' | 'error' | 'cancelled'

/** 执行记录完整信息（对应后端 UiTestExecution 模型） */
export interface UiTestExecution {
  id: number
  /** 所属项目 ID */
  project: number
  project_name?: string
  /** 关联的测试用例 ID */
  test_case: number
  test_case_name?: string
  status: ExecutionStatus
  /** 浏览器运行模式：headless 无头模式 | headed 有头模式 */
  browser_mode: 'headless' | 'headed'
  started_at: string | null
  completed_at: string | null
  /** 执行耗时（秒） */
  duration_seconds: number | null
  error_message: string | null
  /** Agent 执行历史（JSON 字符串） */
  agent_history: string
  /** 关联的报告 ID */
  report: number | null
  /** JSON 格式报告的服务端文件路径 */
  json_report_path?: string | null
  screenshots_count?: number
  created_at: string
  updated_at: string
}

/** 创建执行记录所需参数 */
export interface UiTestExecutionCreate {
  project: number
  test_case: number
  browser_mode?: 'headless' | 'headed'
}

/** WebSocket 实时进度推送的数据结构 */
export interface ExecutionProgress {
  execution_id: number
  message: string
  data: {
    status: ExecutionStatus
    /** 当前执行步骤的详细信息 */
    step?: AgentStep
    /** Base64 编码的截图数据 */
    screenshot?: string
    timestamp: string
  }
}

/** AI Agent 单步执行信息 */
export interface AgentStep {
  action: string
  timestamp: string
  details?: Record<string, unknown>
}

/** 执行状态分布汇总（用于统计面板展示） */
export interface ExecutionSummary {
  total: number
  pending: number
  running: number
  passed: number
  failed: number
  error: number
  cancelled: number
}
