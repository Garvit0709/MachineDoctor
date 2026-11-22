
export type SignalAnalysisResponse = {
  status: string
  analysis_type: string
  algorithm: string
  aura_inference_performed: boolean

  metadata: {
    sample_count: number
    duration_s: number
    sampling_rate_hz: number
    has_rpm: boolean
    mean_rpm?: number
  }

  features: {
    rms: number
    absolute_peak: number
    peak_to_peak: number
    crest_factor: number
    kurtosis: number
    dominant_frequency: number
    spectral_centroid: number
  }

  waveform: {
    time: number
    vibration: number
  }[]

  spectrum: {
    frequency: number
    magnitude: number
  }[]
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  'http://127.0.0.1:8000'

export async function analyzeSignal(
  file: File,
  signal?: AbortSignal,
): Promise<SignalAnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    `${API_BASE_URL}/api/signals/analyze`,
    {
      method: 'POST',
      body: formData,
      signal,
    },
  )

  if (!response.ok) {
    let message = `Signal analysis failed (${response.status})`

    try {
      const error: unknown = await response.json()

      if (
        typeof error === 'object' &&
        error !== null &&
        'detail' in error &&
        typeof error.detail === 'string'
      ) {
        message = error.detail
      }
    } catch {
      // Keep the HTTP status message.
    }

    throw new Error(message)
  }

  const result: SignalAnalysisResponse =
    await response.json()

  if (
    result.status !== 'processed' ||
    result.aura_inference_performed !== false ||
    !result.metadata ||
    !result.features ||
    !Array.isArray(result.waveform) ||
    !Array.isArray(result.spectrum)
  ) {
    throw new Error(
      'Unexpected signal analysis response from backend.',
    )
  }

  return result
}
