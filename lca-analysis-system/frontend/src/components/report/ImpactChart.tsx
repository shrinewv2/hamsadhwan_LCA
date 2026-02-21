import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface ImpactChartProps {
  data: {
    labels: string[]
    values: number[]
    units: string[]
  }
}

const CHART_COLORS = [
  '#4CAF7D',
  '#66BB9A',
  '#81C784',
  '#A5D6A7',
  '#C8E6C9',
  '#4DB6AC',
  '#80CBC4',
]

export default function ImpactChart({ data }: ImpactChartProps) {
  if (!data?.labels?.length) {
    return (
      <div className="flex items-center justify-center h-64 text-text-muted font-body text-sm">
        No impact data available
      </div>
    )
  }

  const chartData = data.labels.map((label, i) => ({
    name: label.length > 25 ? label.slice(0, 22) + '…' : label,
    fullName: label,
    value: data.values[i],
    unit: data.units[i],
  }))

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#A0A4B0', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis
            tick={{ fill: '#A0A4B0', fontSize: 10, fontFamily: 'IBM Plex Mono' }}
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
            formatter={(value: number, _name: string, props?: { payload?: { unit: string } }) => [
              `${value.toExponential(3)} ${props?.payload?.unit || ''}`,
              'Value',
            ]}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((_, idx) => (
              <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
