/**
 * UI自动化测试项目相关类型定义
 *
 * 包含项目模型、创建参数、关联用户信息和项目统计数据。
 */

/** 项目完整信息（对应后端 UiProject 模型） */
export interface UiProject {
  id: number
  name: string
  description: string | null
  /** 项目负责人 */
  owner: UiUser
  owner_id?: number
  /** 是否启用 */
  is_active: boolean
  created_at: string
  updated_at: string
  /** 关联的测试用例数量（后端聚合字段） */
  test_cases_count?: number
  /** 关联的执行记录数量（后端聚合字段） */
  executions_count?: number
}

/** 创建项目所需参数 */
export interface UiProjectCreate {
  name: string
  description?: string
  is_active?: boolean
}

/** 用户基本信息（嵌套在项目数据中） */
export interface UiUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

/** 项目统计数据（用于项目详情页的概览面板） */
export interface UiProjectStatistics {
  total_test_cases: number
  total_executions: number
  successful_executions: number
  failed_executions: number
  /** 执行成功率（0-100 百分比） */
  success_rate: number
}
