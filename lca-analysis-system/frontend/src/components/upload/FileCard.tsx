import { motion } from 'framer-motion'
import {
  FileSpreadsheet,
  FileText,
  Image,
  File,
  Brain,
  Presentation,
  X,
} from 'lucide-react'

interface FileCardProps {
  file: File
  onRemove: () => void
}

const FORMAT_ICONS: Record<string, React.ElementType> = {
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  csv: FileSpreadsheet,
  pdf: FileText,
  docx: FileText,
  txt: FileText,
  png: Image,
  jpg: Image,
  jpeg: Image,
  tiff: Image,
  tif: Image,
  webp: Image,
  xmind: Brain,
  mm: Brain,
  pptx: Presentation,
}

const FORMAT_COLORS: Record<string, string> = {
  xlsx: 'text-green-400',
  xls: 'text-green-400',
  csv: 'text-green-400',
  pdf: 'text-red-400',
  docx: 'text-blue-400',
  txt: 'text-gray-400',
  png: 'text-purple-400',
  jpg: 'text-purple-400',
  jpeg: 'text-purple-400',
  tiff: 'text-purple-400',
  tif: 'text-purple-400',
  webp: 'text-purple-400',
  xmind: 'text-amber-400',
  mm: 'text-amber-400',
  pptx: 'text-orange-400',
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function getExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() || ''
}

export default function FileCard({ file, onRemove }: FileCardProps) {
  const ext = getExtension(file.name)
  const Icon = FORMAT_ICONS[ext] || File
  const colorClass = FORMAT_COLORS[ext] || 'text-text-muted'

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="flex items-center gap-3 bg-bg-tertiary rounded-lg px-4 py-3 group hover:bg-white/[0.06] transition-colors"
    >
      <div className={`w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center ${colorClass}`}>
        <Icon className="w-4.5 h-4.5" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary truncate font-body">{file.name}</p>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-muted uppercase">{ext}</span>
          <span className="text-xs text-text-muted">·</span>
          <span className="text-xs font-mono text-text-muted">{formatBytes(file.size)}</span>
        </div>
      </div>

      <button
        onClick={onRemove}
        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
        title="Remove file"
      >
        <X className="w-4 h-4 text-text-muted hover:text-error-red" />
      </button>
    </motion.div>
  )
}
