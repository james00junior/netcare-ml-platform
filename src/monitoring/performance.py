"""
Model performance monitoring.
"""

from typing import Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_performance_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    y_prob: pd.Series | None = None,
) -> dict[str, float]:
    """Compute live performance metrics from scored data that has labels."""
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if y_prob is not None:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    return metrics


def check_performance_degradation(
    current_metrics: dict[str, float],
    baseline_metrics: dict[str, float],
    threshold: float = 0.05,
    primary_metric: str = "roc_auc",
) -> dict[str, Any]:
    """
    Compare current performance against a baseline (e.g. validation metrics).

    Flags degradation if the primary metric drops by more than `threshold`.
    """
    current = current_metrics.get(primary_metric)
    baseline = baseline_metrics.get(primary_metric)

    if current is None or baseline is None:
        return {
            "degraded": False,
            "reason": f"Metric '{primary_metric}' not available in both sets.",
            "current": current,
            "baseline": baseline,
        }

    drop = baseline - current
    degraded = drop > threshold

    return {
        "degraded": degraded,
        "primary_metric": primary_metric,
        "baseline": baseline,
        "current": current,
        "absolute_drop": float(drop),
        "threshold": threshold,
        "message": (
            f"{primary_metric} dropped by {drop:.4f} (threshold={threshold})"
            if degraded
            else f"{primary_metric} within acceptable range"
        ),
    }
