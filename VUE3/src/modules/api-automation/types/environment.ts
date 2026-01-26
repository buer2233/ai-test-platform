export interface ApiTestEnvironment {
  id: number
  name: string
  description: string
  project: number
  project_name: string
  base_url: string
  global_headers: Record<string, any>
  global_variables: Record<string, any>
  is_default: boolean
  is_active: boolean
  is_favorite: boolean
  created_time: string
  updated_time: string
}

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