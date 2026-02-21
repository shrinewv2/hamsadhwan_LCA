import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, FileText, AlertCircle } from 'lucide-react'
import DropZone from '../components/upload/DropZone'
import FileCard from '../components/upload/FileCard'
import { createJob } from '../api/client'
import { useJobStore } from '../store/jobStore'

export default function UploadPage() {
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])
  const [userContext, setUserContext] = useState('')
  const { setActiveJob, setCreating, isCreating, setError, error } = useJobStore()

  const handleFilesAccepted = useCallback(
    (newFiles: File[]) => {
      setFiles((prev) => {
        const combined = [...prev, ...newFiles]
        // Dedupe by name+size
        const seen = new Set<string>()
        return combined.filter((f) => {
          const key = `${f.name}__${f.size}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
      })
    },
    []
  )

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const handleAnalyse = async () => {
    if (files.length === 0) return
    setCreating(true)
    setError(null)
    try {
      const result = await createJob(files, userContext || undefined)
      setActiveJob(result.job_id)
      navigate(`/processing/${result.job_id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create analysis job'
      setError(msg)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h2 className="font-heading text-3xl font-semibold text-text-primary">
          Upload LCA Documents
        </h2>
        <p className="text-text-muted font-body">
          Upload your Life Cycle Assessment files for multi-agent analysis. Supported formats
          include Excel, PDF, images, mind maps, and more.
        </p>
      </motion.div>

      {/* Drop zone */}
      <DropZone onFilesAccepted={handleFilesAccepted} disabled={isCreating} />

      {/* File list */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-body text-text-secondary flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {files.length} file{files.length > 1 ? 's' : ''} selected
            </h3>
            <button
              onClick={() => setFiles([])}
              className="text-xs text-text-muted hover:text-error-red transition-colors"
            >
              Clear all
            </button>
          </div>

          <div className="space-y-2">
            <AnimatePresence mode="popLayout">
              {files.map((file, idx) => (
                <FileCard
                  key={`${file.name}__${file.size}`}
                  file={file}
                  onRemove={() => removeFile(idx)}
                />
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}

      {/* Additional context */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="space-y-2"
      >
        <label className="text-sm font-body text-text-secondary" htmlFor="user-context">
          Additional Context{' '}
          <span className="text-text-muted">(optional)</span>
        </label>
        <textarea
          id="user-context"
          value={userContext}
          onChange={(e) => setUserContext(e.target.value)}
          placeholder="Describe what you'd like to learn from these documents, specific focus areas, or any relevant context…"
          rows={3}
          disabled={isCreating}
          className="w-full bg-bg-tertiary border border-white/10 rounded-lg px-4 py-3 text-sm font-body text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-green/50 focus:ring-1 focus:ring-accent-green/20 resize-none transition-all disabled:opacity-50"
        />
      </motion.div>

      {/* Error message */}
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

      {/* Analyse button */}
      <motion.button
        whileHover={files.length > 0 && !isCreating ? { scale: 1.01 } : {}}
        whileTap={files.length > 0 && !isCreating ? { scale: 0.99 } : {}}
        onClick={handleAnalyse}
        disabled={files.length === 0 || isCreating}
        className={`w-full flex items-center justify-center gap-3 py-4 rounded-xl font-body font-medium text-base transition-all ${
          files.length > 0 && !isCreating
            ? 'bg-accent-green text-bg-primary hover:bg-accent-green/90 shadow-lg shadow-accent-green/20'
            : 'bg-white/5 text-text-muted cursor-not-allowed'
        }`}
      >
        {isCreating ? (
          <>
            <div className="w-5 h-5 border-2 border-bg-primary/30 border-t-bg-primary rounded-full animate-spin" />
            Creating Analysis Job…
          </>
        ) : (
          <>
            <Play className="w-5 h-5" />
            Analyse Documents
          </>
        )}
      </motion.button>
    </div>
  )
}
