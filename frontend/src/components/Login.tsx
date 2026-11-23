
import { useState } from 'react'
import type { FormEvent } from 'react'

import {
  Activity,
  AlertCircle,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
} from 'lucide-react'

import { useAuth } from '../auth/useAuth'
import CreatorCredit from './CreatorCredit'

export default function Login() {
  const { login } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (loading) return

    setLoading(true)
    setError('')

    try {
      await login(username.trim(), password)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Authentication failed.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0B1220] px-5 py-12 text-slate-100">
      <div className="w-full max-w-md">
        {/* Application branding */}
        <div className="mb-10 flex items-center justify-center gap-3">
          <div className="rounded-xl bg-cyan-400/10 p-3 text-cyan-400">
            <Activity size={27} />
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              MachineDoctor
            </h1>

            <p className="text-xs font-semibold tracking-[0.2em] text-cyan-400">
              POWERED BY AURA
            </p>
          </div>
        </div>

        {/* Login card */}
        <div className="rounded-2xl border border-slate-800 bg-[#111C2D] p-8 shadow-2xl">
          <div className="mb-7 text-center">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-cyan-400/10 text-cyan-400">
              <ShieldCheck size={28} />
            </div>

            <h2 className="text-2xl font-semibold">
              Administrator Access
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Sign in to manage equipment and access
              AURA diagnostic intelligence.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >
            <div>
              <label
                htmlFor="username"
                className="mb-2 block text-sm text-slate-300"
              >
                Username
              </label>

              <input
                id="username"
                type="text"
                autoComplete="username"
                required
                maxLength={100}
                value={username}
                onChange={(event) =>
                  setUsername(event.target.value)
                }
                placeholder="Administrator username"
                className="w-full rounded-xl border border-slate-700 bg-[#0B1220] px-4 py-3 text-sm outline-none transition focus:border-cyan-400"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm text-slate-300"
              >
                Password
              </label>

              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Administrator password"
                  className="w-full rounded-xl border border-slate-700 bg-[#0B1220] px-4 py-3 pr-12 text-sm outline-none transition focus:border-cyan-400"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                  aria-label={
                    showPassword
                      ? 'Hide password'
                      : 'Show password'
                  }
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300"
              >
                <AlertCircle
                  size={18}
                  className="shrink-0"
                />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <LockKeyhole size={18} />

              {loading
                ? 'Signing in...'
                : 'Sign in securely'}
            </button>
          </form>
        </div>

        {/* Creator branding */}
        <div className="mt-8 flex flex-col items-center gap-4">
          <CreatorCredit />

          <p className="text-center text-xs leading-6 text-slate-500">
            MachineDoctor Research Prototype
            {' · '}
            Experimental motor-bearing diagnostics
          </p>
        </div>
      </div>
    </div>
  )
}
