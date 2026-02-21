import { motion } from 'framer-motion'

interface CompletenessGaugeProps {
  value: number // 0-100
  label?: string
}

export default function CompletenessGauge({ value, label }: CompletenessGaugeProps) {
  const clampedValue = Math.max(0, Math.min(100, value))
  const radius = 70
  const strokeWidth = 10
  const circumference = Math.PI * radius // half circle
  const offset = circumference - (clampedValue / 100) * circumference

  const getColor = (v: number) => {
    if (v >= 80) return '#4CAF7D'
    if (v >= 50) return '#F59E0B'
    return '#EF4444'
  }

  const color = getColor(clampedValue)

  return (
    <div className="flex flex-col items-center">
      <svg width="180" height="100" viewBox="0 0 180 100">
        {/* Background arc */}
        <path
          d="M 10 90 A 70 70 0 0 1 170 90"
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <motion.path
          d="M 10 90 A 70 70 0 0 1 170 90"
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
        {/* Center text */}
        <text
          x="90"
          y="78"
          textAnchor="middle"
          fill="#E8EAF0"
          fontSize="28"
          fontFamily="IBM Plex Mono, monospace"
          fontWeight="600"
        >
          {Math.round(clampedValue)}%
        </text>
      </svg>
      {label && (
        <p className="text-sm text-text-muted font-body mt-1">{label}</p>
      )}
    </div>
  )
}
