
import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  FileUp,
  Info,
  LoaderCircle,
  Waves,
} from 'lucide-react'

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  analyzeSignal,
} from '../services/signalApi'

import type {
  SignalAnalysisResponse,
} from '../services/signalApi'


const MAX_FILE_BYTES = 12 * 1024 * 1024

export default function SignalExplorer() {
  const [analysis, setAnalysis] =
    useState<SignalAnalysisResponse | null>(null)

  const [filename, setFilename] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => controllerRef.current?.abort()
  }, [])

  async function handleFile(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    if (!file) return

    controllerRef.current?.abort()

    const controller = new AbortController()
    controllerRef.current = controller

    setAnalysis(null)
    setFilename('')
    setError('')
    setLoading(true)

    try {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        throw new Error('Please select a CSV file.')
      }

      if (file.size > MAX_FILE_BYTES) {
        throw new Error(
          'File exceeds the 12 MB upload limit.',
        )
      }

      const result = await analyzeSignal(
        file,
        controller.signal,
      )

      if (controller.signal.aborted) return

      setAnalysis(result)
      setFilename(file.name)
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to process recording.',
        )
      }
    } finally {
      if (controllerRef.current === controller) {
        setLoading(false)
        controllerRef.current = null
      }

      event.target.value = ''
    }
  }

  const features = analysis?.features
  const metadata = analysis?.metadata

  return (
    <div className="space-y-7">
      <div>
        <h2 className="text-2xl font-semibold">
          Signal Explorer
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Upload vibration recordings for Python-based
          signal processing and frequency analysis.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold">
              Upload Recording
            </h3>

            <p className="mt-2 text-xs text-slate-400">
              CSV columns: time_s, vibration, optional rpm.
              Maximum 12 MB and 200,000 samples.
            </p>
          </div>

          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300">
            <FileUp size={18} />
            Select CSV

            <input
              type="file"
              accept=".csv,text/csv"
              onChange={handleFile}
              className="sr-only"
            />
          </label>
        </div>

        {loading && (
          <div
            role="status"
            className="mt-5 flex items-center gap-2 text-sm text-cyan-300"
          >
            <LoaderCircle
              size={18}
              className="animate-spin"
            />
            Processing recording with Python...
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="mt-5 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300"
          >
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        {analysis && filename && (
          <div className="mt-5 flex items-center gap-2 text-sm text-emerald-300">
            <CheckCircle2 size={18} />
            Processed {filename} using FastAPI
          </div>
        )}
      </section>

      {analysis && metadata && features ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              [
                'Samples',
                metadata.sample_count.toLocaleString(),
              ],
              [
                'Duration',
                `${metadata.duration_s.toFixed(3)} s`,
              ],
              [
                'Sampling Rate',
                `${metadata.sampling_rate_hz.toFixed(2)} Hz`,
              ],
              [
                'Mean RPM',
                metadata.mean_rpm !== undefined
                  ? metadata.mean_rpm.toFixed(1)
                  : 'Not provided',
              ],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-2xl border border-slate-800 bg-[#111C2D] p-5"
              >
                <p className="text-sm text-slate-400">
                  {label}
                </p>

                <p className="mt-3 text-xl font-semibold">
                  {value}
                </p>
              </div>
            ))}
          </div>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="mb-5 flex items-center gap-2">
              <Activity className="text-cyan-400" />
              <h3 className="font-semibold">
                Time-Domain Waveform
              </h3>
            </div>

            <p className="mb-4 text-xs text-slate-500">
              Backend-calculated recording preview.
              Display points are downsampled.
            </p>

            <div className="h-80">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={analysis.waveform}>
                  <CartesianGrid
                    stroke="#253348"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="time"
                    stroke="#94A3B8"
                    tickFormatter={(value: number) =>
                      value.toFixed(2)
                    }
                  />

                  <YAxis stroke="#94A3B8" />
                  <Tooltip />

                  <Line
                    type="linear"
                    dataKey="vibration"
                    stroke="#22D3EE"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <div className="mb-5 flex items-center gap-2">
              <Waves className="text-cyan-400" />

              <h3 className="font-semibold">
                Frequency Spectrum
              </h3>
            </div>

            <p className="mb-4 text-xs text-slate-500">
              Hann-windowed FFT calculated by Python.
              Magnitudes are uncalibrated.
            </p>

            <div className="h-80">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={analysis.spectrum}>
                  <CartesianGrid
                    stroke="#253348"
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="frequency"
                    stroke="#94A3B8"
                    tickFormatter={(value: number) =>
                      value.toFixed(0)
                    }
                  />

                  <YAxis stroke="#94A3B8" />
                  <Tooltip />

                  <Line
                    type="linear"
                    dataKey="magnitude"
                    stroke="#A78BFA"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
            <h3 className="mb-5 font-semibold">
              Python-Extracted Signal Features
            </h3>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {[
                ['RMS', features.rms],
                ['Absolute Peak', features.absolute_peak],
                ['Peak-to-Peak', features.peak_to_peak],
                ['Crest Factor', features.crest_factor],
                ['Pearson Kurtosis', features.kurtosis],
                [
                  'Dominant Frequency (Hz)',
                  features.dominant_frequency,
                ],
                [
                  'Spectral Centroid (Hz)',
                  features.spectral_centroid,
                ],
              ].map(([label, value]) => (
                <div
                  key={String(label)}
                  className="rounded-xl border border-slate-800 bg-[#0B1220] p-4"
                >
                  <p className="text-xs text-slate-400">
                    {label}
                  </p>

                  <p className="mt-2 text-xl font-semibold">
                    {Number(value).toFixed(4)}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <div className="flex items-start gap-3 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-5 text-sm text-cyan-100">
            <Info
              size={20}
              className="shrink-0 text-cyan-400"
            />

            <p>
              Signal processing completed using the
              MachineDoctor Python backend. AURA diagnostic
              inference has not been performed on this recording.
              Diagnostic integration is the next phase.
            </p>
          </div>
        </>
      ) : (
        !loading && (
          <div className="rounded-2xl border border-dashed border-slate-700 p-12 text-center">
            <Waves
              className="mx-auto mb-4 text-slate-500"
              size={38}
            />

            <h3 className="font-semibold">
              No recording analyzed
            </h3>

            <p className="mt-2 text-sm text-slate-400">
              Upload a CSV to process its waveform,
              frequency spectrum and statistical features
              using the Python backend.
            </p>
          </div>
        )
      )}
    </div>
  )
}
