/**
 * 集合（Collection）类型定义
 *
 * 集合是测试用例的逻辑分组，隶属于某个项目。
 * 一个集合可以包含多个测试用例，用于组织和批量执行测试。
 */

import type { ApiTestCaseList } from './testCase'

/** 集合基础信息 */
export interface ApiCollection {
  id: number
  name: string
  description: string | null
  /** 所属项目 ID */
  project: number
  /** 所属项目名称（后端关联查询返回） */
  project_name?: string
  created_time: string
  updated_time: string
  /** 集合下的测试用例数量 */
  test_cases_count?: number
}

/** 创建集合时的请求参数 */
export interface ApiCollectionCreate {
  name: string
  description?: string
  project: number
}

/** 集合详情（包含关联的测试用例列表） */
export interface ApiCollectionDetail extends ApiCollection {
  test_cases: ApiTestCaseList[]
}