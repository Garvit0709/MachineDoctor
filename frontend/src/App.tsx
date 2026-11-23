
import { AuthProvider } from './auth/AuthContext'
import { useAuth } from './auth/useAuth'

import Dashboard from './components/Dashboard'
import Login from './components/Login'

function ApplicationContent() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Login />
  }

  return <Dashboard />
}

export default function App() {
  return (
    <AuthProvider>
      <ApplicationContent />
    </AuthProvider>
  )
}
