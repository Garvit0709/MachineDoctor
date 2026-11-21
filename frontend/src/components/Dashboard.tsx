import BackendStatus from './BackendStatus'
import { useState } from 'react'
import SignalExplorer from './SignalExplorer'
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Cpu,
  FileText,
  Gauge,
  LayoutDashboard,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react'

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'


// --------------------------------------------------
// TYPES
// --------------------------------------------------

type DiagnosticState = 'NORMAL' | 'WARNING' | 'UNKNOWN'

type Motor = {
  id: string
  name: string
  location: string
  rpm: number
  rms: number
  state: DiagnosticState
}

// --------------------------------------------------
// DEMONSTRATION DATA
// --------------------------------------------------

const motors: Motor[] = [
  {
    id: 'MTR-001',
    name: 'Induction Motor A',
    location: 'Production Line A',
    rpm: 1490,
    rms: 0.18,
    state: 'NORMAL',
  },
  {
    id: 'MTR-002',
    name: 'Induction Motor B',
    location: 'Production Line B',
    rpm: 1780,
    rms: 0.74,
    state: 'WARNING',
  },
  {
    id: 'MTR-003',
    name: 'Cooling Motor',
    location: 'Cooling Unit',
    rpm: 2200,
    rms: 0.41,
    state: 'UNKNOWN',
  },
  {
    id: 'MTR-004',
    name: 'Conveyor Motor',
    location: 'Conveyor Section',
    rpm: 1450,
    rms: 0.16,
    state: 'NORMAL',
  },
]

const vibrationData = Array.from(
  { length: 50 },
  (_, i) => ({
    time: i,
    vibration:
      0.25 +
      0.08 * Math.sin(i * 0.65) +
      0.035 * Math.sin(i * 1.9) +
      (i > 30 ? (i - 30) * 0.014 : 0),
  }),
)

const navigation = [
  { name: 'Overview', icon: LayoutDashboard },
  { name: 'Motor Registry', icon: Cpu },
  { name: 'Diagnostics', icon: Activity },
  { name: 'AURA Intelligence', icon: BrainCircuit },
  { name: 'Reports', icon: FileText },
  { name: 'Settings', icon: Settings },
]

const stateStyles: Record<DiagnosticState, string> = {
  NORMAL:
    'bg-emerald-400/10 text-emerald-400 border-emerald-400/20',
  WARNING:
    'bg-amber-400/10 text-amber-400 border-amber-400/20',
  UNKNOWN:
    'bg-slate-400/10 text-slate-300 border-slate-400/20',
}

// --------------------------------------------------
// STATUS BADGE
// --------------------------------------------------

function StateBadge({
  state,
}: {
  state: DiagnosticState
}) {
  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${stateStyles[state]}`}
    >
      {state}
    </span>
  )
}

// --------------------------------------------------
// MAIN DASHBOARD
// --------------------------------------------------

export default function Dashboard() {
  const [activePage, setActivePage] = useState('Overview')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [search, setSearch] = useState('')

  const filteredMotors = motors.filter((motor) =>
    `${motor.name} ${motor.id} ${motor.location}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  )

  const selectPage = (page: string) => {
    setActivePage(page)
    setMobileOpen(false)
  }

  // --------------------------------------------------
  // SIDEBAR
  // --------------------------------------------------

  const renderSidebar = (isCollapsed: boolean) => (
    <>
      <div className="flex h-20 items-center justify-between border-b border-slate-800 px-5">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="shrink-0 rounded-xl bg-cyan-400/10 p-2.5 text-cyan-400">
            <Activity size={23} />
          </div>

          {!isCollapsed && (
            <div className="min-w-0">
              <h1 className="text-lg font-bold tracking-tight">
                MachineDoctor
              </h1>

              <p className="text-[10px] font-semibold tracking-[0.2em] text-cyan-400">
                POWERED BY AURA
              </p>
            </div>
          )}
        </div>

        <button
          type="button"
          className="text-slate-400 hover:text-white lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation"
        >
          <X size={20} />
        </button>
      </div>

      <nav
        className="space-y-1 px-3 py-6"
        aria-label="Main navigation"
      >
        {!isCollapsed && (
          <p className="mb-4 px-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Workspace
          </p>
        )}

        {navigation.map(({ name, icon: Icon }) => (
          <button
            key={name}
            type="button"
            onClick={() => selectPage(name)}
            title={name}
            aria-current={
              activePage === name ? 'page' : undefined
            }
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${
              activePage === name
                ? 'bg-cyan-400/10 font-medium text-cyan-300'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Icon size={19} className="shrink-0" />

            {!isCollapsed && <span>{name}</span>}
          </button>
        ))}
      </nav>

      {!isCollapsed && (
        <div className="mt-auto border-t border-slate-800 p-5">
          <div className="rounded-xl border border-cyan-400/10 bg-cyan-400/5 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-cyan-300">
              <BrainCircuit size={16} />
              AURA v0.1
            </div>

            <p className="text-xs leading-5 text-slate-400">
              Experimental diagnostic algorithm.
              Scientific validation is ongoing.
            </p>
          </div>
        </div>
      )}
    </>
  )

  // --------------------------------------------------
  // OVERVIEW PAGE
  // --------------------------------------------------

  const renderOverview = () => (
    <>
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            Monitoring Overview
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Demonstration environment for motor-bearing diagnostics.
          </p>
        </div>

        <button
          type="button"
          onClick={() => selectPage('Diagnostics')}
          className="flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
        >
          <Upload size={17} />
          Open Diagnostics
        </button>
      </div>

      {/* SUMMARY CARDS */}

      <div className="mb-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: 'Registered Motors',
            value: '04',
            icon: Cpu,
          },
          {
            label: 'Normal',
            value: '02',
            icon: ShieldCheck,
          },
          {
            label: 'Warnings',
            value: '01',
            icon: AlertTriangle,
          },
          {
            label: 'Unknown',
            value: '01',
            icon: CircleHelp,
          },
        ].map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
          >
            <div className="mb-5 flex items-center justify-between">
              <span className="text-sm text-slate-400">
                {label}
              </span>

              <Icon
                size={20}
                className="text-cyan-400"
              />
            </div>

            <p className="text-3xl font-semibold">
              {value}
            </p>

            <p className="mt-2 text-xs text-slate-500">
              Illustrative monitoring data
            </p>
          </div>
        ))}
      </div>

      {/* VIBRATION AND AURA PANELS */}

      <div className="mb-7 grid gap-6 xl:grid-cols-3">
        <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6 xl:col-span-2">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold">
                Vibration Trend
              </h3>

              <p className="mt-1 text-xs text-slate-500">
                Illustrative signal — not live sensor data
              </p>
            </div>

            <Gauge
              size={20}
              className="text-cyan-400"
            />
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer
              width="100%"
              height="100%"
            >
              <AreaChart data={vibrationData}>
                <defs>
                  <linearGradient
                    id="vibrationFill"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#22D3EE"
                      stopOpacity={0.25}
                    />

                    <stop
                      offset="100%"
                      stopColor="#22D3EE"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  stroke="#253348"
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="time"
                  stroke="#64748B"
                  tickLine={false}
                />

                <YAxis
                  stroke="#64748B"
                  tickLine={false}
                  domain={[0, 'auto']}
                />

                <Tooltip
                  contentStyle={{
                    background: '#172337',
                    border: '1px solid #334155',
                    borderRadius: 12,
                    color: '#E2E8F0',
                  }}
                />

                <Area
                  type="monotone"
                  dataKey="vibration"
                  stroke="#22D3EE"
                  strokeWidth={2}
                  fill="url(#vibrationFill)"
                  dot={false}
                  name="Illustrative vibration"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* AURA INFORMATION */}

        <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
          <div className="mb-6 flex items-center gap-3">
            <BrainCircuit
              className="text-cyan-400"
              size={22}
            />

            <h3 className="font-semibold">
              AURA Intelligence
            </h3>
          </div>

          <p className="text-sm leading-7 text-slate-400">
            AURA v0.1 combines operating-condition
            unfamiliarity with persistent residual analysis.
          </p>

          <div className="mt-6 space-y-4">
            {[
              [
                'Healthy reference',
                'Frozen baseline',
              ],
              [
                'Residual memory',
                'EWMA',
              ],
              [
                'Uncertainty',
                'Mahalanobis distance',
              ],
              [
                'Decision states',
                'Normal / Warning / Unknown',
              ],
            ].map(([label, value]) => (
              <div
                key={label}
                className="border-b border-slate-800 pb-3"
              >
                <p className="text-xs text-slate-500">
                  {label}
                </p>

                <p className="mt-1 text-sm font-medium">
                  {value}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-5 text-xs leading-5 text-amber-300">
            Research prototype. No validated failure
            probability or remaining useful life estimate
            is available.
          </p>
        </section>
      </div>

      {/* MOTOR REGISTRY */}

      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111C2D]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 p-6">
          <div>
            <h3 className="font-semibold">
              Motor Registry
            </h3>

            <p className="mt-1 text-xs text-slate-500">
              Demonstration assets
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-slate-700 px-3">
            <Search
              size={17}
              className="text-slate-500"
            />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search motors..."
              aria-label="Search motors"
              className="w-44 bg-transparent py-2.5 text-sm outline-none placeholder:text-slate-600"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[650px] text-left text-sm">
            <thead className="bg-slate-800/30 text-xs text-slate-500">
              <tr>
                {[
                  'Motor',
                  'Location',
                  'RPM',
                  'RMS (illustrative)',
                  'Status',
                ].map((heading) => (
                  <th
                    key={heading}
                    className="px-6 py-4 font-medium"
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
                  className="border-t border-slate-800/80 hover:bg-slate-800/20"
                >
                  <td className="px-6 py-4">
                    <p className="font-medium">
                      {motor.name}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      {motor.id}
                    </p>
                  </td>

                  <td className="px-6 py-4 text-slate-400">
                    {motor.location}
                  </td>

                  <td className="px-6 py-4">
                    {motor.rpm}
                  </td>

                  <td className="px-6 py-4">
                    {motor.rms.toFixed(2)}
                  </td>

                  <td className="px-6 py-4">
                    <StateBadge state={motor.state} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredMotors.length === 0 && (
            <p className="p-6 text-sm text-slate-400">
              No motors match your search.
            </p>
          )}
        </div>
      </section>
    </>
  )

  // --------------------------------------------------
  // PLACEHOLDER PAGES
  // --------------------------------------------------

  const renderPlaceholder = () => (
    <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-8">
      <div className="mb-4 flex items-center gap-3">
        <ArrowUpRight
          className="text-cyan-400"
          size={24}
        />

        <h2 className="text-2xl font-semibold">
          {activePage}
        </h2>
      </div>

      <p className="max-w-xl leading-7 text-slate-400">
        This module is part of the MachineDoctor
        development roadmap. Its dedicated functionality
        will be implemented in the upcoming steps.
      </p>

      <button
        type="button"
        onClick={() => selectPage('Overview')}
        className="mt-6 rounded-xl border border-slate-700 px-5 py-2.5 text-sm text-cyan-300 hover:bg-slate-800"
      >
        Return to Overview
      </button>
    </section>
  )

  // --------------------------------------------------
  // PAGE CONTENT
  // --------------------------------------------------

  
const renderPage = () => {
  switch (activePage) {
    case 'Overview':
      return renderOverview()

    case 'Diagnostics':
      return <SignalExplorer />

    default:
      return renderPlaceholder()
  }
}


  // --------------------------------------------------
  // APPLICATION LAYOUT
  // --------------------------------------------------

  return (
    <div className="min-h-screen bg-[#0B1220] text-slate-100">

      {/* MOBILE NAVIGATION */}

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/70"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          />

          <aside className="relative z-10 flex h-full w-72 flex-col bg-[#111C2D]">
            {renderSidebar(false)}
          </aside>
        </div>
      )}

      {/* DESKTOP SIDEBAR */}

      <aside
        className={`fixed inset-y-0 left-0 hidden flex-col border-r border-slate-800 bg-[#111C2D] transition-all duration-300 lg:flex ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {renderSidebar(collapsed)}

        <button
          type="button"
          onClick={() =>
            setCollapsed(!collapsed)
          }
          className="absolute -right-3 top-24 rounded-full border border-slate-700 bg-[#172337] p-1 text-slate-400 hover:text-white"
          aria-label={
            collapsed
              ? 'Expand sidebar'
              : 'Collapse sidebar'
          }
        >
          {collapsed ? (
            <ChevronRight size={16} />
          ) : (
            <ChevronLeft size={16} />
          )}
        </button>
      </aside>

      {/* MAIN CONTENT */}

      <div
        className={`transition-all duration-300 ${
          collapsed
            ? 'lg:ml-20'
            : 'lg:ml-64'
        }`}
      >

        {/* HEADER */}

        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-800 bg-[#0B1220]/95 px-5 backdrop-blur md:px-8">
          <div className="flex items-center gap-4">
            <BackendStatus />
            <button
              type="button"
              onClick={() =>
                setMobileOpen(true)
              }
              className="text-slate-300 lg:hidden"
              aria-label="Open navigation"
            >
              <Menu size={24} />
            </button>

            <div>
              <p className="text-xs text-slate-500">
                MachineDoctor / Workspace
              </p>

              <h2 className="text-xl font-semibold">
                {activePage}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-300 sm:inline-flex">
              DEMONSTRATION DATA
            </span>

            <Bell
              size={20}
              className="text-slate-400"
            />

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-400/10 text-sm font-bold text-cyan-300">
              MD
            </div>
          </div>
        </header>

        {/* DYNAMIC PAGE */}

        <main className="mx-auto max-w-[1600px] p-5 md:p-8">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}
