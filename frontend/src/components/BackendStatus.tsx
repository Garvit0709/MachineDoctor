
import { useEffect, useState } from 'react'
import { Server, WifiOff } from 'lucide-react'

type HealthResponse = {
  status: string
  application: string
  algorithm: string
  version: string
}

export default function BackendStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function checkBackend() {
      try {
        const response = await fetch(
          'http://127.0.0.1:8000/api/health',
          { signal: controller.signal },
        )

        if (!response.ok) {
          throw new Error('Backend unavailable')
        }

        const data: HealthResponse = await response.json()

        setHealth(data)
        setError(false)
      } catch {
        if (!controller.signal.aborted) {
          setError(true)
        }
      }
    }

    void checkBackend()

    return () => controller.abort()
  }, [])

  return (
    <div
      className="inline-flex items-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-xs"
      role="status"
    >
      {health?.status === 'operational' && !error ? (
        <>
          <Server size={15} className="text-emerald-400" />
          <span className="text-emerald-300">
            Backend connected · v{health.version}
          </span>
        </>
      ) : error ? (
        <>
          <WifiOff size={15} className="text-red-400" />
          <span className="text-red-300">
            Backend disconnected
          </span>
        </>
      ) : (
        <span className="text-slate-400">
          Checking backend...
        </span>
      )}
    </div>
  )
}
