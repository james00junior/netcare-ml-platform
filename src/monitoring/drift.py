"""
Data drift detection helpers.

Lightweight implementation; can later be swapped for Evidently or
Databricks Lakehouse Monitoring.
"""

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats


def detect_data_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    numerical_columns: Optional[List[str]] = None,
    categorical_columns: Optional[List[str]] = None,
    threshold: float = 0.15,
) -> Dict[str, Any]:
    """
    Simple drift detection using KS-test (numeric) and chi-squared (categorical).

    Returns a report with per-column drift flags and an overall drifted flag.
    """
    numerical_columns = numerical_columns or reference.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = categorical_columns or reference.select_dtypes(include=["object", "category"]).columns.tolist()

    column_reports = []
    drifted_columns = []

    for col in numerical_columns:
        if col not in current.columns:
            continue
        ref = reference[col].dropna()
        cur = current[col].dropna()
        if len(ref) < 10 or len(cur) < 10:
            continue
        stat, p_value = stats.ks_2samp(ref, cur)
        drifted = p_value < threshold
        column_reports.append(
            {
                "column": col,
                "type": "numerical",
                "statistic": float(stat),
                "p_value": float(p_value),
                "drifted": drifted,
            }
        )
        if drifted:
            drifted_columns.append(col)

    for col in categorical_columns:
        if col not in current.columns:
            continue
        ref_counts = reference[col].value_counts(normalize=True)
        cur_counts = current[col].value_counts(normalize=True)
        # Align categories
        all_cats = sorted(set(ref_counts.index) | set(cur_counts.index))
        ref_vec = np.array([ref_counts.get(c, 0) for c in all_cats])
        cur_vec = np.array([cur_counts.get(c, 0) for c in all_cats])
        # Chi-square on absolute counts approximation
        ref_abs = ref_vec * len(reference)
        cur_abs = cur_vec * len(current)
        try:
            stat, p_value = stats.chisquare(cur_abs + 1e-6, ref_abs + 1e-6)
        except (ValueError, TypeError):
            stat, p_value = 0.0, 1.0
        drifted = p_value < threshold
        column_reports.append(
            {
                "column": col,
                "type": "categorical",
                "statistic": float(stat),
                "p_value": float(p_value),
                "drifted": drifted,
            }
        )
        if drifted:
            drifted_columns.append(col)

    return {
        "n_columns_checked": len(column_reports),
        "n_drifted": len(drifted_columns),
        "drifted_columns": drifted_columns,
        "overall_drifted": len(drifted_columns) > 0,
        "threshold": threshold,
        "column_reports": column_reports,
    }
