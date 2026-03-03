import { http } from '../../../shared/utils/http'
import type { GeneratedArtifact, TrafficCapture, TrafficSession, TrafficVariableRule } from '../types/traffic'

const API_URL = '/v1/api-automation'

export const trafficApi = {
  getCaptures(params?: any) {
    return http.get<{ results: TrafficCapture[], count: number }>(`${API_URL}/traffic-captures/`, params)
  },

  createCapture(data: FormData | Record<string, any>) {
    const config = data instanceof FormData
      ? { headers: { 'Content-Type': 'multipart/form-data' } }
      : undefined
    return http.post<TrafficCapture>(`${API_URL}/traffic-captures/`, data, config)
  },

  parseCapture(id: number) {
    return http.post<{
      capture_id: number
      sessions_count: number
      total_entries: number
      filtered_entries: number
      message?: string
    }>(`${API_URL}/traffic-captures/${id}/parse/`, {})
  },

  getSessions(params?: any) {
    return http.get<{ results: TrafficSession[], count: number }>(`${API_URL}/traffic-sessions/`, params)
  },

  generateArtifact(sessionId: number, name?: string) {
    return http.post<GeneratedArtifact>(`${API_URL}/traffic-sessions/${sessionId}/generate/`, { name })
  },

  getArtifacts(params?: any) {
    return http.get<{ results: GeneratedArtifact[], count: number }>(`${API_URL}/generated-artifacts/`, params)
  },

  previewArtifact(id: number) {
    return http.get<{ payload: Record<string, any> }>(`${API_URL}/generated-artifacts/${id}/preview/`)
  },

  updateArtifact(id: number, data: Partial<GeneratedArtifact>) {
    return http.patch<GeneratedArtifact>(`${API_URL}/generated-artifacts/${id}/`, data)
  },

  trialRunArtifact(id: number, passed: boolean, errorInfo?: string) {
    return http.post<GeneratedArtifact>(`${API_URL}/generated-artifacts/${id}/trial_run/`, {
      passed,
      error_info: errorInfo
    })
  },

  commitArtifact(id: number) {
    return http.post(`${API_URL}/generated-artifacts/${id}/commit/`, {})
  },

  getVariableRules(params?: any) {
    return http.get<{ results: TrafficVariableRule[], count: number }>(`${API_URL}/traffic-variable-rules/`, params)
  },

  updateVariableRule(id: number, data: Partial<TrafficVariableRule>) {
    return http.patch<TrafficVariableRule>(`${API_URL}/traffic-variable-rules/${id}/`, data)
  }
}
