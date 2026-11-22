
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react'

import { motorApi } from '../services/motorApi'
import type { Motor } from '../services/motorApi'

type Props = {
  onNavigate: (page: string) => void
}

export default function LiveOverview({ onNavigate }: Props) {
  const [motors, setMotors] = useState<Motor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const records = await motorApi.list()
      setMotors(records)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to retrieve equipment records.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

 
useEffect(() => {
  let active = true

  motorApi.list()
    .then((records) => {
      if (!active) return

      setMotors(records)
      setError('')
    })
    .catch((err: unknown) => {
      if (!active) return

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to retrieve equipment records.',
      )
    })
    .finally(() => {
      if (active) {
        setLoading(false)
      }
    })

  return () => {
    active = false
  }
}, [])


  const stats = useMemo(() => {
    return {
      totalMotors: motors.length,
      totalBearings: motors.reduce(
        (sum, motor) => sum + motor.bearings.length,
        0,
      ),
      registered: motors.filter(
        (motor) => motor.operational_status === 'REGISTERED',
      ).length,
      otherStatuses: motors.filter(
        (motor) => motor.operational_status !== 'REGISTERED',
      ).length,
    }
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
      label: 'Registration Status',
      value: stats.registered,
      icon: Database,
    },
    {
      label: 'Other Operating Statuses',
      value: stats.otherStatuses,
      icon: ShieldAlert,
    },
  ]

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">
            Monitoring Overview
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Equipment information retrieved from PostgreSQL.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadData()}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-slate-700 px-4 py-3 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
        >
          <RefreshCw size={17} />
          Refresh
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300"
        >
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {loading ? (
        <p role="status" className="text-sm text-slate-400">
          Loading equipment records...
        </p>
      ) : error ? (
        <div className="rounded-xl border border-slate-800 p-6 text-sm text-slate-400">
          Dashboard metrics are unavailable until the backend
          connection is restored.
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">{label}</p>
                  <Icon size={20} className="text-cyan-400" />
                </div>

                <p className="mt-5 text-3xl font-semibold">
                  {value}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  PostgreSQL equipment registry
                </p>
              </div>
            ))}
          </div>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="mb-4 flex items-center gap-3">
              <Activity size={21} className="text-cyan-400" />
              <h3 className="font-semibold">
                Diagnostic Monitoring
              </h3>
            </div>

            <p className="text-sm leading-7 text-slate-400">
              Equipment registration is connected to PostgreSQL.
              Live vibration monitoring and historical AURA
              diagnostic results are not yet connected to
              this overview.
            </p>

            <button
              type="button"
              onClick={() => onNavigate('Diagnostics')}
              className="mt-5 flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
            >
              Open Signal Explorer
              <ArrowRight size={17} />
            </button>
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 p-6">
              <div>
                <h3 className="font-semibold">
                  Equipment Registry
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  {motors.length} motor records
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
                        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                          {motor.operational_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredMotors.length === 0 && (
                <p className="p-8 text-center text-sm text-slate-400">
                  No matching equipment records.
                </p>
              )}
            </div>

            <div className="border-t border-slate-800 p-5">
              <button
                type="button"
                onClick={() => onNavigate('Motor Registry')}
                className="flex items-center gap-2 text-sm font-medium text-cyan-300 hover:text-cyan-200"
              >
                Manage Motor Registry
                <ArrowRight size={16} />
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
