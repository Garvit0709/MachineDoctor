
import { useEffect, useMemo, useState } from 'react'

import {
  Activity,
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
} from 'lucide-react'

import { motorApi } from '../services/motorApi'
import type { Motor } from '../services/motorApi'

import { diagnosticHistoryApi } from '../services/diagnosticHistoryApi'
import type {
  DiagnosticSessionSummary,
} from '../services/diagnosticHistoryApi'

type Props = {
  onNavigate: (page: string) => void
}

function formatDate(value: string) {
  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? 'Unknown date'
    : date.toLocaleString()
}

export default function LiveOverview({ onNavigate }: Props) {
  const [motors, setMotors] = useState<Motor[]>([])
  const [sessions, setSessions] =
    useState<DiagnosticSessionSummary[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
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
            : 'Unable to load monitoring overview.',
        )

        setLoading(false)
      })

    return () => controller.abort()
  }, [refreshKey])

  const stats = useMemo(() => {
    const totalBearings = motors.reduce(
      (sum, motor) => sum + motor.bearings.length,
      0,
    )

    const motorsWithHistory = new Set(
      sessions.map((session) => session.motor_id),
    ).size

    const warningWindows = sessions.reduce(
      (sum, session) => sum + session.warning_count,
      0,
    )

    return {
      totalMotors: motors.length,
      totalBearings,
      totalSessions: sessions.length,
      motorsWithHistory,
      warningWindows,
    }
  }, [motors, sessions])

  const motorNames = useMemo(() => {
    return new Map(
      motors.map((motor) => [motor.id, motor.name]),
    )
  }, [motors])

  const filteredMotors = motors.filter((motor) =>
    [
      motor.motor_code,
      motor.name,
      motor.location ?? '',
      motor.motor_type ?? '',
    ]
      .join(' ')
      .toLowerCase()
      .includes(search.toLowerCase()),
  )

  const recentSessions = [...sessions]
    .sort((a, b) => {
      const dateDifference =
        new Date(b.created_at).getTime() -
        new Date(a.created_at).getTime()

      return dateDifference || b.id - a.id
    })
    .slice(0, 5)

  const cards = [
    {
      label: 'Registered Motors',
      value: stats.totalMotors,
      icon: Cpu,
    },
    {
      label: 'Installed Bearings',
      value: stats.totalBearings,
      icon: HardDrive,
    },
    {
      label: 'Diagnostic Sessions',
      value: stats.totalSessions,
      icon: Database,
    },
    {
      label: 'Motors With History',
      value: stats.motorsWithHistory,
      icon: BrainCircuit,
    },
  ]

  function refresh() {
    setLoading(true)
    setError('')
    setRefreshKey((value) => value + 1)
  }

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">
            Monitoring Overview
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            PostgreSQL equipment records and saved
            AURA diagnostic history.
          </p>
        </div>

        <button
          type="button"
          onClick={refresh}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-3 text-sm hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300"
        >
          <AlertCircle size={18} className="mr-2 inline" />
          {error}
        </div>
      )}

      {loading ? (
        <p role="status" className="text-sm text-slate-400">
          Loading equipment and diagnostic history...
        </p>
      ) : error ? (
        <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
          <p className="text-sm text-slate-400">
            Overview data is unavailable. Check the
            FastAPI and PostgreSQL connections.
          </p>
        </section>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">
                    {label}
                  </p>

                  <Icon size={20} className="text-cyan-400" />
                </div>

                <p className="mt-5 text-3xl font-semibold">
                  {value}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  Database-backed records
                </p>
              </div>
            ))}
          </div>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="mb-4 flex items-center gap-3">
              <Activity size={20} className="text-cyan-400" />
              <h3 className="font-semibold">
                Historical Diagnostic Evidence
              </h3>
            </div>

            <p className="text-sm leading-7 text-slate-400">
              AURA has recorded {stats.warningWindows} WARNING
              windows across {stats.totalSessions} saved
              diagnostic sessions. These counts are historical
              observations, not current motor health states.
            </p>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => onNavigate('Reports')}
                className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
              >
                View Diagnostic Reports
                <ArrowRight size={17} />
              </button>

              <button
                type="button"
                onClick={() => onNavigate('AURA Intelligence')}
                className="rounded-xl border border-slate-700 px-4 py-3 text-sm hover:bg-slate-800"
              >
                Open AURA Intelligence
              </button>
            </div>
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
            <div className="border-b border-slate-800 p-6">
              <h3 className="font-semibold">
                Recent Diagnostic Sessions
              </h3>

              <p className="mt-1 text-xs text-slate-500">
                Latest five saved analyses
              </p>
            </div>

            {recentSessions.length === 0 ? (
              <p className="p-6 text-sm text-slate-400">
                No diagnostic sessions have been saved yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[650px] text-left text-sm">
                  <thead className="bg-slate-800/30 text-xs text-slate-400">
                    <tr>
                      {[
                        'Session',
                        'Motor',
                        'Windows',
                        'Warnings',
                        'Date',
                      ].map((heading) => (
                        <th
                          key={heading}
                          className="px-5 py-4 font-medium"
                        >
                          {heading}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {recentSessions.map((session) => (
                      <tr
                        key={session.id}
                        className="border-t border-slate-800"
                      >
                        <td className="px-5 py-4 text-cyan-300">
                          #{session.id}
                        </td>

                        <td className="px-5 py-4">
                          {motorNames.get(session.motor_id) ??
                            `Motor #${session.motor_id}`}
                        </td>

                        <td className="px-5 py-4">
                          {session.total_windows}
                        </td>

                        <td className="px-5 py-4 text-amber-300">
                          {session.warning_count}
                        </td>

                        <td className="px-5 py-4 text-slate-400">
                          {formatDate(session.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 p-6">
              <div>
                <h3 className="font-semibold">
                  Equipment Registry
                </h3>

                <p className="mt-1 text-xs text-slate-500">
                  {motors.length} registered motors
                </p>
              </div>

              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search equipment..."
                aria-label="Search equipment"
                className="rounded-xl border border-slate-700 bg-[#0B1220] px-4 py-3 text-sm outline-none focus:border-cyan-400"
              />
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[650px] text-left text-sm">
                <thead className="bg-slate-800/30 text-xs text-slate-400">
                  <tr>
                    {[
                      'Motor Code',
                      'Equipment',
                      'Location',
                      'Bearings',
                      'Operating Status',
                    ].map((heading) => (
                      <th
                        key={heading}
                        className="px-5 py-4 font-medium"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {filteredMotors.map((motor) => (
                    <tr
                      key={motor.id}
                      className="border-t border-slate-800"
                    >
                      <td className="px-5 py-4 text-cyan-300">
                        {motor.motor_code}
                      </td>

                      <td className="px-5 py-4">
                        {motor.name}
                      </td>

                      <td className="px-5 py-4 text-slate-400">
                        {motor.location ?? 'Not specified'}
                      </td>

                      <td className="px-5 py-4">
                        {motor.bearings.length}
                      </td>

                      <td className="px-5 py-4">
                        {motor.operational_status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredMotors.length === 0 && (
                <p className="p-6 text-center text-sm text-slate-400">
                  No matching equipment records.
                </p>
              )}
            </div>

            <div className="border-t border-slate-800 p-5">
              <button
                type="button"
                onClick={() => onNavigate('Motor Registry')}
                className="flex items-center gap-2 text-sm font-medium text-cyan-300"
              >
                Manage Motor Registry
                <ArrowRight size={16} />
              </button>
            </div>
          </section>

          <p className="text-xs leading-6 text-amber-300">
            MachineDoctor currently displays saved research
            results. Real-time sensor monitoring and
            independently validated industrial diagnostics
            are not yet available.
          </p>
        </>
      )}
    </div>
  )
}
