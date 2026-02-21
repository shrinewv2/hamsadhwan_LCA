import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, AlertCircle } from 'lucide-react'
import PipelineView from '../components/processing/PipelineView'
import AgentCard from '../components/processing/AgentCard'
import LogStream from '../components/processing/LogStream'
import { useJobPolling } from '../hooks/useJobPolling'
import { useJobStore } from '../store/jobStore'

export default function ProcessingPage() {
  const { jobId } = useParams<{ jobId: string }>()
  useJobPolling(jobId)

  const { jobStatus, files, progress, error } = useJobStore()

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-accent-green animate-pulse-slow" />
          <h2 className="font-heading text-3xl font-semibold text-text-primary">
            Analysis in Progress
          </h2>
        </div>
        <p className="text-text-muted font-body">
          Job <span className="font-mono text-text-secondary">{jobId}</span> — Processing{' '}
          {files.length} file{files.length !== 1 ? 's' : ''}
        </p>
      </motion.div>

      {/* Error banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 bg-error-red/10 border border-error-red/20 rounded-lg px-4 py-3"
        >
          <AlertCircle className="w-4 h-4 text-error-red flex-shrink-0" />
          <p className="text-sm text-error-red font-body">{error}</p>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline */}
        <div className="lg:col-span-1">
          <PipelineView progress={progress} />
        </div>

        {/* File agent cards */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overall progress bar */}
          <div className="bg-bg-secondary rounded-xl border border-white/5 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-body text-text-secondary flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Overall Progress
              </span>
              <span className="text-sm font-mono text-accent-green">
                {Math.round(progress)}%
              </span>
            </div>
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className="h-full bg-accent-green rounded-full"
              />
            </div>
          </div>

          {/* Agent cards */}
          <div className="space-y-2">
            {files.map((file) => (
              <AgentCard key={file.file_id} file={file} />
            ))}
            {files.length === 0 && (
              <div className="text-center text-text-muted py-8 font-body">
                Waiting for file processing to begin…
              </div>
            )}
          </div>

          {/* Log stream */}
          {jobId && <LogStream jobId={jobId} />}
        </div>
      </div>
    </div>
  )
}
