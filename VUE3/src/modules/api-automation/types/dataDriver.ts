export interface ApiDataDriver {
  id: number
  name: string
  description: string
  project: number
  project_name: string
  test_case: number
  test_case_name: string
  data_type: 'JSON' | 'CSV' | 'EXCEL' | 'DATABASE'
  data_source: Record<string, any>
  data_content: any[]
  variable_mapping: Record<string, string>
  is_active: boolean
  created_time: string
  updated_time: string
}

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

export interface DataDriverPreview {
  data_type: string
  data_content: any[]
  variable_mapping: Record<string, string>
  sample_data: any[]
}

export interface DataImportResult {
  success: boolean
  message: string
  data_count?: number
  sample_data?: any[]
}