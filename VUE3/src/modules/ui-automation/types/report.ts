/**
 * UI自动化测试报告类型定义
 */

// ============ browser-use JSON 报告类型 ============

/**
 * browser-use Agent 执行历史报告
 * 这是 run_aiTest.py 生成的 JSON 报告格式
 */
export interface BrowserUseReport {
  history: AgentHistoryStep[]
}

/**
 * Agent 执行步骤历史
 */
export interface AgentHistoryStep {
  model_output: ModelOutput
  result: ActionResult[]
  state: BrowserState
  metadata: StepMetadata
  state_message: string
}

/**
 * 模型输出（AI 决策）
 */
export interface ModelOutput {
  evaluation_previous_goal: string | null
  memory: string
  next_goal: string
  action: Action[]
  thinking?: string
}

/**
 * 执行操作类型
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

/**
 * 执行结果
 */
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

/**
 * 浏览器状态
 */
export interface BrowserState {
  tabs: TabInfo[]
  screenshot_path: string | null
  url: string
  title: string
  interacted_element?: (unknown | null)[]
}

/**
 * 标签页信息
 */
export interface TabInfo {
  url: string
  title: string
  target_id: string
  parent_target_id: string | null
}

/**
 * 步骤元数据
 */
export interface StepMetadata {
  step_start_time: number
  step_end_time: number
  step_number: number
  step_interval: number | null
}

// ============ 数据库报告记录类型 ============

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

export interface ReportStep {
  timestamp: string
  action: string
  state?: Record<string, unknown>
  screenshot?: string
}

export interface ReportScreenshot {
  description: string
  data: string
  timestamp: string
}

export interface ReportMetrics {
  total_steps: number
  total_screenshots: number
  duration: string
  status: 'passed' | 'failed'
}
