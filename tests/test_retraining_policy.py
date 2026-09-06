"""Tests for the evidence-driven retraining policy."""

import pytest

from src.retraining.policy import RetrainingPolicy, should_retrain


def test_policy_requires_positive_observation_threshold() -> None:
    with pytest.raises(ValueError, match="positive"):
        RetrainingPolicy(min_observations=0)


def test_policy_requires_a_signal() -> None:
    with pytest.raises(ValueError, match="signal"):
        RetrainingPolicy(min_observations=10, require_drift=False)


def test_retraining_waits_for_enough_observations() -> None:
    policy = RetrainingPolicy(min_observations=100)

    decision, reasons = should_retrain(
        observation_count=20,
        drift_report={"overall_drifted": True},
        performance_report=None,
        policy=policy,
    )

    assert decision is False
    assert reasons == ("insufficient observations",)


def test_retraining_requires_drift_when_configured() -> None:
    policy = RetrainingPolicy(min_observations=10)

    decision, reasons = should_retrain(
        observation_count=10,
        drift_report={"overall_drifted": False},
        performance_report=None,
        policy=policy,
    )

    assert decision is False
    assert reasons == ("required drift signal not present",)


def test_retraining_triggers_on_required_drift() -> None:
    policy = RetrainingPolicy(min_observations=10)

    decision, reasons = should_retrain(
        observation_count=10,
        drift_report={"overall_drifted": True},
        performance_report=None,
        policy=policy,
    )

    assert decision is True
    assert reasons == ("data drift detected",)


def test_retraining_can_require_both_drift_and_performance_degradation() -> None:
    policy = RetrainingPolicy(
        min_observations=10,
        require_performance_degradation=True,
    )

    decision, reasons = should_retrain(
        observation_count=10,
        drift_report={"overall_drifted": True},
        performance_report={"degraded": True},
        policy=policy,
    )

    assert decision is True
    assert reasons == ("data drift detected", "performance degradation detected")
