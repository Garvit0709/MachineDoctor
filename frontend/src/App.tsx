
import { lazy, Suspense } from 'react'

import { AuthProvider } from './auth/AuthContext'
import { useAuth } from './auth/useAuth'

import Login from './components/Login'

const Dashboard = lazy(
  () => import('./components/Dashboard')
)

function DashboardLoading() {
  return (
    <div
      role="status"
      className="flex min-h-screen items-center justify-center bg-[#0B1220] text-slate-100"
    >
      <div className="text-center">
        <div className="mx-auto mb-5 h-12 w-12 animate-spin rounded-full border-4 border-slate-700 border-t-cyan-400" />

        <p className="text-sm text-slate-400">
          Loading MachineDoctor...
        </p>
      </div>
    </div>
  )
}

function ApplicationContent() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Login />
  }

  return (
    <Suspense fallback={<DashboardLoading />}>
      <Dashboard />
    </Suspense>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ApplicationContent />
    </AuthProvider>
  )
}
