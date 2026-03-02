/**
 * 测试执行（Execution）类型定义
 *
 * 执行任务代表一次测试运行的生命周期。
 * 包含执行状态、进度统计、时间信息等。
 */

/** 执行任务的状态枚举 */
type ExecutionStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

/** 测试执行任务基础信息 */
export interface ApiTestExecution {
  id: number
  name: string
  description: string
  /** 所属项目 ID */
  project: number
  project_name: string
  /** 执行所使用的环境 ID（可为空） */
  environment: number | null
  environment_name: string | null
  /** 关联的测试用例 ID 列表 */
  test_cases: number[]
  /** 当前执行状态 */
  status: ExecutionStatus
  /** 测试用例总数 */
  total_count: number
  /** 通过数 */
  passed_count: number
  /** 失败数 */
  failed_count: number
  /** 跳过数 */
  skipped_count: number
  start_time: string | null
  end_time: string | null
  /** 执行总耗时（秒） */
  duration: number | null
  /** 创建者用户 ID */
  created_by: number
  created_by_name: string
  created_time: string
  updated_time: string
}

/** 创建执行任务时的请求参数 */
export interface ExecutionCreate {
  name: string
  description?: string
  project: number
  environment?: number
  test_cases: number[]
}

/** 执行任务详情（包含测试结果和报告） */
export interface ExecutionDetail extends ApiTestExecution {
  test_results: any[]
  report?: any
}