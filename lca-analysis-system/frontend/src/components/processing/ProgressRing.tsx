interface ProgressRingProps {
  progress: number // 0-100
  size?: number
  strokeWidth?: number
}

export default function ProgressRing({
  progress,
  size = 40,
  strokeWidth = 3,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (progress / 100) * circumference

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      {/* Background circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={strokeWidth}
      />
      {/* Progress circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={progress >= 100 ? '#4CAF7D' : '#4CAF7D'}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-500"
      />
      {/* Percentage text */}
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="#E8EAF0"
        fontSize={size * 0.24}
        fontFamily="IBM Plex Mono, monospace"
        transform={`rotate(90, ${size / 2}, ${size / 2})`}
      >
        {Math.round(progress)}%
      </text>
    </svg>
  )
}
