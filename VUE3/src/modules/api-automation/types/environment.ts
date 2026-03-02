/**
 * 测试环境（Environment）类型定义
 *
 * 测试环境封装了 API 请求的基础配置，包括 Base URL、全局请求头、全局变量等。
 * 每个项目可配置多个环境（如开发、测试、生产），便于在不同环境间切换执行。
 */

/** 测试环境完整信息 */
export interface ApiTestEnvironment {
  id: number
  name: string
  description: string
  /** 所属项目 ID */
  project: number
  project_name: string
  /** 环境的基础 URL（所有请求路径将拼接在此之后） */
  base_url: string
  /** 全局请求头（在该环境下的所有请求中自动添加） */
  global_headers: Record<string, any>
  /** 全局变量（可在请求中通过 ${变量名} 引用） */
  global_variables: Record<string, any>
  /** 是否为当前项目的默认环境 */
  is_default: boolean
  /** 是否启用 */
  is_active: boolean
  /** 是否已收藏 */
  is_favorite: boolean
  created_time: string
  updated_time: string
}

/** 创建/编辑环境时的请求参数 */
export interface EnvironmentCreate {
  name: string
  description?: string
  project: number | undefined
  base_url: string
  global_headers?: Record<string, any>
  global_variables?: Record<string, any>
  is_default?: boolean
  is_active?: boolean
  is_favorite?: boolean
}