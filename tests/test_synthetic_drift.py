"""Tests for the deterministic synthetic Phase 12 drift scenarios."""

from src.monitoring.drift import detect_data_drift
from src.retraining.synthetic import make_reference_dataset, make_shifted_dataset


def test_reference_dataset_is_deterministic() -> None:
    first = make_reference_dataset()
    second = make_reference_dataset()
    assert first.equals(second)


def test_shifted_dataset_is_deterministic() -> None:
    first = make_shifted_dataset()
    second = make_shifted_dataset()
    assert first.equals(second)


def test_reference_against_reference_has_no_drift() -> None:
    reference = make_reference_dataset()
    report = detect_data_drift(
        reference,
        reference.copy(),
        numerical_columns=["age", "creatinine", "hemoglobin", "sodium", "potassium"],
        categorical_columns=["sex", "admission_type", "admission_source"],
    )
    assert report["overall_drifted"] is False
    assert report["n_drifted"] == 0


def test_shifted_population_has_drift() -> None:
    reference = make_reference_dataset()
    shifted = make_shifted_dataset()
    report = detect_data_drift(
        reference,
        shifted,
        numerical_columns=["age", "creatinine", "hemoglobin", "sodium", "potassium"],
        categorical_columns=["sex", "admission_type", "admission_source"],
    )
    assert report["overall_drifted"] is True
    assert report["n_drifted"] > 0
