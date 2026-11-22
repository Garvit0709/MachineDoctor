
import { useState } from 'react'

import AURAIntelligence from './AURAIntelligence'
import BackendStatus from './BackendStatus'
import LiveOverview from './LiveOverview'
import MotorRegistry from './MotorRegistry'
import SignalExplorer from './SignalExplorer'

import {
  Activity,
  ArrowUpRight,
  Bell,
  BrainCircuit,
  ChevronLeft,
  ChevronRight,
  Cpu,
  FileText,
  LayoutDashboard,
  Menu,
  Settings,
  X,
} from 'lucide-react'

const navigation = [
  { name: 'Overview', icon: LayoutDashboard },
  { name: 'Motor Registry', icon: Cpu },
  { name: 'Diagnostics', icon: Activity },
  { name: 'AURA Intelligence', icon: BrainCircuit },
  { name: 'Reports', icon: FileText },
  { name: 'Settings', icon: Settings },
]

export default function Dashboard() {
  const [activePage, setActivePage] = useState('Overview')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const selectPage = (page: string) => {
    setActivePage(page)
    setMobileOpen(false)
  }

  // Sidebar navigation
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

  // Placeholder for upcoming modules
  const renderPlaceholder = () => (
    <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-8">
      <div className="mb-4 flex items-center gap-3">
        <ArrowUpRight className="text-cyan-400" size={24} />
        <h2 className="text-2xl font-semibold">
          {activePage}
        </h2>
      </div>

      <p className="max-w-xl leading-7 text-slate-400">
        This module is part of the MachineDoctor development
        roadmap. Its dedicated functionality will be
        implemented in the upcoming steps.
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

  // Page rendering
  const renderPage = () => {
    switch (activePage) {
      case 'Overview':
        return <LiveOverview onNavigate={selectPage} />

      case 'Motor Registry':
        return <MotorRegistry />

      case 'Diagnostics':
        return <SignalExplorer />

      case 'AURA Intelligence':
        return <AURAIntelligence />

      default:
        return renderPlaceholder()
    }
  }

  return (
    <div className="min-h-screen bg-[#0B1220] text-slate-100">
      {/* Mobile navigation */}
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

      {/* Desktop sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 hidden flex-col border-r border-slate-800 bg-[#111C2D] transition-all duration-300 lg:flex ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {renderSidebar(collapsed)}

        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-24 rounded-full border border-slate-700 bg-[#172337] p-1 text-slate-400 hover:text-white"
          aria-label={
            collapsed ? 'Expand sidebar' : 'Collapse sidebar'
          }
        >
          {collapsed ? (
            <ChevronRight size={16} />
          ) : (
            <ChevronLeft size={16} />
          )}
        </button>
      </aside>

      {/* Main application */}
      <div
        className={`transition-all duration-300 ${
          collapsed ? 'lg:ml-20' : 'lg:ml-64'
        }`}
      >
        {/* Header */}
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-800 bg-[#0B1220]/95 px-5 backdrop-blur md:px-8">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
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
            <div className="hidden sm:block">
              <BackendStatus />
            </div>

            <span className="hidden rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1.5 text-xs font-medium text-cyan-300 xl:inline-flex">
              RESEARCH PROTOTYPE
            </span>

            <Bell size={20} className="text-slate-400" />

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-400/10 text-sm font-bold text-cyan-300">
              MD
            </div>
          </div>
        </header>

        {/* Dynamic page content */}
        <main className="mx-auto max-w-[1600px] p-5 md:p-8">
          {renderPage()}
        </main>
      </div>
    </div>
  )
}
