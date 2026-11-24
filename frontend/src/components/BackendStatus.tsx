
import { useEffect, useState } from 'react'
import { Server, WifiOff, LoaderCircle } from 'lucide-react'

type HealthResponse = {
  status: string
  application: string
  algorithm: string
  version: string
}

type ConnectionStatus =
  | 'checking'
  | 'connected'
  | 'disconnected'

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8000'
).replace(/\/+$/, '')

const HEALTH_CHECK_INTERVAL = 30000

export default function BackendStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(
    null
  )

  const [status, setStatus] =
    useState<ConnectionStatus>('checking')

  useEffect(() => {
    let active = true
    let currentController: AbortController | null = null

    async function checkBackend() {
      currentController?.abort()

      const controller = new AbortController()
      currentController = controller

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/health`,
          {
            method: 'GET',
            cache: 'no-store',
            signal: controller.signal,
          }
        )

        if (!response.ok) {
          throw new Error('Backend health check failed')
        }

        const data: HealthResponse = await response.json()

        if (!active || controller.signal.aborted) {
          return
        }

        setHealth(data)

        setStatus(
          data.status === 'operational'
            ? 'connected'
            : 'disconnected'
        )
      } catch {
        if (!active || controller.signal.aborted) {
          return
        }

        setStatus('disconnected')
      }
    }

    void checkBackend()

    const interval = window.setInterval(() => {
      void checkBackend()
    }, HEALTH_CHECK_INTERVAL)

    return () => {
      active = false
      window.clearInterval(interval)
      currentController?.abort()
    }
  }, [])

  return (
    <div
      className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-xs"
      role="status"
      aria-live="polite"
    >
      {status === 'connected' ? (
        <>
          <Server
            size={15}
            className="text-emerald-400"
          />

          <span className="text-emerald-300">
            Backend connected - v{health?.version}
          </span>
        </>
      ) : status === 'disconnected' ? (
        <>
          <WifiOff
            size={15}
            className="text-red-400"
          />

          <span className="text-red-300">
            Backend disconnected
          </span>
        </>
      ) : (
        <>
          <LoaderCircle
            size={15}
            className="animate-spin text-cyan-400"
          />

          <span className="text-slate-400">
            Checking backend...
          </span>
        </>
      )}
    </div>
  )
}
