
from pathlib import Path

import numpy as np
import pandas as pd

from aura.simulator_v2 import generate_motor_signal
from aura.progressive_simulator import generate_progressive_signal
from aura.features import extract_features
from aura.acceleration_aware import AccelerationAwareDetector
from aura.calibrated_sequential import detect


FS = 2000
WINDOW = 2000
STEP = 1000
FAULT_START = 3.0

FEATURES = [
    "rms", "std", "peak_to_peak",
    "crest_factor", "kurtosis",
    "dominant_frequency", "spectral_centroid",
]

OUTPUT = Path("results/generated")


def window_features(signal, run_id):
    records = []

    for start in range(0, len(signal) - WINDOW + 1, STEP):
        w = signal.iloc[start:start + WINDOW]
        f = extract_features(w["vibration"].to_numpy(), FS)

        rpm = w["rpm"].to_numpy()
        time = w["time_s"].to_numpy()

        f.update({
            "rpm": float(np.mean(rpm)),
            "rpm_acceleration": float(
                (rpm[-1] - rpm[0]) / (time[-1] - time[0])
            ),
            "time_start": float(time[0]),
            "time_end": float(time[-1]),
            "run_id": run_id,
        })

        records.append(f)

    return pd.DataFrame(records)


def healthy_runs(seeds, duration=5.0):
    runs = []

    for profile in ["constant", "accelerating"]:
        for rpm in [1200, 1500, 1800]:
            for acceleration in [60, 120]:
                for seed in seeds:
                    signal = generate_motor_signal(
                        condition="healthy",
                        profile=profile,
                        start_rpm=rpm,
                        acceleration=acceleration,
                        duration=duration,
                        seed=seed,
                    )

                    run_id = f"h_{profile}_{rpm}_{acceleration}_{seed}"
                    run = window_features(signal, run_id)
                    run["profile"] = profile
                    runs.append(run)

    return runs


def progressive_runs(seeds):
    runs = []

    for profile in ["constant", "accelerating"]:
        for seed in seeds:
            signal = generate_progressive_signal(
                profile=profile,
                fault_start=FAULT_START,
                seed=seed,
            )

            run = window_features(
                signal, f"fault_{profile}_{seed}"
            )

            run["profile"] = profile
            runs.append(run)

    return runs


def score_runs(detector, runs):
    scored = []

    for run in runs:
        copy = run.copy()
        copy["score"] = detector.anomaly_score(copy)
        scored.append(copy)

    return scored


def false_alarm_rate(runs, threshold, method, parameter):
    false_alarm_runs = 0

    for run in runs:
        alerts = detect(
            run["score"].to_numpy(),
            threshold,
            method,
            parameter,
        )

        if np.any(alerts):
            false_alarm_runs += 1

    return false_alarm_runs / len(runs)


def calibrate_methods(runs, threshold, target=0.05):
    """
    Select candidates meeting the healthy-run
    false-alarm target.

    This is a preliminary calibration procedure.
    """

    candidates = {
        "single": [None],
        "consecutive": [2, 3, 4],
        "cusum": [
            (k, h)
            for k in [0.0, 0.25, 0.5, 0.75]
            for h in [0.5, 1.0, 2.0, 3.0, 4.0]
        ],
    }

    selected = {}

    for method, parameters in candidates.items():
        measurements = []

        for parameter in parameters:
            rate = false_alarm_rate(
                runs, threshold, method, parameter
            )

            measurements.append((rate, parameter))

        eligible = [
            (rate, parameter)
            for rate, parameter in measurements
            if rate <= target
        ]

        if eligible:
            # Pick the candidate with the highest
            # eligible observed false-alarm rate.
            # This is a heuristic, not a guarantee
            # of optimal detection delay.
            selected[method] = max(
                eligible,
                key=lambda x: x[0],
            )
        else:
            selected[method] = min(
                measurements,
                key=lambda x: x[0],
            )

    return selected


def evaluate(runs, threshold, method, parameter):
    rows = []

    for run in runs:
        run = run.sort_values("time_start")
        alerts = detect(
            run["score"].to_numpy(),
            threshold,
            method,
            parameter,
        )

        before = run["time_end"].to_numpy() < FAULT_START
        after = run["time_start"].to_numpy() >= FAULT_START

        false_alarm = bool(np.any(alerts[before]))
        detections = np.flatnonzero(alerts & after)

        if len(detections):
            first_index = detections[0]
            delay = (
                float(run.iloc[first_index]["time_end"])
                - FAULT_START
            )
        else:
            delay = np.nan

        rows.append({
            "run_id": run["run_id"].iloc[0],
            "profile": run["profile"].iloc[0],
            "method": method,
            "parameter": str(parameter),
            "false_alarm": false_alarm,
            "detected": len(detections) > 0,
            "delay": delay,
        })

    return pd.DataFrame(rows)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    train_runs = healthy_runs(range(100, 110))
    base_cal_runs = healthy_runs(range(500, 505))
    seq_cal_runs = healthy_runs(range(700, 730))
    test_runs = progressive_runs(range(1000, 1020))

    train = pd.concat(train_runs, ignore_index=True)
    base_cal = pd.concat(base_cal_runs, ignore_index=True)

    detector = AccelerationAwareDetector(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
    )

    detector.fit(train)
    detector.calibrate(base_cal, quantile=0.95)

    seq_cal_runs = score_runs(detector, seq_cal_runs)
    test_runs = score_runs(detector, test_runs)

    selected = calibrate_methods(
        seq_cal_runs,
        detector.threshold,
        target=0.05,
    )

    print("\n=== AURA-B007 CALIBRATION ===")

    all_results = []

    for method, (rate, parameter) in selected.items():
        print(
            f"{method}: parameter={parameter}, "
            f"calibration false-alarm rate={rate:.4f}"
        )

        result = evaluate(
            test_runs,
            detector.threshold,
            method,
            parameter,
        )

        all_results.append(result)

        print("\nTest results:")
        print(
            result.groupby("profile").agg(
                runs=("detected", "size"),
                false_alarms=("false_alarm", "sum"),
                detections=("detected", "sum"),
                mean_delay=("delay", "mean"),
            ).round(4)
        )

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(
        OUTPUT / "b007_calibrated_results.csv",
        index=False,
    )

    print("\nAURA-B007 completed.")


if __name__ == "__main__":
    main()
