import { CheckCircle2, AlertTriangle, XCircle, ShieldAlert } from 'lucide-react'

interface ValidationTableProps {
  summary: Record<string, number>
}

const VALIDATION_ITEMS = [
  { key: 'passed', label: 'Passed', icon: CheckCircle2, color: 'text-accent-green', bg: 'bg-accent-green/10' },
  { key: 'warnings', label: 'Warnings', icon: AlertTriangle, color: 'text-warn-amber', bg: 'bg-warn-amber/10' },
  { key: 'failed', label: 'Failed', icon: XCircle, color: 'text-error-red', bg: 'bg-error-red/10' },
  { key: 'quarantined', label: 'Quarantined', icon: ShieldAlert, color: 'text-warn-amber', bg: 'bg-warn-amber/10' },
]

export default function ValidationTable({ summary }: ValidationTableProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {VALIDATION_ITEMS.map((item) => {
        const Icon = item.icon
        const count = summary[item.key] ?? 0
        return (
          <div
            key={item.key}
            className="bg-bg-secondary border border-white/5 rounded-lg p-4 text-center"
          >
            <div className={`w-10 h-10 rounded-lg ${item.bg} flex items-center justify-center mx-auto mb-2`}>
              <Icon className={`w-5 h-5 ${item.color}`} />
            </div>
            <p className="text-2xl font-mono font-semibold text-text-primary">{count}</p>
            <p className="text-xs font-body text-text-muted mt-1">{item.label}</p>
          </div>
        )
      })}
    </div>
  )
}
