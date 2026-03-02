/**
 * 数据驱动（DataDriver）类型定义
 *
 * 数据驱动配置用于参数化测试。
 * 支持 JSON、CSV、Excel、数据库等数据源，
 * 通过变量映射将数据源字段注入到测试用例的请求参数中。
 */

/** 数据驱动配置完整信息 */
export interface ApiDataDriver {
  id: number
  name: string
  description: string
  /** 所属项目 ID */
  project: number
  project_name: string
  /** 关联的测试用例 ID */
  test_case: number
  test_case_name: string
  /** 数据源类型 */
  data_type: 'JSON' | 'CSV' | 'EXCEL' | 'DATABASE'
  /** 数据源连接配置（如数据库连接串、文件路径等） */
  data_source: Record<string, any>
  /** 实际数据内容（数组形式，每项为一组参数） */
  data_content: any[]
  /** 变量映射：数据源字段名 -> 测试用例变量名 */
  variable_mapping: Record<string, string>
  is_active: boolean
  created_time: string
  updated_time: string
}

/** 创建数据驱动配置时的请求参数 */
export interface DataDriverCreate {
  name: string
  description?: string
  project: number
  test_case: number
  data_type: 'JSON' | 'CSV' | 'EXCEL' | 'DATABASE'
  data_source?: Record<string, any>
  data_content?: any[]
  variable_mapping?: Record<string, string>
  is_active?: boolean
}

/** 数据预览结果（用于配置验证） */
export interface DataDriverPreview {
  data_type: string
  data_content: any[]
  variable_mapping: Record<string, string>
  /** 示例数据（取前几条展示） */
  sample_data: any[]
}

/** 数据导入结果 */
export interface DataImportResult {
  success: boolean
  message: string
  data_count?: number
  sample_data?: any[]
}