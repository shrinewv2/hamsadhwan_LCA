import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJobStatus } from '../api/client'
import { useJobStore } from '../store/jobStore'

const POLL_INTERVAL = 3000

export function useJobPolling(jobId: string | undefined) {
  const navigate = useNavigate()
  const updateStatus = useJobStore((s) => s.updateStatus)
  const setError = useJobStore((s) => s.setError)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!jobId) return

    const poll = async () => {
      try {
        const status = await getJobStatus(jobId)
        updateStatus(status)

        if (status.status === 'COMPLETED') {
          if (intervalRef.current) clearInterval(intervalRef.current)
          navigate(`/report/${jobId}`)
        } else if (status.status === 'FAILED') {
          if (intervalRef.current) clearInterval(intervalRef.current)
          setError('Pipeline failed. Check logs for details.')
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Polling error'
        setError(msg)
      }
    }

    poll() // initial
    intervalRef.current = setInterval(poll, POLL_INTERVAL)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [jobId, navigate, updateStatus, setError])
}
