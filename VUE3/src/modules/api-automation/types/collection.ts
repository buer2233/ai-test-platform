// 集合相关的类型定义
import type { ApiTestCaseList } from './testCase'

export interface ApiCollection {
  id: number
  name: string
  description: string | null
  project: number
  project_name?: string
  created_time: string
  updated_time: string
  test_cases_count?: number
}

export interface ApiCollectionCreate {
  name: string
  description?: string
  project: number
}

export interface ApiCollectionDetail extends ApiCollection {
  test_cases: ApiTestCaseList[]
}