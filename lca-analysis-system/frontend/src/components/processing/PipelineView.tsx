import { motion } from 'framer-motion'
import {
  Upload,
  ScanSearch,
  Route,
  Cpu,
  CheckCircle2,
  Layers,
  FileOutput,
} from 'lucide-react'

const PHASES = [
  { id: 'ingestion', label: 'Ingestion', icon: Upload, desc: 'File detection & virus scan' },
  { id: 'routing', label: 'Routing', icon: Route, desc: 'Agent assignment' },
  { id: 'processing', label: 'Agent Processing', icon: Cpu, desc: 'Specialist extraction' },
  { id: 'normalization', label: 'Normalization', icon: Layers, desc: 'Markdown conversion' },
  { id: 'validation', label: 'Validation', icon: ScanSearch, desc: 'Rule & LLM checks' },
  { id: 'synthesis', label: 'Synthesis', icon: CheckCircle2, desc: 'Cross-document analysis' },
  { id: 'output', label: 'Output', icon: FileOutput, desc: 'Report generation' },
]

interface PipelineViewProps {
  progress: number // 0-100
  currentPhase?: string
}

function getPhaseIndex(progress: number): number {
  if (progress <= 0) return -1
  if (progress >= 100) return PHASES.length
  return Math.floor((progress / 100) * PHASES.length)
}

export default function PipelineView({ progress, currentPhase }: PipelineViewProps) {
  const activeIdx = currentPhase
    ? PHASES.findIndex((p) => p.id === currentPhase)
    : getPhaseIndex(progress)

  return (
    <div className="bg-bg-secondary rounded-xl border border-white/5 p-6">
      <h3 className="text-sm font-body text-text-secondary mb-6">Pipeline Progress</h3>
      <div className="space-y-1">
        {PHASES.map((phase, idx) => {
          const Icon = phase.icon
          const done = idx < activeIdx
          const active = idx === activeIdx
          const pending = idx > activeIdx

          return (
            <div key={phase.id} className="flex items-stretch gap-4">
              {/* Connector line + circle */}
              <div className="flex flex-col items-center w-8">
                <motion.div
                  initial={false}
                  animate={{
                    backgroundColor: done
                      ? '#4CAF7D'
                      : active
                      ? '#4CAF7D'
                      : 'rgba(255,255,255,0.1)',
                    scale: active ? 1.2 : 1,
                  }}
                  className={`w-3 h-3 rounded-full z-10 ${
                    active ? 'ring-4 ring-accent-green/20' : ''
                  }`}
                />
                {idx < PHASES.length - 1 && (
                  <div
                    className={`w-0.5 flex-1 min-h-[32px] ${
                      done ? 'bg-accent-green' : 'bg-white/10'
                    }`}
                  />
                )}
              </div>

              {/* Content */}
              <div
                className={`flex-1 pb-4 ${
                  pending ? 'opacity-40' : ''
                } transition-opacity`}
              >
                <div className="flex items-center gap-2">
                  <Icon
                    className={`w-4 h-4 ${
                      done
                        ? 'text-accent-green'
                        : active
                        ? 'text-accent-green'
                        : 'text-text-muted'
                    }`}
                  />
                  <span
                    className={`text-sm font-body ${
                      active ? 'text-text-primary font-medium' : 'text-text-secondary'
                    }`}
                  >
                    {phase.label}
                  </span>
                  {done && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-accent-green ml-auto" />
                  )}
                  {active && (
                    <div className="ml-auto w-2 h-2 rounded-full bg-accent-green animate-pulse-slow" />
                  )}
                </div>
                <p className="text-xs text-text-muted mt-0.5 ml-6">{phase.desc}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
