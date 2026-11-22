
import { useEffect, useMemo, useState } from 'react'

import {
  Activity,
  AlertCircle,
  Download,
  FileText,
  RefreshCw,
} from 'lucide-react'

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { motorApi } from '../services/motorApi'
import type { Motor } from '../services/motorApi'

import { diagnosticHistoryApi } from '../services/diagnosticHistoryApi'
import type {
  DiagnosticSessionDetail,
  DiagnosticSessionSummary,
  DiagnosticWindow,
} from '../services/diagnosticHistoryApi'


function formatDate(value: string) {
  return new Date(value).toLocaleString()
}

function formatNumber(value: number | null) {
  return value === null ? '—' : value.toFixed(4)
}

function exportCSV(
  session: DiagnosticSessionDetail,
) {
  const columns = [
    'window_index',
    'time_start',
    'time_end',
    'state',
    'reason',
    'persistent_score',
    'instantaneous_score',
    'uncertainty_distance',
    'memory_size',
  ] as const

  const escapeCSV = (value: unknown) => {
    const text = String(value ?? '')

    // Prevent spreadsheet formula interpretation.
    const safe = /^[=+\-@\t\r]/.test(text)
      ? `'${text}`
      : text

    return `"${safe.replaceAll('"', '""')}"`
  }

  const rows = session.predictions.map((prediction) =>
    columns.map((key) => escapeCSV(prediction[key])).join(','),
  )

  const csv = [
    columns.join(','),
    ...rows,
  ].join('\r\n')

  const blob = new Blob([csv], {
    type: 'text/csv;charset=utf-8',
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `aura_session_${session.id}.csv`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export default function DiagnosticReports() {
  const [motors, setMotors] = useState<Motor[]>([])
  const [sessions, setSessions] =
    useState<DiagnosticSessionSummary[]>([])

  const [selectedMotor, setSelectedMotor] = useState('')
  const [selectedSession, setSelectedSession] =
    useState<DiagnosticSessionDetail | null>(null)

  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    Promise.all([
      motorApi.list(),
      diagnosticHistoryApi.list(undefined, controller.signal),
    ])
      .then(([motorRecords, history]) => {
        if (controller.signal.aborted) return

        setMotors(motorRecords)
        setSessions(history)
        setError('')
        setLoading(false)
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return

        setError(
          err instanceof Error
            ? err.message
            : 'Unable to load diagnostic history.',
        )
        setLoading(false)
      })

    return () => controller.abort()
  }, [refreshKey])

  const filteredSessions = useMemo(() => {
    if (!selectedMotor) return sessions

    return sessions.filter(
      (session) =>
        session.motor_id === Number(selectedMotor),
    )
  }, [sessions, selectedMotor])

  async function openSession(id: number) {
    setDetailLoading(true)
    setError('')

    try {
      const detail = await diagnosticHistoryApi.get(id)
      setSelectedSession(detail)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to retrieve diagnostic session.',
      )
    } finally {
      setDetailLoading(false)
    }
  }

  function refresh() {
    setLoading(true)
    setSelectedSession(null)
    setRefreshKey((value) => value + 1)
  }

  const selectedMotorName = (id: number) =>
    motors.find((motor) => motor.id === id)?.name ??
    `Motor #${id}`

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <FileText size={26} className="text-cyan-400" />
            <h2 className="text-2xl font-semibold">
              Diagnostic Reports
            </h2>
          </div>

          <p className="text-sm text-slate-400">
            Review stored AURA diagnostic sessions and
            historical evidence from PostgreSQL.
          </p>
        </div>

        <button
          type="button"
          onClick={refresh}
          className="flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-3 text-sm hover:bg-slate-800"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300"
        >
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold">
              Saved Diagnostic Sessions
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              {filteredSessions.length} sessions
            </p>
          </div>

          <select
            value={selectedMotor}
            onChange={(event) =>
              setSelectedMotor(event.target.value)
            }
            aria-label="Filter by motor"
            className="rounded-xl border border-slate-700 bg-[#0B1220] px-4 py-3 text-sm"
          >
            <option value="">All Motors</option>

            {motors.map((motor) => (
              <option key={motor.id} value={motor.id}>
                {motor.motor_code} — {motor.name}
              </option>
            ))}
          </select>
        </div>

        {loading ? (
          <p role="status" className="mt-6 text-sm text-slate-400">
            Loading diagnostic sessions...
          </p>
        ) : filteredSessions.length === 0 ? (
          <p className="mt-6 text-sm text-slate-400">
            No saved diagnostic sessions found.
          </p>
        ) : (
          <div className="mt-5 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-xs text-slate-400">
                <tr>
                  {[
                    'Session',
                    'Motor',
                    'Recording',
                    'Windows',
                    'Normal',
                    'Warning',
                    'Unknown',
                    'Date',
                  ].map((heading) => (
                    <th
                      key={heading}
                      className="px-3 py-3 font-medium"
                    >
                      {heading}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody>
                {filteredSessions.map((session) => (
                  <tr
                    key={session.id}
                    className="border-t border-slate-800 hover:bg-slate-800/20"
                  >
                    <td className="px-3 py-4">
                      <button
                        type="button"
                        onClick={() =>
                          void openSession(session.id)
                        }
                        className="font-semibold text-cyan-300 hover:underline"
                      >
                        #{session.id}
                      </button>
                    </td>

                    <td className="px-3 py-4">
                      {selectedMotorName(session.motor_id)}
                    </td>

                    <td className="px-3 py-4 text-slate-400">
                      {session.recording_name}
                    </td>

                    <td className="px-3 py-4">
                      {session.total_windows}
                    </td>

                    <td className="px-3 py-4 text-emerald-300">
                      {session.normal_count}
                    </td>

                    <td className="px-3 py-4 text-amber-300">
                      {session.warning_count}
                    </td>

                    <td className="px-3 py-4 text-slate-300">
                      {session.unknown_count}
                    </td>

                    <td className="px-3 py-4 text-slate-400">
                      {formatDate(session.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {detailLoading && (
        <p role="status" className="text-sm text-cyan-300">
          Loading session details...
        </p>
      )}

      {selectedSession && !detailLoading && (
        <>
          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold">
                  Session #{selectedSession.id}
                </h3>

                <p className="mt-2 text-sm text-slate-400">
                  {selectedMotorName(selectedSession.motor_id)}
                  {' · '}
                  {selectedSession.model_name}
                  {' · '}
                  {selectedSession.model_version}
                </p>
              </div>

              <button
                type="button"
                onClick={() => exportCSV(selectedSession)}
                className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
              >
                <Download size={17} />
                Export CSV
              </button>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              {([
                ['NORMAL', 'text-emerald-300'],
                ['WARNING', 'text-amber-300'],
                ['UNKNOWN', 'text-slate-300'],
              ] as const).map(([state, color]) => (
                <div
                  key={state}
                  className="rounded-xl border border-slate-800 bg-[#0B1220] p-4"
                >
                  <p className="text-xs text-slate-400">
                    {state}
                  </p>

                  <p className={`mt-3 text-2xl font-semibold ${color}`}>
                    {selectedSession.state_counts[state]}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="mb-5 flex items-center gap-2">
              <Activity size={20} className="text-cyan-400" />
              <h3 className="font-semibold">
                Persistent Residual History
              </h3>
            </div>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={selectedSession.predictions}>
                  <CartesianGrid
                    stroke="#253348"
                    strokeDasharray="3 3"
                  />
                  <XAxis dataKey="time_end" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
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
            <h3 className="mb-5 font-semibold">
              Operating-Condition Uncertainty History
            </h3>

            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={selectedSession.predictions}>
                  <CartesianGrid
                    stroke="#253348"
                    strokeDasharray="3 3"
                  />
                  <XAxis dataKey="time_end" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
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
                Window-Level Diagnostic Results
              </h3>
            </div>

            <div className="max-h-[420px] overflow-auto">
              <table className="w-full min-w-[750px] text-left text-sm">
                <thead className="sticky top-0 bg-[#172337] text-xs text-slate-400">
                  <tr>
                    {[
                      'Window',
                      'Time (s)',
                      'State',
                      'Persistence',
                      'Uncertainty',
                      'Reason',
                    ].map((heading) => (
                      <th
                        key={heading}
                        className="px-4 py-3 font-medium"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {selectedSession.predictions.map(
                    (window: DiagnosticWindow) => (
                      <tr
                        key={window.window_index}
                        className="border-t border-slate-800"
                      >
                        <td className="px-4 py-3">
                          {window.window_index}
                        </td>
                        <td className="px-4 py-3">
                          {window.time_end.toFixed(2)}
                        </td>
                        <td className="px-4 py-3">
                          {window.state}
                        </td>
                        <td className="px-4 py-3">
                          {formatNumber(window.persistent_score)}
                        </td>
                        <td className="px-4 py-3">
                          {formatNumber(window.uncertainty_distance)}
                        </td>
                        <td className="px-4 py-3 text-slate-400">
                          {window.reason ?? '—'}
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <p className="text-xs leading-6 text-amber-300">
            These are historical results from an experimental
            AURA model. They do not represent validated
            industrial safety assessments.
          </p>
        </>
      )}
    </div>
  )
}
