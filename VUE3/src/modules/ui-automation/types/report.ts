/**
 * UI自动化测试报告相关类型定义
 *
 * 本文件分为两大部分：
 * 1. browser-use JSON 报告类型 -- AI Agent 执行过程中产生的详细步骤数据
 * 2. 数据库报告记录类型 -- 后端持久化的报告摘要和统计信息
 */

// ===================================================================
// 第一部分：browser-use JSON 报告类型
// 由 run_aiTest.py 生成，完整记录每一步的 AI 决策和浏览器操作
// ===================================================================

/**
 * browser-use Agent 执行历史报告（顶层结构）
 * history 数组中每个元素对应 Agent 执行的一个步骤
 */
export interface BrowserUseReport {
  history: AgentHistoryStep[]
}

/** Agent 单步执行历史，包含模型输出、执行结果、浏览器状态和元数据 */
export interface AgentHistoryStep {
  model_output: ModelOutput
  result: ActionResult[]
  state: BrowserState
  metadata: StepMetadata
  state_message: string
}

/** AI 模型输出（包含上一步评估、记忆、下一步目标和执行操作列表） */
export interface ModelOutput {
  evaluation_previous_goal: string | null
  memory: string
  next_goal: string
  action: Action[]
  thinking?: string
}

/**
 * 执行操作联合类型
 *
 * 每种操作对应 browser_use 支持的一种浏览器交互行为。
 * 使用 `unknown` 兜底，确保向前兼容未知的新操作类型。
 */
export type Action =
  | NavigateAction
  | ClickAction
  | InputAction
  | SearchAction
  | ScrollAction
  | ExtractAction
  | DoneAction
  | WaitAction
  | GoBackAction
  | SwitchTabAction
  | CloseTabAction
  | unknown

export interface NavigateAction {
  navigate?: {
    url: string
    new_tab?: boolean
  }
}

export interface ClickAction {
  click?: {
    element: string
    index?: number
  }
}

export interface InputAction {
  input?: {
    index: number
    text: string
    clear?: boolean
  }
}

export interface SearchAction {
  search?: {
    query: string
    engine?: string
  }
}

export interface ScrollAction {
  scroll?: {
    direction?: 'up' | 'down'
    amount?: number
  }
}

export interface ExtractAction {
  extract?: string
}

export interface DoneAction {
  done?: {
    text: string
    success: boolean
  }
}

export interface WaitAction {
  wait?: {
    seconds?: number
  }
}

export interface GoBackAction {
  go_back?: boolean
}

export interface SwitchTabAction {
  switch_tab?: {
    index: number
  }
}

export interface CloseTabAction {
  close_tab?: {
    index: number
  }
}

/** 单步执行结果（包含完成状态、成功/失败标记、错误信息等） */
export interface ActionResult {
  is_done: boolean
  success?: boolean
  error?: string
  long_term_memory?: string
  extracted_content?: string
  include_extracted_content_only_once?: boolean
  include_in_memory?: boolean
  metadata?: {
    input_x?: number
    input_y?: number
    click_x?: number
    click_y?: number
  }
}

/** 浏览器当前状态（URL、标题、标签页列表和截图路径） */
export interface BrowserState {
  tabs: TabInfo[]
  screenshot_path: string | null
  url: string
  title: string
  interacted_element?: (unknown | null)[]
}

/** 浏览器标签页信息 */
export interface TabInfo {
  url: string
  title: string
  target_id: string
  parent_target_id: string | null
}

/** 步骤元数据（时间戳、步骤编号和执行间隔） */
export interface StepMetadata {
  step_start_time: number
  step_end_time: number
  step_number: number
  step_interval: number | null
}

// ===================================================================
// 第二部分：数据库报告记录类型
// 后端持久化的报告摘要，与 browser-use JSON 报告一一对应
// ===================================================================

/** 测试报告数据库记录（对应后端 UiTestReport 模型） */
export interface UiTestReport {
  id: number
  project: number
  project_name?: string
  execution: number
  execution_id?: number
  test_case_name?: string
  status: 'passed' | 'failed' | 'error' | 'pending' | 'running' | 'cancelled'
  duration_seconds: number | null
  started_at: string | null
  completed_at: string | null
  agent_history: unknown
  screenshot_paths?: unknown
  error_message?: string | null
  html_report_path?: string | null
  json_report_path?: string | null
  created_at: string
}

/** 报告汇总信息（包含执行概况和步骤统计指标） */
export interface UiTestReportSummary {
  id: number
  execution_id: number
  project_id: number
  project_name: string
  test_case_name: string
  browser_mode: 'headless' | 'headed'
  status: 'passed' | 'failed' | 'error' | 'pending' | 'running' | 'cancelled'
  started_at: string | null
  completed_at: string | null
  duration_seconds: number | null
  json_report_path: string | null
  summary: string
  final_result: string
  error_message: string
  metrics: {
    total_steps: number
    failed_steps: number
    success_steps: number
    screenshot_count: number
  }
}

/** 报告步骤简要信息（用于列表展示） */
export interface ReportStep {
  timestamp: string
  action: string
  state?: Record<string, unknown>
  screenshot?: string
}

/** 报告关联的截图信息 */
export interface ReportScreenshot {
  description: string
  data: string
  timestamp: string
}

/** 报告统计指标（用于概览卡片展示） */
export interface ReportMetrics {
  total_steps: number
  total_screenshots: number
  duration: string
  status: 'passed' | 'failed'
}
