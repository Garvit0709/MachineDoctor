
import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'

import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  CircleHelp,
  FileUp,
  LoaderCircle,
  ShieldCheck,
} from 'lucide-react'

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { diagnoseAURA } from '../services/auraApi'
import type {
  AURAResponse,
  AURAState,
} from '../services/auraApi'


const MAX_BYTES = 2 * 1024 * 1024

const STATE_STYLES: Record<AURAState, string> = {
  NORMAL: 'text-emerald-300 bg-emerald-400/10 border-emerald-400/20',
  WARNING: 'text-amber-300 bg-amber-400/10 border-amber-400/20',
  UNKNOWN: 'text-slate-300 bg-slate-400/10 border-slate-400/20',
}

function StatusBadge({ state }: { state: AURAState }) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${STATE_STYLES[state]}`}
    >
      {state}
    </span>
  )
}

export default function AURAIntelligence() {
  const [result, setResult] = useState<AURAResponse | null>(null)
  const [filename, setFilename] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => controllerRef.current?.abort()
  }, [])

  async function handleUpload(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]
    if (!file) return

    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setResult(null)
    setFilename('')
    setError('')
    setLoading(true)

    try {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        throw new Error('Please select a CSV file.')
      }

      if (file.size > MAX_BYTES) {
        throw new Error('Feature CSV exceeds the 2 MB limit.')
      }

      const response = await diagnoseAURA(file, controller.signal)

      if (controller.signal.aborted) return

      setResult(response)
      setFilename(file.name)
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to run AURA diagnosis.',
        )
      }
    } finally {
      if (controllerRef.current === controller) {
        setLoading(false)
        controllerRef.current = null
      }
      event.target.value = ''
    }
  }

  return (
    <div className="space-y-7">
      <div>
        <div className="mb-3 flex items-center gap-3">
          <BrainCircuit size={26} className="text-cyan-400" />
          <h2 className="text-2xl font-semibold">
            AURA Intelligence
          </h2>
        </div>

        <p className="text-sm leading-7 text-slate-400">
          Explore operating-condition uncertainty, persistent
          residual evidence and diagnostic states generated
          by the experimental AURA v0.1 model.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold">
              Run AURA Diagnosis
            </h3>
            <p className="mt-2 text-xs leading-5 text-slate-400">
              Upload precomputed feature windows containing
              run_id, time_start, time_end, rms, crest_factor,
              kurtosis, rpm and rpm_acceleration.
            </p>
          </div>

          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300">
            <FileUp size={18} />
            Select Feature CSV
            <input
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              onChange={handleUpload}
            />
          </label>
        </div>

        {loading && (
          <p role="status" className="mt-5 flex items-center gap-2 text-sm text-cyan-300">
            <LoaderCircle size={18} className="animate-spin" />
            Running AURA diagnostic inference...
          </p>
        )}

        {error && (
          <p role="alert" className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
            {error}
          </p>
        )}

        {result && (
          <p className="mt-5 flex items-center gap-2 text-sm text-emerald-300">
            <CheckCircle2 size={18} />
            Diagnosis completed for {filename}
          </p>
        )}
      </section>

      {result ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            {([
              ['NORMAL', ShieldCheck],
              ['WARNING', AlertTriangle],
              ['UNKNOWN', CircleHelp],
            ] as const).map(([state, Icon]) => (
              <div
                key={state}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">{state}</p>
                  <Icon size={20} className="text-cyan-400" />
                </div>
                <p className="mt-4 text-3xl font-semibold">
                  {result.state_counts[state]}
                </p>
                <p className="mt-2 text-xs text-slate-500">
                  Diagnostic windows
                </p>
              </div>
            ))}
          </div>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <h3 className="mb-2 font-semibold">
              Persistent Residual Evidence
            </h3>
            <p className="mb-5 text-xs text-slate-500">
              Score compared with the calibrated persistence threshold.
            </p>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.predictions}>
                  <CartesianGrid stroke="#253348" strokeDasharray="3 3" />
                  <XAxis dataKey="time_end" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
                  <ReferenceLine
                    y={result.thresholds.persistence}
                    stroke="#F59E0B"
                    strokeDasharray="5 5"
                    label="Threshold"
                  />
                  <Line
                    type="monotone"
                    dataKey="persistent_score"
                    stroke="#22D3EE"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <h3 className="mb-2 font-semibold">
              Operating-Condition Uncertainty
            </h3>
            <p className="mb-5 text-xs text-slate-500">
              Unfamiliarity distance compared with the uncertainty threshold.
            </p>

            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.predictions}>
                  <CartesianGrid stroke="#253348" strokeDasharray="3 3" />
                  <XAxis dataKey="time_end" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
                  <ReferenceLine
                    y={result.thresholds.uncertainty}
                    stroke="#F59E0B"
                    strokeDasharray="5 5"
                    label="Threshold"
                  />
                  <Line
                    type="monotone"
                    dataKey="uncertainty_distance"
                    stroke="#A78BFA"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
            <div className="border-b border-slate-800 p-6">
              <h3 className="font-semibold">
                Diagnostic Timeline
              </h3>
              <p className="mt-2 text-xs text-slate-500">
                Individual window decisions and supporting explanations.
              </p>
            </div>

            <div className="max-h-[440px] overflow-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="sticky top-0 bg-[#172337] text-xs text-slate-400">
                  <tr>
                    {['Time (s)', 'State', 'Persistence', 'Uncertainty', 'Reason'].map((heading) => (
                      <th key={heading} className="px-5 py-4 font-medium">
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.predictions.map((prediction, index) => (
                    <tr key={index} className="border-t border-slate-800">
                      <td className="px-5 py-4">
                        {prediction.time_end.toFixed(2)}
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge state={prediction.state} />
                      </td>
                      <td className="px-5 py-4">
                        {prediction.persistent_score.toFixed(3)}
                      </td>
                      <td className="px-5 py-4">
                        {prediction.uncertainty_distance.toFixed(3)}
                      </td>
                      <td className="px-5 py-4 text-slate-400">
                        {prediction.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <h3 className="font-semibold">Model Information</h3>
            <div className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <p>Model: <span className="text-cyan-300">{result.model_name}</span></p>
              <p>Version: {result.model_version}</p>
              <p>Recording: {result.run_id}</p>
              <p>Total windows: {result.total_windows}</p>
              <p>Data scope: {result.data_scope}</p>
            </div>
            <p className="mt-5 text-sm leading-6 text-amber-300">
              {result.limitations}
            </p>
          </section>
        </>
      ) : (
        !loading && (
          <div className="rounded-2xl border border-dashed border-slate-700 p-12 text-center">
            <BrainCircuit size={38} className="mx-auto mb-4 text-slate-500" />
            <h3 className="font-semibold">No AURA diagnosis loaded</h3>
            <p className="mt-2 text-sm text-slate-400">
              Upload a compatible feature-window CSV to view
              diagnostic decisions and supporting evidence.
            </p>
          </div>
        )
      )}
    </div>
  )
}
