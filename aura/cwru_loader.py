
from pathlib import Path

import numpy as np
from scipy.io import loadmat


DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "cwru"
)

FILES = {
    97: {"condition": "healthy", "load_hp": 0, "rpm": 1797},
    98: {"condition": "healthy", "load_hp": 1, "rpm": 1772},
    130: {"condition": "outer_race_fault", "load_hp": 0, "rpm": 1797},
    131: {"condition": "outer_race_fault", "load_hp": 1, "rpm": 1772},
}


def load_cwru_record(file_id):
    """Load one CWRU drive-end vibration recording."""

    if file_id not in FILES:
        raise ValueError(f"Unknown file ID: {file_id}")

    path = DATA_DIR / f"{file_id}.mat"

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    data = loadmat(path)

    signal_keys = [
        key for key in data
        if key.endswith("_DE_time")
    ]

    if len(signal_keys) != 1:
        raise ValueError(
            f"Expected one drive-end signal, found: {signal_keys}"
        )

    signal = np.asarray(
        data[signal_keys[0]], dtype=float
    ).ravel()

    if len(signal) < 12000:
        raise ValueError("Recording is too short.")

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains invalid values.")

    rpm_keys = [
        key for key in data
        if key.endswith("RPM")
    ]

    rpm = None
    rpm_source = "documented_approximate"

    if rpm_keys:
        rpm_values = np.asarray(
            data[rpm_keys[0]]
        ).ravel()

        if rpm_values.size > 0:
            rpm = float(rpm_values[0])
            rpm_source = "mat_file"

    if rpm is None:
        rpm = float(FILES[file_id]["rpm"])

    return {
        "file_id": file_id,
        "signal": signal,
        "sampling_rate": 12000,
        "rpm": rpm,
        "rpm_source": rpm_source,
        "condition": FILES[file_id]["condition"],
        "load_hp": FILES[file_id]["load_hp"],
    }


if __name__ == "__main__":
    for file_id in FILES:
        record = load_cwru_record(file_id)

        print(
            f"File: {file_id} | "
            f"Condition: {record['condition']} | "
            f"Samples: {len(record['signal'])} | "
            f"RPM: {record['rpm']} | "
            f"Source: {record['rpm_source']}"
        )
