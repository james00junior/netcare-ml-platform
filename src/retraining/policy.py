"""Evidence-driven retraining decision policy.

The policy deliberately does not choose operational thresholds. Callers must
supply them explicitly after they have been approved for the deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrainingPolicy:
    """Explicit policy for deciding whether retraining should be requested."""

    min_observations: int
    require_drift: bool = True
    require_performance_degradation: bool = False

    def __post_init__(self) -> None:
        if self.min_observations <= 0:
            raise ValueError("min_observations must be positive")
        if not self.require_drift and not self.require_performance_degradation:
            raise ValueError("at least one retraining signal must be required")


def should_retrain(
    *,
    observation_count: int,
    drift_report: dict[str, Any] | None,
    performance_report: dict[str, Any] | None,
    policy: RetrainingPolicy,
) -> tuple[bool, tuple[str, ...]]:
    """Return an auditable retraining decision from explicitly supplied signals."""
    if observation_count < 0:
        raise ValueError("observation_count cannot be negative")

    reasons: list[str] = []
    if observation_count < policy.min_observations:
        return False, ("insufficient observations",)

    drifted = bool(drift_report and drift_report.get("overall_drifted", False))
    degraded = bool(performance_report and performance_report.get("degraded", False))

    if policy.require_drift and drifted:
        reasons.append("data drift detected")
    if policy.require_performance_degradation and degraded:
        reasons.append("performance degradation detected")

    if not policy.require_drift and not policy.require_performance_degradation:
        return False, ("no retraining signal configured",)

    if policy.require_drift and not drifted:
        return False, ("required drift signal not present",)
    if policy.require_performance_degradation and not degraded:
        return False, ("required performance signal not present")

    return True, tuple(reasons)
