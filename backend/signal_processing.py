
import io
import numpy as np
import pandas as pd

from scipy.signal import get_window


MAX_SAMPLES = 200_000
MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_PLOT_POINTS = 1200
FFT_SIZE = 4096


class SignalValidationError(ValueError):
    pass


def parse_vibration_csv(content: bytes):
    if not content:
        raise SignalValidationError("Uploaded CSV is empty.")

    if len(content) > MAX_FILE_BYTES:
        raise SignalValidationError(
            "CSV exceeds the 12 MB file limit."
        )

    try:
        data = pd.read_csv(
            io.BytesIO(content),
            encoding="utf-8-sig",
        )
    except Exception as exc:
        raise SignalValidationError(
            "Unable to parse CSV."
        ) from exc

    data.columns = [
        str(column).strip().lower()
        for column in data.columns
    ]

    aliases = {
        "time": "time_s",
        "timestamp": "time_s",
        "amplitude": "vibration",
        "signal": "vibration",
    }

    data = data.rename(columns=aliases)

    required = {"time_s", "vibration"}

    if not required.issubset(data.columns):
        raise SignalValidationError(
            "CSV requires time_s and vibration columns."
        )

    if not 2 <= len(data) <= MAX_SAMPLES:
        raise SignalValidationError(
            "CSV must contain between 2 and 200000 samples."
        )

    columns = ["time_s", "vibration"]

    if "rpm" in data.columns:
        columns.append("rpm")

    for column in columns:
        try:
            data[column] = pd.to_numeric(
                data[column],
                errors="raise",
            )
        except (ValueError, TypeError) as exc:
            raise SignalValidationError(
                f"Invalid numerical values in {column}."
            ) from exc

    if not np.isfinite(
        data[columns].to_numpy(dtype=float)
    ).all():
        raise SignalValidationError(
            "CSV contains missing or non-finite values."
        )

    times = data["time_s"].to_numpy(dtype=float)
    intervals = np.diff(times)

    if np.any(intervals <= 0):
        raise SignalValidationError(
            "Time values must increase strictly."
        )

    median_interval = float(np.median(intervals))

    if median_interval <= 0:
        raise SignalValidationError(
            "Invalid sampling interval."
        )

    relative_deviation = (
        np.abs(intervals - median_interval)
        / median_interval
    )

    if np.any(relative_deviation > 0.01):
        raise SignalValidationError(
            "Sampling intervals must be uniform within 1%."
        )

    sampling_rate = 1.0 / float(
        np.mean(intervals)
    )

    return data, sampling_rate


def extract_signal_features(signal, sampling_rate):
    x = np.asarray(signal, dtype=float)

    if x.ndim != 1 or len(x) < 2:
        raise SignalValidationError(
            "Signal must contain at least two samples."
        )

    if not np.isfinite(x).all():
        raise SignalValidationError(
            "Signal contains non-finite values."
        )

    mean = float(np.mean(x))
    rms = float(np.sqrt(np.mean(x ** 2)))
    peak = float(np.max(np.abs(x)))
    peak_to_peak = float(np.ptp(x))

    variance = float(np.mean((x - mean) ** 2))

    kurtosis = (
        float(np.mean((x - mean) ** 4) / variance ** 2)
        if variance > 1e-20
        else 0.0
    )

    crest_factor = peak / rms if rms > 0 else 0.0

    n_fft = min(FFT_SIZE, 2 ** int(np.floor(np.log2(len(x)))))

    segment = x[:n_fft]
    segment = segment - np.mean(segment)

    window = get_window(
        "hann", n_fft, fftbins=False
    )

    spectrum = np.abs(
        np.fft.rfft(segment * window)
    )

    frequencies = np.fft.rfftfreq(
        n_fft,
        d=1.0 / sampling_rate,
    )

    if len(spectrum) > 1:
        dominant_index = (
            int(np.argmax(spectrum[1:])) + 1
        )
        dominant_frequency = float(
            frequencies[dominant_index]
        )
    else:
        dominant_frequency = 0.0

    magnitude_sum = float(np.sum(spectrum))

    spectral_centroid = (
        float(
            np.sum(frequencies * spectrum)
            / magnitude_sum
        )
        if magnitude_sum > 0
        else 0.0
    )

    return {
        "rms": rms,
        "absolute_peak": peak,
        "peak_to_peak": peak_to_peak,
        "crest_factor": crest_factor,
        "kurtosis": kurtosis,
        "dominant_frequency": dominant_frequency,
        "spectral_centroid": spectral_centroid,
    }


def analyze_vibration_csv(content: bytes):
    data, sampling_rate = parse_vibration_csv(content)

    signal = data["vibration"].to_numpy(dtype=float)
    times = data["time_s"].to_numpy(dtype=float)

    features = extract_signal_features(
        signal, sampling_rate
    )

    # Preserve full-resolution calculations.
    # Downsample only for browser visualization.
    plot_step = max(
        1,
        int(np.ceil(len(signal) / MAX_PLOT_POINTS)),
    )

    waveform = [
        {
            "time": float(times[i]),
            "vibration": float(signal[i]),
        }
        for i in range(0, len(signal), plot_step)
    ]

    n_fft = min(
        FFT_SIZE,
        2 ** int(np.floor(np.log2(len(signal)))),
    )

    segment = signal[:n_fft]
    segment = segment - np.mean(segment)

    window = get_window(
        "hann", n_fft, fftbins=False
    )

    magnitudes = np.abs(
        np.fft.rfft(segment * window)
    )

    frequencies = np.fft.rfftfreq(
        n_fft,
        d=1.0 / sampling_rate,
    )

    spectrum = [
        {
            "frequency": float(frequency),
            "magnitude": float(magnitude),
        }
        for frequency, magnitude in zip(
            frequencies, magnitudes
        )
    ]

    metadata = {
        "sample_count": len(signal),
        "duration_s": float(times[-1] - times[0]),
        "sampling_rate_hz": sampling_rate,
        "has_rpm": "rpm" in data.columns,
    }

    if "rpm" in data.columns:
        metadata["mean_rpm"] = float(
            data["rpm"].mean()
        )

    return {
        "status": "processed",
        "analysis_type": "signal_features_only",
        "algorithm": "AURA",
        "aura_inference_performed": False,
        "metadata": metadata,
        "features": features,
        "waveform": waveform,
        "spectrum": spectrum,
    }
