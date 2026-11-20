
import pytest

from aura.decision_engine import AURADecisionEngine


@pytest.fixture
def engine():
    return AURADecisionEngine(
        uncertainty_threshold=2.5,
        persistence_threshold=1.8,
        min_history=3,
    )


def memory(persistent, history=5, instantaneous=1.0):
    return {
        "persistent_score": persistent,
        "instantaneous_score": instantaneous,
        "memory_size": history,
    }


def test_normal_decision(engine):
    result = engine.decide(
        1.0,
        memory(persistent=0.5),
    )

    assert result["state"] == "NORMAL"


def test_warning_decision(engine):
    result = engine.decide(
        1.0,
        memory(persistent=2.4),
    )

    assert result["state"] == "WARNING"


def test_unknown_for_unfamiliar_conditions(engine):
    result = engine.decide(
        4.0,
        memory(persistent=2.4),
    )

    assert result["state"] == "UNKNOWN"


def test_unknown_for_insufficient_history(engine):
    result = engine.decide(
        1.0,
        memory(persistent=2.4, history=1),
    )

    assert result["state"] == "UNKNOWN"


def test_uncertainty_has_priority(engine):
    result = engine.decide(
        5.0,
        memory(persistent=10.0),
    )

    assert result["state"] == "UNKNOWN"


def test_invalid_threshold():
    with pytest.raises(ValueError):
        AURADecisionEngine(
            uncertainty_threshold=-1,
            persistence_threshold=1.0,
        )


def test_missing_memory_measurements(engine):
    with pytest.raises(ValueError):
        engine.decide(
            1.0,
            {"persistent_score": 2.0},
        )
