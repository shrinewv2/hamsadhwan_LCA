import { create } from 'zustand'
import { getJobReport, type AnalysisReport } from '../api/client'

interface ReportState {
  report: AnalysisReport | null
  isLoading: boolean
  error: string | null

  fetchReport: (jobId: string) => Promise<void>
  clearReport: () => void
}

export const useReportStore = create<ReportState>((set) => ({
  report: null,
  isLoading: false,
  error: null,

  fetchReport: async (jobId: string) => {
    set({ isLoading: true, error: null })
    try {
      const data = await getJobReport(jobId)
      set({ report: data, isLoading: false })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load report'
      set({ error: message, isLoading: false })
    }
  },

  clearReport: () => set({ report: null, isLoading: false, error: null }),
}))
