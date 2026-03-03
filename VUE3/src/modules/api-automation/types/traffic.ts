export interface TrafficCapture {
  id: number
  project: number
  project_name?: string
  name: string
  description?: string | null
  capture_type: 'PROXY_UPLOAD' | 'PROXY_LIVE'
  file_path?: string | null
  file_format: string
  file_size?: number | null
  content_hash?: string | null
  status: 'UPLOADED' | 'PARSING' | 'PARSED' | 'FAILED'
  total_entries?: number
  filtered_entries?: number
  sessions_count?: number
  processing_config?: Record<string, any>
  error_info?: Record<string, any>
  created_time?: string
  updated_time?: string
}

export interface TrafficSession {
  id: number
  project: number
  capture: number
  session_key: string
  start_time: string
  end_time: string
  duration_ms: number
  entry_count: number
  status: 'READY' | 'FILTERED' | 'FAILED'
  tags?: string[]
  created_time?: string
}

export interface TrafficEntry {
  id: number
  session: number
  request_method: string
  request_url: string
  request_headers?: Record<string, any>
  request_params?: Record<string, any>
  request_body?: Record<string, any>
  response_status?: number | null
  response_headers?: Record<string, any>
  response_body?: Record<string, any>
  response_time_ms?: number
  is_valuable?: boolean
  filter_reason?: string
}

export interface TrafficVariableRule {
  id: number
  entry: number
  variable_name: string
  source_type: 'JSONPATH' | 'REGEX' | 'HEADER'
  expression: string
  target_scope: 'SCENARIO' | 'GLOBAL'
  created_time?: string
}

export interface GeneratedArtifact {
  id: number
  project: number
  source_type: 'TRAFFIC' | 'RAG'
  source_id: number
  artifact_type: 'TEST_CASE' | 'SCENARIO'
  name: string
  status: 'DRAFT' | 'READY' | 'COMMITTED' | 'FAILED'
  payload: Record<string, any>
  preview_diff?: Record<string, any>
  created_time?: string
  updated_time?: string
}
