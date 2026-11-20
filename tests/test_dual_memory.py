
import numpy as np
import pytest

from aura.dual_memory import DualMemoryResidualEngine


def make_healthy_data():
    rng = np.random.default_rng(42)

    return rng.normal(
        loc=0.0,
        scale=1.0,
        size=(200, 3),
    )


def test_frozen_long_term_memory():
    engine = DualMemoryResidualEngine()
    engine.fit(make_healthy_data())

    original_mean = engine.long_term_mean.copy()
    original_scale = engine.long_term_scale.copy()

    for _ in range(20):
        engine.update(np.array([5.0, 5.0, 5.0]))

    np.testing.assert_allclose(
        engine.long_term_mean,
        original_mean,
    )

    np.testing.assert_allclose(
        engine.long_term_scale,
        original_scale,
    )


def test_persistent_deviation_increases_memory():
    engine = DualMemoryResidualEngine(alpha=0.3)
    engine.fit(make_healthy_data())

    first = engine.update(np.array([4.0, 4.0, 4.0]))

    last = first

    for _ in range(10):
        last = engine.update(np.array([4.0, 4.0, 4.0]))

    assert (
        last["persistent_score"]
        > first["persistent_score"]
    )


def test_reset_preserves_long_term_reference():
    engine = DualMemoryResidualEngine()
    engine.fit(make_healthy_data())

    original_mean = engine.long_term_mean.copy()

    engine.update(np.array([2.0, 2.0, 2.0]))
    engine.reset_short_term()

    assert engine.short_term_memory is None
    assert len(engine.history) == 0

    np.testing.assert_allclose(
        engine.long_term_mean,
        original_mean,
    )


def test_invalid_dimension():
    engine = DualMemoryResidualEngine()
    engine.fit(make_healthy_data())

    with pytest.raises(ValueError):
        engine.update(np.array([1.0, 2.0]))


def test_update_before_fit():
    engine = DualMemoryResidualEngine()

    with pytest.raises(RuntimeError):
        engine.update(np.array([1.0, 2.0, 3.0]))
