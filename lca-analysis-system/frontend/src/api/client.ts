import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const client = axios.create({
  baseURL: API_BASE_URL,
})

// Request interceptor — add Content-Type for non-multipart
client.interceptors.request.use((config) => {
  if (!config.headers['Content-Type'] && !(config.data instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
  }
  return config
})

// ─── Types ───

export interface FileRecord {
  file_id: string
  name: string
  type: string
  agent: string
  status: string
  confidence: number
}

export interface JobStatus {
  job_id: string
  status: string
  progress: number
  files: FileRecord[]
  errors: string[]
}

export interface JobCreateResponse {
  job_id: string
  file_count: number
  estimated_seconds: number
  status: string
}

export interface LogEntry {
  timestamp: string
  level: string
  agent: string
  file_id?: string
  message: string
}

export interface AnalysisReport {
  markdown_report: string
  structured_json: {
    job_id: string
    analysis_date: string
    functional_unit: string | null
    system_boundary: string | null
    impact_method: string | null
    impact_results: Array<{
      category: string
      value: number
      unit: string
      stage: string | null
    }>
    hotspots: Array<{
      process: string
      contribution_pct: number | null
      impact_category: string
    }>
    data_quality: string
    completeness: number
    files_processed: number
    validation_summary: {
      passed: number
      warnings: number
      failed: number
      quarantined: number
    }
    recommendations: string[]
  }
  viz_data: {
    impact_bar_chart: { labels: string[]; values: number[]; units: string[] }
    hotspot_pareto: { labels: string[]; values: number[]; cumulative_pct: number[] }
    completeness_gauge: { value: number; label: string }
    stage_coverage_heatmap: { stages: string[]; covered: boolean[] }
    data_quality_scores: { file_ids: string[]; scores: number[]; labels: string[] }
  }
  validation_summary: Record<string, number>
  audit_summary: Record<string, unknown>
}

// ─── API Functions ───

export async function createJob(files: File[], userContext?: string): Promise<JobCreateResponse> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  if (userContext) {
    formData.append('user_context', userContext)
  }

  const response = await client.post<JobCreateResponse>('/jobs', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await client.get<JobStatus>(`/jobs/${jobId}`)
  return response.data
}

export async function getJobReport(jobId: string): Promise<AnalysisReport> {
  const response = await client.get<AnalysisReport>(`/jobs/${jobId}/report`)
  return response.data
}

export function getLogsSSEUrl(jobId: string): string {
  return `${API_BASE_URL}/jobs/${jobId}/logs`
}

export function getDownloadUrl(jobId: string, type: 'report' | 'json' | 'audit'): string {
  return `${API_BASE_URL}/jobs/${jobId}/download/${type}`
}

export async function forceIncludeQuarantined(jobId: string) {
  const response = await client.post(`/jobs/${jobId}/force-include-quarantined`)
  return response.data
}

export async function healthCheck() {
  const response = await client.get('/health')
  return response.data
}

export default client
