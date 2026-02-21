import { create } from 'zustand'
import type { FileRecord, JobStatus, LogEntry } from '../api/client'

const MAX_LOG_ENTRIES = 2000

interface JobState {
  activeJobId: string | null
  jobStatus: JobStatus | null
  files: FileRecord[]
  progress: number
  logs: LogEntry[]
  isCreating: boolean
  error: string | null

  setActiveJob: (jobId: string) => void
  updateStatus: (status: JobStatus) => void
  appendLog: (log: LogEntry) => void
  setLogs: (logs: LogEntry[]) => void
  setCreating: (v: boolean) => void
  setError: (err: string | null) => void
  resetJob: () => void
}

export const useJobStore = create<JobState>((set) => ({
  activeJobId: null,
  jobStatus: null,
  files: [],
  progress: 0,
  logs: [],
  isCreating: false,
  error: null,

  setActiveJob: (jobId) => set({ activeJobId: jobId, error: null }),

  updateStatus: (status) =>
    set({
      jobStatus: status,
      files: status.files,
      progress: status.progress,
      error: status.errors?.length ? status.errors.join('; ') : null,
    }),

  appendLog: (log) =>
    set((state) => {
      const newLogs = [...state.logs, log]
      return { logs: newLogs.length > MAX_LOG_ENTRIES ? newLogs.slice(-MAX_LOG_ENTRIES) : newLogs }
    }),

  setLogs: (logs) => set({ logs }),

  setCreating: (v) => set({ isCreating: v }),

  setError: (err) => set({ error: err }),

  resetJob: () =>
    set({
      activeJobId: null,
      jobStatus: null,
      files: [],
      progress: 0,
      logs: [],
      isCreating: false,
      error: null,
    }),
}))
