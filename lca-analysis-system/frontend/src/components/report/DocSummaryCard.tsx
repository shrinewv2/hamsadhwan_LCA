import { motion } from 'framer-motion'
import { FileText, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'

interface DocSummaryCardProps {
  name: string
  type: string
  status: string
  agent: string
  confidence: number
}

export default function DocSummaryCard({ name, type, status, agent, confidence }: DocSummaryCardProps) {
  const statusConf: Record<string, { icon: React.ElementType; color: string; bg: string }> = {
    COMPLETED: { icon: CheckCircle2, color: 'text-accent-green', bg: 'bg-accent-green/10' },
    FAILED: { icon: XCircle, color: 'text-error-red', bg: 'bg-error-red/10' },
    QUARANTINED: { icon: AlertTriangle, color: 'text-warn-amber', bg: 'bg-warn-amber/10' },
  }

  const conf = statusConf[status] || statusConf.COMPLETED
  const Icon = conf.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-bg-secondary border border-white/5 rounded-lg p-4 hover:border-white/10 transition-colors"
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-text-muted" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-body text-text-primary truncate">{name}</p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs font-mono text-text-muted uppercase">{type}</span>
            <span className="text-xs text-text-muted">·</span>
            <span className="text-xs font-mono text-text-muted capitalize">
              {agent?.replace('_', ' ')}
            </span>
            {confidence > 0 && (
              <>
                <span className="text-xs text-text-muted">·</span>
                <span className="text-xs font-mono text-text-muted">
                  {(confidence * 100).toFixed(0)}% confidence
                </span>
              </>
            )}
          </div>
        </div>
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md ${conf.bg}`}>
          <Icon className={`w-3.5 h-3.5 ${conf.color}`} />
          <span className={`text-xs font-mono ${conf.color}`}>{status}</span>
        </div>
      </div>
    </motion.div>
  )
}
