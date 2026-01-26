import { http } from '../../../shared/utils/http'

const API_URL = '/v1/api-automation/dashboard'

// 仪表盘数据类型定义
export interface DashboardStats {
  total_projects: number
  total_collections: number
  total_test_cases: number
  total_executions: number
}

export interface TestStats {
  total_cases: number
  passed_cases: number
  failed_cases: number
  skipped_cases: number
  error_cases: number
  pass_rate: number
  avg_response_time: number
}

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

export interface ChartData {
  pass_rate_pie: {
    passed: number
    failed: number
    skipped: number
    error: number
  }
  response_time_trend: Array<{
    date: string
    avg_time: number
  }>
  method_distribution: {
    GET: number
    POST: number
    PUT: number
    PATCH: number
    DELETE: number
  }
  execution_trend: Array<{
    date: string
    count: number
  }>
}

export interface DashboardOverview {
  overview: DashboardStats
  test_stats: TestStats
  recent_results: any[]
}

// 通用筛选参数类型
export interface DashboardFilterParams {
  project_id?: number
  collection_id?: number
  owner_id?: number
  module?: string
  start_date?: string
  end_date?: string
}

export const dashboardApi = {
  // 获取仪表盘概览数据（支持筛选）
  getOverview(params?: DashboardFilterParams) {
    return http.get<DashboardOverview>(`${API_URL}/`, params)
  },

  // 获取环境维度报告（支持筛选）
  getEnvironmentReports(params?: DashboardFilterParams) {
    return http.get<{ results: EnvironmentReport[], count: number }>(`${API_URL}/environment_reports/`, params)
  },

  // 获取项目维度报告（支持筛选）
  getProjectReports(params?: DashboardFilterParams) {
    return http.get<{ results: ProjectReport[], count: number }>(`${API_URL}/project_reports/`, params)
  },

  // 获取集合维度报告（支持筛选）
  getCollectionReports(params?: DashboardFilterParams) {
    return http.get<{ results: CollectionReport[], count: number }>(`${API_URL}/collection_reports/`, params)
  },

  // 获取图表数据
  getChartData() {
    return http.get<ChartData>(`${API_URL}/chart_data/`)
  },

  // 执行环境所有用例
  executeEnvironment(data: { environment_id: number }) {
    return http.post(`${API_URL}/execute_environment/`, data)
  },

  // 执行集合所有用例
  executeCollection(data: { collection_id: number; environment_id: number }) {
    return http.post(`${API_URL}/execute_collection/`, data)
  },

  // 重试失败用例
  retryFailed(data: {
    scope: 'all' | 'selected'
    test_result_ids?: number[]
    environment_id: number
    execution_name?: string
  }) {
    return http.post(`${API_URL}/retry_failed/`, data)
  },

  // 获取测试结果列表（支持筛选）
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
