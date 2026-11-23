
import { apiFetch } from './apiClient'

export type AURAState =
  | 'NORMAL'
  | 'WARNING'
  | 'UNKNOWN'

export interface AURAPrediction {
  run_id: string
  time_start: number
  time_end: number
  state: AURAState
  reason: string | null
  persistent_score: number | null
  instantaneous_score: number | null
  uncertainty_distance: number | null
  memory_size: number | null
}

export interface AURAStateCounts {
  NORMAL: number
  WARNING: number
  UNKNOWN: number
}

export interface AURAThresholds {
  uncertainty: number
  persistence: number
}

export interface AURADiagnosticResult {
  application: string
  algorithm: string
  model_name: string
  model_version: string
  data_scope: string
  run_id: string
  total_windows: number
  state_counts: AURAStateCounts
  thresholds: AURAThresholds
  predictions: AURAPrediction[]
  limitations: string
}

// Preserve the type expected by AURAIntelligence.tsx.
export type AURAResponse = AURADiagnosticResult

async function parseApiError(
  response: Response,
): Promise<string> {
  const fallback = `AURA request failed (${response.status})`

  try {
    const body: unknown = await response.json()

    if (
      typeof body === 'object' &&
      body !== null &&
      'detail' in body
    ) {
      const detail = body.detail

      if (typeof detail === 'string') {
        return detail
      }

      if (Array.isArray(detail)) {
        return detail
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
    // Preserve the HTTP status fallback.
  }

  return fallback
}

export async function diagnoseAURA(
  file: File,
  signal?: AbortSignal,
): Promise<AURAResponse> {
  if (!file.name.toLowerCase().endsWith('.csv')) {
    throw new Error(
      'Only CSV feature files are supported.',
    )
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await apiFetch(
    '/api/aura/diagnose',
    {
      method: 'POST',
      body: formData,
      signal,
    },
  )

  if (!response.ok) {
    throw new Error(
      await parseApiError(response),
    )
  }

  return response.json() as Promise<AURAResponse>
}

export const auraApi = {
  diagnose: diagnoseAURA,
}
