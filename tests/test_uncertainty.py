
import numpy as np

from aura.uncertainty import OperatingConditionUncertainty


def test_unseen_conditions_are_more_distant():
    rng = np.random.default_rng(42)

    training = np.column_stack([
        rng.normal(1500, 100, 200),
        rng.normal(60, 15, 200),
    ])

    calibration = np.column_stack([
        rng.normal(1500, 100, 100),
        rng.normal(60, 15, 100),
    ])

    model = OperatingConditionUncertainty()
    model.fit(training)
    model.calibrate(calibration)

    familiar = np.array([[1500, 60]])
    unfamiliar = np.array([[2500, 300]])

    familiar_distance = model.distance(familiar)[0]
    unfamiliar_distance = model.distance(unfamiliar)[0]

    assert unfamiliar_distance > familiar_distance
    assert model.is_unfamiliar(unfamiliar)[0]
    assert not model.is_unfamiliar(familiar)[0]


def test_invalid_input():
    model = OperatingConditionUncertainty()

    invalid = np.array([
        [1500, 60],
        [np.nan, 70],
        [1600, 80],
    ])

    try:
        model.fit(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid input."
        )
