
import { apiFetch } from './apiClient'

export type DiagnosticState =
  | 'NORMAL'
  | 'WARNING'
  | 'UNKNOWN'

export interface DiagnosticSessionSummary {
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

export interface DiagnosticWindow {
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

export interface DiagnosticSessionDetail {
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

async function request<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await apiFetch(path, {
    signal,
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`

    try {
      const body: unknown = await response.json()

      if (
        typeof body === 'object' &&
        body !== null &&
        'detail' in body
      ) {
        const detail = body.detail

        if (typeof detail === 'string') {
          message = detail
        } else if (Array.isArray(detail)) {
          message = detail
            .map((item: unknown) => {
              if (
                typeof item === 'object' &&
                item !== null &&
                'msg' in item &&
                typeof item.msg === 'string'
              ) {
                return item.msg
              }

              return 'Invalid input'
            })
            .join('; ')
        }
      }
    } catch {
      // Keep the HTTP status fallback.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export const diagnosticHistoryApi = {
  list: (
    motorId?: number,
    signal?: AbortSignal,
  ) => {
    const query =
      motorId !== undefined
        ? `?motor_id=${encodeURIComponent(motorId)}`
        : ''

    return request<DiagnosticSessionSummary[]>(
      `/api/diagnostic-sessions${query}`,
      signal,
    )
  },

  get: (
    sessionId: number,
    signal?: AbortSignal,
  ) =>
    request<DiagnosticSessionDetail>(
      `/api/diagnostic-sessions/${sessionId}`,
      signal,
    ),
}
