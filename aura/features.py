
import numpy as np
from scipy.stats import kurtosis


def extract_features(signal, sampling_rate):
    """
    Extract statistical and frequency-domain
    features from a vibration signal.

    Parameters
    ----------
    signal : array-like
        Vibration measurements.
    sampling_rate : float
        Samples per second (Hz).

    Returns
    -------
    dict
        Extracted numerical features.
    """

    x = np.asarray(signal, dtype=float)

    if x.ndim != 1 or len(x) < 2:
        raise ValueError("Signal must be a 1D array with at least 2 samples.")

    if not np.all(np.isfinite(x)):
        raise ValueError("Signal contains NaN or infinite values.")

    if sampling_rate <= 0:
        raise ValueError("Sampling rate must be positive.")

    # Time-domain features
    mean = np.mean(x)
    std = np.std(x)
    rms = np.sqrt(np.mean(x ** 2))

    peak = np.max(np.abs(x))
    peak_to_peak = np.ptp(x)

    crest_factor = peak / rms if rms > 0 else 0.0

    signal_kurtosis = (
        kurtosis(x, fisher=False, bias=False)
        if std > 1e-12 and len(x) >= 4
        else 0.0
    )

    # Remove DC offset before spectral analysis.
    centered = x - mean

    # Hann window reduces spectral leakage.
    window = np.hanning(len(centered))
    spectrum = np.abs(np.fft.rfft(centered * window))

    frequencies = np.fft.rfftfreq(
        len(centered),
        d=1.0 / sampling_rate
    )

    # Exclude DC from dominant frequency selection.
    spectrum[0] = 0.0

    if np.sum(spectrum) > 0:
        dominant_frequency = frequencies[np.argmax(spectrum)]

        spectral_centroid = (
            np.sum(frequencies * spectrum)
            / np.sum(spectrum)
        )
    else:
        dominant_frequency = 0.0
        spectral_centroid = 0.0

    return {
        "mean": float(mean),
        "std": float(std),
        "rms": float(rms),
        "peak": float(peak),
        "peak_to_peak": float(peak_to_peak),
        "crest_factor": float(crest_factor),
        "kurtosis": float(signal_kurtosis),
        "dominant_frequency": float(dominant_frequency),
        "spectral_centroid": float(spectral_centroid),
    }
