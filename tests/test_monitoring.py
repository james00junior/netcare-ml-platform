"""Unit tests for the Phase 11 monitoring primitives."""

import pandas as pd

from src.monitoring.drift import detect_data_drift
from src.monitoring.performance import (
    check_performance_degradation,
    compute_performance_metrics,
)


def test_performance_metrics_are_reproducible() -> None:
    y_true = pd.Series([0, 1, 1, 0])
    y_pred = pd.Series([0, 1, 0, 0])
    y_prob = pd.Series([0.1, 0.9, 0.4, 0.2])

    metrics = compute_performance_metrics(y_true, y_pred, y_prob)

    assert metrics["accuracy"] == 0.75
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["f1_score"] == 2 / 3
    assert 0.0 <= metrics["roc_auc"] <= 1.0


def test_performance_degradation_compares_explicit_baseline() -> None:
    result = check_performance_degradation(
        current_metrics={"roc_auc": 0.72},
        baseline_metrics={"roc_auc": 0.80},
        threshold=0.05,
    )

    assert result["degraded"] is True
    assert result["primary_metric"] == "roc_auc"
    assert result["absolute_drop"] == 0.08


def test_identical_reference_and_current_data_are_not_drifted() -> None:
    reference = pd.DataFrame(
        {
            "age": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
            "sex": ["F", "M"] * 5,
        }
    )
    current = reference.copy()

    result = detect_data_drift(
        reference,
        current,
        numerical_columns=["age"],
        categorical_columns=["sex"],
        threshold=0.05,
    )

    assert result["overall_drifted"] is False
    assert result["n_columns_checked"] == 2


def test_drift_report_skips_missing_current_columns() -> None:
    reference = pd.DataFrame({"age": [20, 25, 30, 35, 40]})
    current = pd.DataFrame({"other": [1, 2, 3, 4, 5]})

    result = detect_data_drift(
        reference,
        current,
        numerical_columns=["age"],
        categorical_columns=[],
        threshold=0.05,
    )

    assert result["n_columns_checked"] == 0
    assert result["overall_drifted"] is False
