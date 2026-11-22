
export type DiagnosticState = 'NORMAL' | 'WARNING' | 'UNKNOWN'

export type DiagnosticSessionSummary = {
  id: number
  motor_id: number
  bearing_id: number | null
  run_id: string
  recording_name: string
  model_name: string
  model_version: string
  total_windows: number
  normal_count: number
  warning_count: number
  unknown_count: number
  created_at: string
}

export type DiagnosticWindow = {
  window_index: number
  time_start: number
  time_end: number
  state: DiagnosticState
  reason: string | null
  persistent_score: number | null
  instantaneous_score: number | null
  uncertainty_distance: number | null
  memory_size: number | null
}

export type DiagnosticSessionDetail = {
  id: number
  motor_id: number
  bearing_id: number | null
  run_id: string
  recording_name: string
  data_source: string
  model_name: string
  model_version: string
  created_at: string
  total_windows: number
  state_counts: Record<DiagnosticState, number>
  predictions: DiagnosticWindow[]
}

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

async function request<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    signal,
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const body: unknown = await response.json()

      if (
        typeof body === 'object' &&
        body !== null &&
        'detail' in body &&
        typeof body.detail === 'string'
      ) {
        message = body.detail
      }
    } catch {
      // Retain HTTP status message.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export const diagnosticHistoryApi = {
  list: (motorId?: number, signal?: AbortSignal) => {
    const query =
      motorId !== undefined
        ? `?motor_id=${encodeURIComponent(motorId)}`
        : ''

    return request<DiagnosticSessionSummary[]>(
      `/api/diagnostic-sessions${query}`,
      signal,
    )
  },

  get: (id: number, signal?: AbortSignal) =>
    request<DiagnosticSessionDetail>(
      `/api/diagnostic-sessions/${id}`,
      signal,
    ),
}
