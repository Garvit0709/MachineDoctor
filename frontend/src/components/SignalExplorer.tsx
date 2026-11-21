
import { useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import FFT from 'fft.js'

import {
  Activity,
  AlertCircle,
  CheckCircle2,
  FileUp,
  Info,
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

type Sample = {
  time: number
  vibration: number
  rpm?: number
}

type SignalFeatures = {
  rms: number
  peak: number
  peakToPeak: number
  crestFactor: number
  kurtosis: number
  dominantFrequency: number
}

const MAX_SAMPLES = 200000
const FFT_SIZE = 4096

function parseCSV(text: string): Sample[] {
  const lines = text
    .replace(/^\uFEFF/, '')
    .trim()
    .split(/\r?\n/)

  if (lines.length < 3) {
    throw new Error(
      'CSV must contain a header and at least two samples.',
    )
  }

  const headers = lines[0]
    .split(',')
    .map((header) =>
      header.trim().toLowerCase().replace(/^"|"$/g, ''),
    )

  const timeIndex = headers.findIndex((header) =>
    ['time', 'time_s', 'timestamp'].includes(header),
  )

  const vibrationIndex = headers.findIndex((header) =>
    ['vibration', 'amplitude', 'signal'].includes(header),
  )

  const rpmIndex = headers.indexOf('rpm')

  if (timeIndex < 0 || vibrationIndex < 0) {
    throw new Error(
      'CSV requires time_s and vibration columns.',
    )
  }

  if (lines.length - 1 > MAX_SAMPLES) {
    throw new Error(
      `Maximum ${MAX_SAMPLES.toLocaleString()} samples supported.`,
    )
  }

  const samples: Sample[] = []

  for (let i = 1; i < lines.length; i++) {
    if (!lines[i].trim()) continue

    const values = lines[i].split(',')

    const timeValue = values[timeIndex]?.trim()
    const vibrationValue = values[vibrationIndex]?.trim()

    if (!timeValue || !vibrationValue) {
      throw new Error(
        `Missing numerical value at row ${i + 1}.`,
      )
    }

    const time = Number(timeValue)
    const vibration = Number(vibrationValue)

    if (
      !Number.isFinite(time) ||
      !Number.isFinite(vibration)
    ) {
      throw new Error(
        `Invalid numerical value at row ${i + 1}.`,
      )
    }

    const sample: Sample = {
      time,
      vibration,
    }

    if (rpmIndex >= 0 && values[rpmIndex]?.trim()) {
      const rpm = Number(values[rpmIndex])

      if (!Number.isFinite(rpm)) {
        throw new Error(
          `Invalid RPM at row ${i + 1}.`,
        )
      }

      sample.rpm = rpm
    }

    samples.push(sample)
  }

  if (samples.length < 2) {
    throw new Error(
      'At least two valid samples are required.',
    )
  }

  const firstInterval =
    samples[1].time - samples[0].time

  if (firstInterval <= 0) {
    throw new Error(
      'Time values must increase strictly.',
    )
  }

  for (let i = 1; i < samples.length; i++) {
    const interval =
      samples[i].time - samples[i - 1].time

    if (interval <= 0) {
      throw new Error(
        `Time values must increase strictly at row ${i + 2}.`,
      )
    }

    const relativeDifference =
      Math.abs(interval - firstInterval) / firstInterval

    if (relativeDifference > 0.01) {
      throw new Error(
        'Sampling intervals are not sufficiently uniform for FFT analysis.',
      )
    }
  }

  return samples
}

function getSamplingRate(samples: Sample[]): number {
  const duration =
    samples[samples.length - 1].time -
    samples[0].time

  return (samples.length - 1) / duration
}

function calculateSpectrum(samples: Sample[]) {
  const n = Math.min(
    FFT_SIZE,
    2 ** Math.floor(Math.log2(samples.length)),
  )

  const samplingRate = getSamplingRate(samples)

  const fft = new FFT(n)

  const input = new Array<number>(n)
  const output = fft.createComplexArray()

  const values = samples
    .slice(0, n)
    .map((sample) => sample.vibration)

  const mean =
    values.reduce((sum, value) => sum + value, 0) / n

  for (let i = 0; i < n; i++) {
    const hann =
      0.5 *
      (1 - Math.cos((2 * Math.PI * i) / (n - 1)))

    input[i] = (values[i] - mean) * hann
  }

  fft.realTransform(output, input)

  const spectrum: {
    frequency: number
    magnitude: number
  }[] = []

  for (let i = 0; i <= n / 2; i++) {
    const re = output[2 * i]
    const im = output[2 * i + 1]

    spectrum.push({
      frequency: (i * samplingRate) / n,
      magnitude: Math.hypot(re, im),
    })
  }

  return spectrum
}

function calculateFeatures(
  samples: Sample[],
  spectrum: ReturnType<typeof calculateSpectrum>,
): SignalFeatures {
  const n = samples.length

  let sum = 0
  let sumSquares = 0
  let peak = 0
  let minimum = Infinity
  let maximum = -Infinity

  for (const sample of samples) {
    const value = sample.vibration

    sum += value
    sumSquares += value * value

    peak = Math.max(peak, Math.abs(value))
    minimum = Math.min(minimum, value)
    maximum = Math.max(maximum, value)
  }

  const mean = sum / n
  const rms = Math.sqrt(sumSquares / n)

  let varianceSum = 0
  let fourthMomentSum = 0

  for (const sample of samples) {
    const difference = sample.vibration - mean

    varianceSum += difference ** 2
    fourthMomentSum += difference ** 4
  }

  const variance = varianceSum / n
  const fourthMoment = fourthMomentSum / n

  const kurtosis =
    variance > 1e-20
      ? fourthMoment / variance ** 2
      : 0

  const crestFactor =
    rms > 0 ? peak / rms : 0

  let dominantFrequency = 0
  let maxMagnitude = -Infinity

  for (const point of spectrum) {
    if (point.frequency === 0) continue

    if (point.magnitude > maxMagnitude) {
      maxMagnitude = point.magnitude
      dominantFrequency = point.frequency
    }
  }

  return {
    rms,
    peak,
    peakToPeak: maximum - minimum,
    crestFactor,
    kurtosis,
    dominantFrequency,
  }
}

function downsample(
  samples: Sample[],
  maxPoints = 1200,
): Sample[] {
  const step = Math.max(
    1,
    Math.ceil(samples.length / maxPoints),
  )

  return samples.filter(
    (_, index) => index % step === 0,
  )
}

export default function SignalExplorer() {
  const [samples, setSamples] = useState<Sample[]>([])
  const [filename, setFilename] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const spectrum = useMemo(
    () =>
      samples.length
        ? calculateSpectrum(samples)
        : [],
    [samples],
  )

  const features = useMemo(
    () =>
      samples.length
        ? calculateFeatures(samples, spectrum)
        : null,
    [samples, spectrum],
  )

  const waveform = useMemo(
    () => downsample(samples),
    [samples],
  )

  const duration = samples.length
    ? samples[samples.length - 1].time -
      samples[0].time
    : 0

  const samplingRate =
    samples.length > 1
      ? getSamplingRate(samples)
      : 0

  async function handleFile(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    if (!file) return

    setLoading(true)
    setError('')
    setSamples([])
    setFilename('')

    try {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        throw new Error(
          'Please select a CSV file.',
        )
      }

      const text = await file.text()
      const parsed = parseCSV(text)

      setSamples(parsed)
      setFilename(file.name)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to read CSV file.',
      )
    } finally {
      setLoading(false)
      event.target.value = ''
    }
  }

  return (
    <div className="space-y-7">
      <div>
        <h2 className="text-2xl font-semibold">
          Signal Explorer
        </h2>

        <p className="mt-2 text-sm text-slate-400">
          Upload and inspect motor-bearing vibration recordings.
          Browser calculations are exploratory.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="font-semibold">
              Upload Recording
            </h3>

            <p className="mt-2 text-xs text-slate-400">
              Supported CSV columns: time_s, vibration,
              optional rpm. Maximum 200,000 samples.
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
          <p className="mt-4 text-sm text-cyan-300">
            Processing recording...
          </p>
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

        {filename && (
          <div className="mt-5 flex items-center gap-2 text-sm text-emerald-300">
            <CheckCircle2 size={18} />
            Loaded {filename}
          </div>
        )}
      </section>

      {samples.length > 0 ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              [
                'Samples',
                samples.length.toLocaleString(),
              ],
              [
                'Duration',
                `${duration.toFixed(3)} s`,
              ],
              [
                'Sampling Rate',
                `${samplingRate.toFixed(2)} Hz`,
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

            <div className="h-80">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={waveform}>
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
              Hann-windowed FFT of the first analysis
              segment. Magnitudes are uncalibrated.
            </p>

            <div className="h-80">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <LineChart data={spectrum}>
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

          {features && (
            <section className="rounded-2xl border border-slate-800 bg-[#111C2D] p-6">
              <h3 className="mb-5 font-semibold">
                Extracted Features
              </h3>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {[
                  ['RMS', features.rms],
                  ['Absolute Peak', features.peak],
                  ['Peak-to-Peak', features.peakToPeak],
                  ['Crest Factor', features.crestFactor],
                  ['Pearson Kurtosis', features.kurtosis],
                  [
                    'Dominant Frequency (Hz)',
                    features.dominantFrequency,
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
          )}

          <div className="flex items-start gap-3 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-5 text-sm text-cyan-100">
            <Info
              size={20}
              className="shrink-0 text-cyan-400"
            />

            <p>
              Signal exploration is available.
              AURA diagnostic inference will be enabled
              after FastAPI integration and model
              configuration validation.
            </p>
          </div>
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-700 p-12 text-center">
          <Waves
            className="mx-auto mb-4 text-slate-500"
            size={38}
          />

          <h3 className="font-semibold">
            No recording loaded
          </h3>

          <p className="mt-2 text-sm text-slate-400">
            Upload a vibration CSV to view its waveform,
            frequency spectrum and statistical features.
          </p>
        </div>
      )}
    </div>
  )
}
