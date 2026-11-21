
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

export async function analyzeSignal(
  file: File,
): Promise<SignalAnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(
    'http://127.0.0.1:8000/api/signals/analyze',
    {
      method: 'POST',
      body: formData,
    },
  )

  if (!response.ok) {
    let message = `Analysis failed (${response.status})`

    try {
      const error = await response.json()
      if (typeof error.detail === 'string') {
        message = error.detail
      }
    } catch {
      // Preserve the HTTP status message.
    }

    throw new Error(message)
  }

  return response.json() as Promise<SignalAnalysisResponse>
}
