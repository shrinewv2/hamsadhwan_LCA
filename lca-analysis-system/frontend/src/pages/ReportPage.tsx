import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  BarChart3,
  FileText,
  Flame,
  Shield,
  BookOpen,
  Download,
  ArrowLeft,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import ImpactChart from '../components/report/ImpactChart'
import HotspotChart from '../components/report/HotspotChart'
import CompletenessGauge from '../components/report/CompletenessGauge'
import MarkdownViewer from '../components/report/MarkdownViewer'
import DocSummaryCard from '../components/report/DocSummaryCard'
import ValidationTable from '../components/report/ValidationTable'
import { useReportStore } from '../store/reportStore'
import { useJobStore } from '../store/jobStore'
import { getDownloadUrl } from '../api/client'

type TabId = 'overview' | 'impact' | 'documents' | 'validation' | 'report'

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'impact', label: 'Impact Analysis', icon: Flame },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'validation', label: 'Validation', icon: Shield },
  { id: 'report', label: 'Full Report', icon: BookOpen },
]

export default function ReportPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const { report, isLoading, error, fetchReport } = useReportStore()
  const files = useJobStore((s) => s.files)

  useEffect(() => {
    if (jobId) fetchReport(jobId)
  }, [jobId, fetchReport])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-accent-green animate-spin" />
          <p className="text-text-muted font-body">Loading analysis report…</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4 text-center">
          <AlertCircle className="w-8 h-8 text-error-red" />
          <p className="text-error-red font-body">{error}</p>
          <Link to="/" className="text-accent-green hover:underline text-sm">
            ← Start new analysis
          </Link>
        </div>
      </div>
    )
  }

  if (!report) return null

  const json = report.structured_json
  const viz = report.viz_data

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between"
      >
        <div className="space-y-2">
          <Link
            to="/"
            className="text-text-muted hover:text-text-secondary text-sm flex items-center gap-1 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            New Analysis
          </Link>
          <h2 className="font-heading text-3xl font-semibold text-text-primary">
            Analysis Report
          </h2>
          <p className="text-text-muted font-body">
            Job <span className="font-mono text-text-secondary">{jobId}</span>
            {json?.analysis_date && (
              <> · {new Date(json.analysis_date).toLocaleDateString()}</>
            )}
            {json?.files_processed != null && (
              <> · {json.files_processed} files processed</>
            )}
          </p>
        </div>

        {/* Download buttons */}
        <div className="flex items-center gap-2">
          {(['report', 'json', 'audit'] as const).map((type) => (
            <a
              key={type}
              href={getDownloadUrl(jobId!, type)}
              download
              className="flex items-center gap-1.5 px-3 py-2 bg-bg-secondary border border-white/10 rounded-lg text-xs font-mono text-text-secondary hover:border-accent-green/30 hover:text-accent-green transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </a>
          ))}
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-bg-secondary rounded-lg p-1 border border-white/5 overflow-x-auto">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const active = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-md text-sm font-body transition-all whitespace-nowrap ${
                active
                  ? 'bg-accent-green/10 text-accent-green'
                  : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Key metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Completeness */}
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6 flex flex-col items-center">
                <h4 className="text-sm font-body text-text-muted mb-4">Study Completeness</h4>
                <CompletenessGauge
                  value={(json?.completeness ?? 0) * 100}
                  label={viz?.completeness_gauge?.label}
                />
              </div>

              {/* Functional Unit */}
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h4 className="text-sm font-body text-text-muted mb-3">Functional Unit</h4>
                <p className="text-text-primary font-body text-lg">
                  {json?.functional_unit || 'Not specified'}
                </p>
                <h4 className="text-sm font-body text-text-muted mt-4 mb-2">System Boundary</h4>
                <p className="text-text-secondary font-body text-sm">
                  {json?.system_boundary || 'Not specified'}
                </p>
              </div>

              {/* Data Quality */}
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h4 className="text-sm font-body text-text-muted mb-3">Data Quality</h4>
                <p className="text-text-primary font-body">{json?.data_quality || 'N/A'}</p>
                <h4 className="text-sm font-body text-text-muted mt-4 mb-2">Impact Method</h4>
                <p className="text-text-secondary font-body text-sm">
                  {json?.impact_method || 'Not specified'}
                </p>
              </div>
            </div>

            {/* Validation Summary */}
            {json?.validation_summary && (
              <div>
                <h3 className="text-sm font-body text-text-secondary mb-4">Validation Results</h3>
                <ValidationTable summary={json.validation_summary} />
              </div>
            )}

            {/* Impact chart preview */}
            {viz?.impact_bar_chart && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h3 className="text-sm font-body text-text-secondary mb-4">
                  Environmental Impact Categories
                </h3>
                <ImpactChart data={viz.impact_bar_chart} />
              </div>
            )}

            {/* Recommendations */}
            {json?.recommendations?.length > 0 && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h3 className="text-sm font-body text-text-secondary mb-4">Recommendations</h3>
                <ul className="space-y-2">
                  {json.recommendations.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start gap-2 text-sm font-body text-text-secondary">
                      <span className="w-5 h-5 rounded bg-accent-green/10 text-accent-green text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                        {i + 1}
                      </span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'impact' && (
          <div className="space-y-6">
            {viz?.impact_bar_chart && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h3 className="text-sm font-body text-text-secondary mb-4">
                  Impact Category Results
                </h3>
                <ImpactChart data={viz.impact_bar_chart} />
              </div>
            )}
            {viz?.hotspot_pareto && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h3 className="text-sm font-body text-text-secondary mb-4">
                  Hotspot Pareto Analysis
                </h3>
                <HotspotChart data={viz.hotspot_pareto} />
              </div>
            )}
            {/* Stage coverage */}
            {viz?.stage_coverage_heatmap && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl p-6">
                <h3 className="text-sm font-body text-text-secondary mb-4">
                  Life Cycle Stage Coverage
                </h3>
                <div className="flex flex-wrap gap-2">
                  {viz.stage_coverage_heatmap.stages.map((stage: string, i: number) => (
                    <div
                      key={stage}
                      className={`px-3 py-2 rounded-lg text-xs font-mono ${
                        viz.stage_coverage_heatmap.covered[i]
                          ? 'bg-accent-green/10 text-accent-green border border-accent-green/20'
                          : 'bg-white/5 text-text-muted border border-white/5'
                      }`}
                    >
                      {stage}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="space-y-4">
            {files.length > 0 ? (
              files.map((file) => (
                <DocSummaryCard
                  key={file.file_id}
                  name={file.name}
                  type={file.type}
                  status={file.status}
                  agent={file.agent}
                  confidence={file.confidence}
                />
              ))
            ) : (
              <p className="text-text-muted font-body text-center py-8">
                No document details available
              </p>
            )}
          </div>
        )}

        {activeTab === 'validation' && (
          <div className="space-y-6">
            {report.validation_summary && (
              <ValidationTable summary={report.validation_summary} />
            )}
            {/* Impact results table */}
            {json?.impact_results?.length > 0 && (
              <div className="bg-bg-secondary border border-white/5 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-white/5">
                  <h3 className="text-sm font-body text-text-secondary">
                    Impact Results Detail
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="px-6 py-3 text-left font-mono text-text-muted text-xs">Category</th>
                        <th className="px-6 py-3 text-right font-mono text-text-muted text-xs">Value</th>
                        <th className="px-6 py-3 text-left font-mono text-text-muted text-xs">Unit</th>
                        <th className="px-6 py-3 text-left font-mono text-text-muted text-xs">Stage</th>
                      </tr>
                    </thead>
                    <tbody>
                      {json.impact_results.map(
                        (
                          row: { category: string; value: number; unit: string; stage: string | null },
                          i: number
                        ) => (
                          <tr key={i} className="border-b border-white/5 last:border-0">
                            <td className="px-6 py-2.5 font-body text-text-primary">{row.category}</td>
                            <td className="px-6 py-2.5 font-mono text-text-secondary text-right">
                              {row.value?.toExponential(3) ?? '—'}
                            </td>
                            <td className="px-6 py-2.5 font-mono text-text-muted">{row.unit}</td>
                            <td className="px-6 py-2.5 font-mono text-text-muted">{row.stage || '—'}</td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'report' && (
          <div className="bg-bg-secondary border border-white/5 rounded-xl p-8">
            <MarkdownViewer content={report.markdown_report || 'No report content available.'} />
          </div>
        )}
      </motion.div>
    </div>
  )
}
