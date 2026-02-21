import { motion } from 'framer-motion'
import {
  FileSpreadsheet,
  FileText,
  Image,
  Brain,
  Presentation,
  File,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Clock,
} from 'lucide-react'
import ProgressRing from './ProgressRing'
import type { FileRecord } from '../../api/client'

const AGENT_ICONS: Record<string, React.ElementType> = {
  excel: FileSpreadsheet,
  csv: FileSpreadsheet,
  pdf_hybrid: FileText,
  pdf_text: FileText,
  pdf_scanned: FileText,
  image_vlm: Image,
  mindmap: Brain,
  generic: File,
  pptx: Presentation,
}

const STATUS_CONFIG: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  PENDING: { icon: Clock, color: 'text-text-muted', label: 'Pending' },
  PROCESSING: { icon: Loader2, color: 'text-accent-green', label: 'Processing' },
  COMPLETED: { icon: CheckCircle2, color: 'text-accent-green', label: 'Completed' },
  FAILED: { icon: AlertTriangle, color: 'text-error-red', label: 'Failed' },
  QUARANTINED: { icon: AlertTriangle, color: 'text-warn-amber', label: 'Quarantined' },
}

interface AgentCardProps {
  file: FileRecord
}

export default function AgentCard({ file }: AgentCardProps) {
  const AgentIcon = AGENT_ICONS[file.agent] || File
  const statusConf = STATUS_CONFIG[file.status] || STATUS_CONFIG.PENDING
  const StatusIcon = statusConf.icon
  const isProcessing = file.status === 'PROCESSING'

  // Derive a faux progress for visual feedback
  const progress =
    file.status === 'COMPLETED'
      ? 100
      : file.status === 'PROCESSING'
      ? Math.min(90, (file.confidence || 0) * 100)
      : 0

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-bg-secondary rounded-lg border border-white/5 p-4 flex items-center gap-4 hover:border-white/10 transition-colors"
    >
      {/* Progress ring */}
      <ProgressRing progress={progress} size={44} strokeWidth={3} />

      {/* Agent icon */}
      <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
        <AgentIcon className="w-4 h-4 text-text-secondary" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary truncate font-body">{file.name}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs font-mono text-text-muted capitalize">
            {file.agent?.replace('_', ' ') || file.type}
          </span>
          {file.confidence > 0 && (
            <>
              <span className="text-xs text-text-muted">·</span>
              <span className="text-xs font-mono text-text-muted">
                {(file.confidence * 100).toFixed(0)}% conf
              </span>
            </>
          )}
        </div>
      </div>

      {/* Status badge */}
      <div className={`flex items-center gap-1.5 ${statusConf.color}`}>
        <StatusIcon className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
        <span className="text-xs font-mono">{statusConf.label}</span>
      </div>
    </motion.div>
  )
}
