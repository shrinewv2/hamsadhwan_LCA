import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts'

interface HotspotChartProps {
  data: {
    labels: string[]
    values: number[]
    cumulative_pct: number[]
  }
}

export default function HotspotChart({ data }: HotspotChartProps) {
  if (!data?.labels?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-text-muted font-body text-sm">
        No hotspot data available
      </div>
    )
  }

  const chartData = data.labels.map((label, i) => ({
    name: label.length > 20 ? label.slice(0, 17) + '…' : label,
    value: data.values[i],
    cumPct: data.cumulative_pct[i],
  }))

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#A0A4B0', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            yAxisId="left"
            tick={{ fill: '#A0A4B0', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            domain={[0, 100]}
            tick={{ fill: '#A0A4B0', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
            unit="%"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1A1D27',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontFamily: 'IBM Plex Mono',
              fontSize: 12,
            }}
            labelStyle={{ color: '#E8EAF0' }}
          />
          <Bar
            yAxisId="left"
            dataKey="value"
            fill="#F59E0B"
            radius={[4, 4, 0, 0]}
            opacity={0.8}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumPct"
            stroke="#4CAF7D"
            strokeWidth={2}
            dot={{ fill: '#4CAF7D', r: 3 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
