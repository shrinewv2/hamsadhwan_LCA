import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Terminal as TerminalIcon, ChevronDown } from 'lucide-react'
import { getLogsSSEUrl, type LogEntry } from '../../api/client'

const MAX_DISPLAY_LOGS = 2000

interface LogStreamProps {
  jobId: string
}

const LOG_COLORS: Record<string, string> = {
  INFO: 'text-text-secondary',
  WARNING: 'text-warn-amber',
  ERROR: 'text-error-red',
  DEBUG: 'text-text-muted',
}

export default function LogStream({ jobId }: LogStreamProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [autoScroll, setAutoScroll] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const url = getLogsSSEUrl(jobId)
    const eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const log: LogEntry = JSON.parse(event.data)
        setLogs((prev) => {
          const newLogs = [...prev, log]
          return newLogs.length > MAX_DISPLAY_LOGS ? newLogs.slice(-MAX_DISPLAY_LOGS) : newLogs
        })
      } catch {
        // heartbeat or non-json
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => eventSource.close()
  }, [jobId])

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [logs, autoScroll])

  const handleScroll = () => {
    if (!containerRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 50)
  }

  return (
    <div className="bg-bg-secondary rounded-xl border border-white/5 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <TerminalIcon className="w-4 h-4 text-text-muted" />
          <span className="text-sm font-body text-text-secondary">Live Logs</span>
          <span className="text-xs font-mono text-text-muted bg-white/5 px-1.5 py-0.5 rounded">
            {logs.length}
          </span>
        </div>
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true)
              if (containerRef.current) {
                containerRef.current.scrollTop = containerRef.current.scrollHeight
              }
            }}
            className="flex items-center gap-1 text-xs text-accent-green hover:underline"
          >
            <ChevronDown className="w-3 h-3" />
            Scroll to bottom
          </button>
        )}
      </div>

      {/* Log entries */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-64 overflow-y-auto p-3 font-mono text-xs space-y-0.5 custom-scrollbar"
      >
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-text-muted">
            <div className="text-center">
              <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse-slow mx-auto mb-2" />
              Waiting for logs…
            </div>
          </div>
        ) : (
          logs.map((log, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-2 leading-relaxed"
            >
              <span className="text-text-muted flex-shrink-0 w-20">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className={`flex-shrink-0 w-6 ${LOG_COLORS[log.level] || 'text-text-muted'}`}>
                {log.level?.charAt(0) || '?'}
              </span>
              {log.agent && (
                <span className="text-accent-green/70 flex-shrink-0">
                  [{log.agent}]
                </span>
              )}
              <span className={LOG_COLORS[log.level] || 'text-text-secondary'}>
                {log.message}
              </span>
            </motion.div>
          ))
        )}
      </div>
    </div>
  )
}
