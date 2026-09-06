"""End-to-end synthetic validation of the Phase 12 retraining decision."""

from src.monitoring.drift import detect_data_drift
from src.retraining.policy import RetrainingPolicy, should_retrain
from src.retraining.synthetic import make_reference_dataset, make_shifted_dataset

NUMERICAL = ["age", "creatinine", "hemoglobin", "sodium", "potassium"]
CATEGORICAL = ["sex", "admission_type", "admission_source"]


def test_synthetic_drift_requests_retraining_after_minimum_observations() -> None:
    reference = make_reference_dataset()
    current = make_shifted_dataset()
    drift = detect_data_drift(
        reference,
        current,
        numerical_columns=NUMERICAL,
        categorical_columns=CATEGORICAL,
    )

    decision, reasons = should_retrain(
        observation_count=len(current),
        drift_report=drift,
        performance_report=None,
        policy=RetrainingPolicy(min_observations=100),
    )

    assert drift["overall_drifted"] is True
    assert decision is True
    assert reasons == ("data drift detected",)


def test_synthetic_no_drift_does_not_request_retraining() -> None:
    reference = make_reference_dataset()
    drift = detect_data_drift(
        reference,
        reference.copy(),
        numerical_columns=NUMERICAL,
        categorical_columns=CATEGORICAL,
    )

    decision, reasons = should_retrain(
        observation_count=len(reference),
        drift_report=drift,
        performance_report=None,
        policy=RetrainingPolicy(min_observations=100),
    )

    assert drift["overall_drifted"] is False
    assert decision is False
    assert reasons == ("required drift signal not present",)
