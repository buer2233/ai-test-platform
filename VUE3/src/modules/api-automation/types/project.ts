// 项目相关的类型定义

export interface ApiProject {
  id: number
  name: string
  description: string | null
  owner: User
  owner_id?: number
  is_active: boolean
  created_time: string
  updated_time: string
  collections_count?: number
  test_cases_count?: number
}

export interface ApiProjectCreate {
  name: string
  description?: string
  is_active?: boolean
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface ProjectMember {
  id: number
  project: number
  user: User
  role: 'owner' | 'admin' | 'developer' | 'viewer'
  created_time: string
}