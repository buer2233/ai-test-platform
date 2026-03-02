/**
 * 仪表盘 API
 *
 * 提供测试平台的概览数据、多维度报告（环境/项目/集合）、图表数据，
 * 以及从仪表盘直接触发执行或重试的便捷操作。
 */

import { http } from '../../../shared/utils/http'

/** API 路由前缀 */
const API_URL = '/v1/api-automation/dashboard'

// ==================== 类型定义 ====================

/** 平台核心统计数据 */
export interface DashboardStats {
  total_projects: number
  total_collections: number
  total_test_cases: number
  total_executions: number
}

/** 测试通过率和响应时间统计 */
export interface TestStats {
  total_cases: number
  passed_cases: number
  failed_cases: number
  skipped_cases: number
  error_cases: number
  pass_rate: number
  avg_response_time: number
}

/** 按环境维度的测试报告 */
export interface EnvironmentReport {
  environment_id: number
  environment_name: string
  project_id: number
  project_name: string
  base_url: string
  execution_id: number | null
  execution_name: string | null
  execution_status: string | null
  stats: {
    total: number
    passed: number
    failed: number
    skipped: number
    error: number
    pass_rate: number
  }
  avg_response_time: number
  last_execution_time: string | null
}

/** 按集合维度的测试报告 */
export interface CollectionReport {
  collection_id: number
  collection_name: string
  project_id: number
  project_name: string
  test_case_count: number
  execution_id: number | null
  execution_name: string | null
  execution_status: string | null
  stats: {
    total: number
    passed: number
    failed: number
    skipped: number
    error: number
    pass_rate: number
  }
  avg_response_time: number
  last_execution_time: string | null
}

/** 按项目维度的测试报告 */
export interface ProjectReport {
  project_id: number
  project_name: string
  owner_id: number | null
  owner_name: string | null
  stats: {
    total: number
    passed: number
    failed: number
    skipped: number
    error: number
    pass_rate: number
  }
  avg_response_time: number
  last_execution_time: string | null
}

/** 图表可视化数据 */
export interface ChartData {
  /** 通过率饼图数据 */
  pass_rate_pie: {
    passed: number
    failed: number
    skipped: number
    error: number
  }
  /** 响应时间趋势（按日期） */
  response_time_trend: Array<{
    date: string
    avg_time: number
  }>
  /** HTTP 方法分布统计 */
  method_distribution: {
    GET: number
    POST: number
    PUT: number
    PATCH: number
    DELETE: number
  }
  /** 执行次数趋势（按日期） */
  execution_trend: Array<{
    date: string
    count: number
  }>
}

/** 仪表盘概览数据（包含统计和最近结果） */
export interface DashboardOverview {
  overview: DashboardStats
  test_stats: TestStats
  recent_results: any[]
}

/** 仪表盘通用筛选参数 */
export interface DashboardFilterParams {
  project_id?: number
  collection_id?: number
  owner_id?: number
  module?: string
  start_date?: string
  end_date?: string
}

// ==================== API 接口 ====================

export const dashboardApi = {
  /** 获取仪表盘概览数据（支持筛选） */
  getOverview(params?: DashboardFilterParams) {
    return http.get<DashboardOverview>(`${API_URL}/`, params)
  },

  /** 获取环境维度报告（支持筛选） */
  getEnvironmentReports(params?: DashboardFilterParams) {
    return http.get<{ results: EnvironmentReport[], count: number }>(`${API_URL}/environment_reports/`, params)
  },

  /** 获取项目维度报告（支持筛选） */
  getProjectReports(params?: DashboardFilterParams) {
    return http.get<{ results: ProjectReport[], count: number }>(`${API_URL}/project_reports/`, params)
  },

  /** 获取集合维度报告（支持筛选） */
  getCollectionReports(params?: DashboardFilterParams) {
    return http.get<{ results: CollectionReport[], count: number }>(`${API_URL}/collection_reports/`, params)
  },

  /** 获取图表可视化数据 */
  getChartData() {
    return http.get<ChartData>(`${API_URL}/chart_data/`)
  },

  /** 执行指定环境的所有测试用例 */
  executeEnvironment(data: { environment_id: number }) {
    return http.post(`${API_URL}/execute_environment/`, data)
  },

  /** 执行指定集合的所有测试用例 */
  executeCollection(data: { collection_id: number; environment_id: number }) {
    return http.post(`${API_URL}/execute_collection/`, data)
  },

  /** 重试失败的测试用例（支持全部或选择性重试） */
  retryFailed(data: {
    scope: 'all' | 'selected'
    test_result_ids?: number[]
    environment_id: number
    execution_name?: string
  }) {
    return http.post(`${API_URL}/retry_failed/`, data)
  },

  /** 获取测试结果列表（支持多维度筛选和排序） */
  getTestResults(params?: {
    page?: number
    page_size?: number
    status?: string
    environment_id?: number
    collection_id?: number
    project_id?: number
    owner_id?: number
    module?: string
    start_date?: string
    end_date?: string
    sort_by?: string
  }) {
    return http.get<{
      results: any[]
      count: number
      page: number
      page_size: number
      total_pages: number
    }>(`${API_URL}/test_results/`, params)
  }
}
