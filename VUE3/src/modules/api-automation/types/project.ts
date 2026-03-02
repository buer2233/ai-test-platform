/**
 * 项目（Project）类型定义
 *
 * 项目是 API 自动化测试的顶层组织单元。
 * 每个项目包含集合、测试用例、环境等子资源。
 */

/** 项目基础信息 */
export interface ApiProject {
  id: number
  name: string
  description: string | null
  /** 项目拥有者 */
  owner: User
  owner_id?: number
  /** 项目是否启用 */
  is_active: boolean
  created_time: string
  updated_time: string
  /** 项目下的集合数量 */
  collections_count?: number
  /** 项目下的测试用例数量 */
  test_cases_count?: number
}

/** 创建/编辑项目时的请求参数 */
export interface ApiProjectCreate {
  name: string
  description?: string
  is_active?: boolean
}

/** 用户基础信息（用于认证和权限展示） */
export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

/** 项目成员（用于项目内的角色分配） */
export interface ProjectMember {
  id: number
  project: number
  user: User
  /** 成员角色：拥有者 / 管理员 / 开发者 / 查看者 */
  role: 'owner' | 'admin' | 'developer' | 'viewer'
  created_time: string
}