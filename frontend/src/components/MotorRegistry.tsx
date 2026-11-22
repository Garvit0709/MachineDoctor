
import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import {
  Activity,
  AlertCircle,
  Cpu,
  LoaderCircle,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from 'lucide-react'

import { motorApi } from '../services/motorApi'
import type {
  BearingCreate,
  Motor,
  MotorCreate,
} from '../services/motorApi'

type MotorForm = {
  motor_code: string
  name: string
  location: string
  motor_type: string
  manufacturer: string
  rated_rpm: string
  rated_power_kw: string
  notes: string
}

const emptyForm: MotorForm = {
  motor_code: '',
  name: '',
  location: '',
  motor_type: '',
  manufacturer: '',
  rated_rpm: '',
  rated_power_kw: '',
  notes: '',
}

const inputClass =
  'w-full rounded-xl border border-slate-700 bg-[#0B1220] px-4 py-3 text-sm text-white outline-none focus:border-cyan-400'

function optionalNumber(value: string) {
  return value.trim() ? Number(value) : null
}

function formToPayload(form: MotorForm): MotorCreate {
  return {
    motor_code: form.motor_code.trim(),
    name: form.name.trim(),
    location: form.location.trim() || null,
    motor_type: form.motor_type.trim() || null,
    manufacturer: form.manufacturer.trim() || null,
    rated_rpm: optionalNumber(form.rated_rpm),
    rated_power_kw: optionalNumber(form.rated_power_kw),
    notes: form.notes.trim() || null,
  }
}

export default function MotorRegistry() {
  const [motors, setMotors] = useState<Motor[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Motor | null>(null)
  const [form, setForm] = useState<MotorForm>(emptyForm)

  const [selectedMotor, setSelectedMotor] =
    useState<Motor | null>(null)

  const [bearingCode, setBearingCode] = useState('')
  const [bearingPosition, setBearingPosition] =
    useState('DRIVE_END')
  const [bearingType, setBearingType] = useState('')

  const loadMotors = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const data = await motorApi.list()
      setMotors(data)
      setSelectedMotor((previous) =>
        previous
          ? data.find((m) => m.id === previous.id) ?? null
          : null,
      )
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load motors.',
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
          : 'Failed to load motors.',
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

  function openCreate() {
    setEditing(null)
    setForm({ ...emptyForm })
    setShowForm(true)
    setError('')
  }

  function openEdit(motor: Motor) {
    setEditing(motor)
    setForm({
      motor_code: motor.motor_code,
      name: motor.name,
      location: motor.location ?? '',
      motor_type: motor.motor_type ?? '',
      manufacturer: motor.manufacturer ?? '',
      rated_rpm: motor.rated_rpm?.toString() ?? '',
      rated_power_kw: motor.rated_power_kw?.toString() ?? '',
      notes: motor.notes ?? '',
    })
    setShowForm(true)
    setError('')
  }

  async function saveMotor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError('')

    try {
      const payload = formToPayload(form)

      if (editing) {
        const { motor_code: _code, ...changes } = payload
        void _code
        await motorApi.update(editing.id, changes)
      } else {
        await motorApi.create(payload)
      }

      setShowForm(false)
      setEditing(null)
      await loadMotors()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Unable to save motor.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function deleteMotor(motor: Motor) {
    const confirmed = window.confirm(
      `Delete ${motor.name} and all its bearings?`,
    )

    if (!confirmed) return

    setError('')

    try {
      await motorApi.remove(motor.id)
      await loadMotors()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Unable to delete motor.',
      )
    }
  }

  async function addBearing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!selectedMotor) return

    setSaving(true)
    setError('')

    try {
      const payload: BearingCreate = {
        bearing_code: bearingCode.trim(),
        position: bearingPosition,
        bearing_type: bearingType.trim() || null,
      }

      await motorApi.addBearing(selectedMotor.id, payload)

      setBearingCode('')
      setBearingType('')
      await loadMotors()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Unable to add bearing.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <Cpu size={26} className="text-cyan-400" />
            <h2 className="text-2xl font-semibold">Motor Registry</h2>
          </div>
          <p className="text-sm text-slate-400">
            Manage motor equipment and bearing information
            stored in PostgreSQL.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => void loadMotors()}
            className="rounded-xl border border-slate-700 p-3 text-slate-300 hover:bg-slate-800"
            aria-label="Refresh motors"
          >
            <RefreshCw size={18} />
          </button>

          <button
            type="button"
            onClick={openCreate}
            className="flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
          >
            <Plus size={18} />
            Register Motor
          </button>
        </div>
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

      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 p-6">
          <div>
            <h3 className="font-semibold">Registered Motors</h3>
            <p className="mt-1 text-xs text-slate-500">
              {motors.length} equipment records
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-slate-700 px-3">
            <Search size={17} className="text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search motors..."
              aria-label="Search motors"
              className="w-48 bg-transparent py-2.5 text-sm outline-none"
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center gap-3 p-12 text-slate-400">
            <LoaderCircle className="animate-spin" size={20} />
            Loading motors...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[750px] text-left text-sm">
              <thead className="bg-slate-800/30 text-xs text-slate-400">
                <tr>
                  {['Code', 'Motor', 'Location', 'Rated RPM', 'Status', 'Actions'].map(
                    (heading) => (
                      <th key={heading} className="px-5 py-4 font-medium">
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredMotors.map((motor) => (
                  <tr
                    key={motor.id}
                    className="border-t border-slate-800 hover:bg-slate-800/20"
                  >
                    <td className="px-5 py-4 font-medium text-cyan-300">
                      {motor.motor_code}
                    </td>
                    <td className="px-5 py-4">{motor.name}</td>
                    <td className="px-5 py-4 text-slate-400">
                      {motor.location ?? '—'}
                    </td>
                    <td className="px-5 py-4">
                      {motor.rated_rpm ?? '—'}
                    </td>
                    <td className="px-5 py-4">
                      <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                        {motor.operational_status}
                      </span>
                    </td>
                    <td className="flex gap-2 px-5 py-4">
                      <button
                        type="button"
                        onClick={() => setSelectedMotor(motor)}
                        className="rounded-lg border border-slate-700 p-2 text-cyan-300"
                        title="View bearings"
                      >
                        <Activity size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => openEdit(motor)}
                        className="rounded-lg border border-slate-700 p-2"
                        title="Edit motor"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => void deleteMotor(motor)}
                        className="rounded-lg border border-red-500/20 p-2 text-red-300"
                        title="Delete motor"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredMotors.length === 0 && (
              <p className="p-8 text-center text-sm text-slate-400">
                No matching motors found.
              </p>
            )}
          </div>
        )}
      </section>

      {selectedMotor && (
        <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h3 className="font-semibold">
                Bearings — {selectedMotor.name}
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                {selectedMotor.bearings.length} registered bearings
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedMotor(null)}
              aria-label="Close bearing details"
              className="text-slate-400 hover:text-white"
            >
              <X size={20} />
            </button>
          </div>

          <div className="mb-6 space-y-2">
            {selectedMotor.bearings.map((bearing) => (
              <div
                key={bearing.id}
                className="flex justify-between rounded-xl border border-slate-800 p-4 text-sm"
              >
                <span>{bearing.bearing_code}</span>
                <span className="text-slate-400">{bearing.position}</span>
              </div>
            ))}
          </div>

          <form onSubmit={(event) => void addBearing(event)} className="grid gap-3 md:grid-cols-4">
            <input
              required
              maxLength={50}
              value={bearingCode}
              onChange={(event) => setBearingCode(event.target.value)}
              placeholder="Bearing code"
              className={inputClass}
            />

            <select
              value={bearingPosition}
              onChange={(event) => setBearingPosition(event.target.value)}
              className={inputClass}
            >
              <option value="DRIVE_END">Drive End</option>
              <option value="FAN_END">Fan End</option>
              <option value="OTHER">Other</option>
            </select>

            <input
              value={bearingType}
              maxLength={100}
              onChange={(event) => setBearingType(event.target.value)}
              placeholder="Bearing type"
              className={inputClass}
            />

            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
            >
              Add Bearing
            </button>
          </form>
        </section>
      )}

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-700 bg-[#111C2D] p-6">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-xl font-semibold">
                {editing ? 'Edit Motor' : 'Register Motor'}
              </h3>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                aria-label="Close form"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={(event) => void saveMotor(event)} className="grid gap-4 sm:grid-cols-2">
              {([
                ['motor_code', 'Motor Code'],
                ['name', 'Motor Name'],
                ['location', 'Location'],
                ['motor_type', 'Motor Type'],
                ['manufacturer', 'Manufacturer'],
                ['rated_rpm', 'Rated RPM'],
                ['rated_power_kw', 'Rated Power (kW)'],
              ] as const).map(([key, label]) => (
                <label key={key} className="space-y-2 text-sm">
                  <span className="text-slate-400">{label}</span>
                  <input
                    value={form[key]}
                    disabled={Boolean(editing && key === 'motor_code')}
                    required={key === 'motor_code' || key === 'name'}
                    type={
                      key === 'rated_rpm' || key === 'rated_power_kw'
                        ? 'number'
                        : 'text'
                    }
                    min={
                      key === 'rated_rpm' || key === 'rated_power_kw'
                        ? '0.000001'
                        : undefined
                    }
                    step={
                      key === 'rated_rpm' || key === 'rated_power_kw'
                        ? 'any'
                        : undefined
                    }
                    onChange={(event) =>
                      setForm((previous) => ({
                        ...previous,
                        [key]: event.target.value,
                      }))
                    }
                    className={inputClass}
                  />
                </label>
              ))}

              <label className="space-y-2 text-sm sm:col-span-2">
                <span className="text-slate-400">Notes</span>
                <textarea
                  value={form.notes}
                  onChange={(event) =>
                    setForm((previous) => ({
                      ...previous,
                      notes: event.target.value,
                    }))
                  }
                  rows={3}
                  className={inputClass}
                />
              </label>

              <div className="flex justify-end gap-3 sm:col-span-2">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="rounded-xl border border-slate-700 px-5 py-3 text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Motor'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
