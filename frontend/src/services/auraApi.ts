
export type AURAState = 'NORMAL' | 'WARNING' | 'UNKNOWN'

export type AURAPrediction = {
  run_id: string
  time_start: number
  time_end: number
  state: AURAState
  reason: string
  persistent_score: number
  instantaneous_score: number
  uncertainty_distance: number
  memory_size: number
}

export type AURAResponse = {
  application: string
  algorithm: string
  model_name: string
  model_version: string
  data_scope: string
  run_id: string
  total_windows: number
  state_counts: Record<AURAState, number>
  thresholds: {
    uncertainty: number
    persistence: number
  }
  predictions: AURAPrediction[]
  limitations: string
}

const API_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

export async function diagnoseAURA(
  file: File,
  signal?: AbortSignal,
): Promise<AURAResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    `${API_URL}/api/aura/diagnose`,
    {
      method: 'POST',
      body: formData,
      signal,
    },
  )

  if (!response.ok) {
    let message = `AURA diagnosis failed (${response.status})`

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
      // Keep HTTP error message.
    }

    throw new Error(message)
  }

  const result: AURAResponse = await response.json()

  if (
    result.algorithm !== 'AURA' ||
    !Array.isArray(result.predictions) ||
    !result.thresholds ||
    !result.state_counts
  ) {
    throw new Error('Invalid AURA response.')
  }

  return result
}
