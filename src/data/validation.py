"""
Data quality validation.

Extracted and refactored from deliverable_1_data_quality.py.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class DataQualityReport:
    """Structured data quality assessment report."""

    n_rows: int
    n_columns: int
    columns: list[str]
    missing_values: dict[str, dict[str, float]] = field(default_factory=dict)
    duplicate_rows: int = 0
    duplicate_patient_ids: int = 0
    duplicate_encounter_ids: int = 0
    outliers: list[dict[str, Any]] = field(default_factory=list)
    categorical_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_rows": self.n_rows,
            "n_columns": self.n_columns,
            "columns": self.columns,
            "missing_values": self.missing_values,
            "duplicate_rows": self.duplicate_rows,
            "duplicate_patient_ids": self.duplicate_patient_ids,
            "duplicate_encounter_ids": self.duplicate_encounter_ids,
            "outliers": self.outliers,
            "categorical_summary": self.categorical_summary,
            "warnings": self.warnings,
        }

    def print_report(self) -> None:
        print("=" * 60)
        print("DATA QUALITY ASSESSMENT REPORT")
        print("=" * 60)
        print(f"\nDataset shape: {self.n_rows} rows, {self.n_columns} columns")
        print(f"\nColumn names:\n{self.columns}")

        print("\n" + "=" * 60)
        print("1. MISSING VALUES")
        print("=" * 60)
        if self.missing_values:
            for col, info in self.missing_values.items():
                print(f"  {col}: {info['count']} ({info['pct']}%)")
            print(f"\nTotal columns with missing values: {len(self.missing_values)}")
        else:
            print("No missing values found.")

        print("\n" + "=" * 60)
        print("2. DUPLICATE RECORDS")
        print("=" * 60)
        print(f"Fully duplicate rows: {self.duplicate_rows}")
        print(f"Duplicate patient_id values: {self.duplicate_patient_ids}")
        print(f"Duplicate encounter_id values: {self.duplicate_encounter_ids}")

        print("\n" + "=" * 60)
        print("3. OUTLIERS (IQR method, 1.5 * IQR)")
        print("=" * 60)
        if self.outliers:
            for o in self.outliers:
                print(
                    f"  {o['column']}: {o['n_outliers']} outliers "
                    f"({o['pct_outliers']}%) "
                    f"[{o['lower_bound']}, {o['upper_bound']}] "
                    f"range=[{o['min']}, {o['max']}]"
                )
            print(f"\nColumns with outliers: {len(self.outliers)}")
        else:
            print("No outliers detected by IQR method.")

        print("\n" + "=" * 60)
        print("4. CATEGORICAL VALUE INSPECTION")
        print("=" * 60)
        for col, info in self.categorical_summary.items():
            print(f"\n{col} ({info['n_unique']} unique values):")
            print(f"  Values: {info['values']}")
            if info.get("case_inconsistency"):
                print("  WARNING: Possible case/whitespace inconsistencies detected.")
            if info.get("n_missing", 0) > 0:
                print(f"  Note: {info['n_missing']} missing values.")

        if self.warnings:
            print("\n" + "=" * 60)
            print("WARNINGS")
            print("=" * 60)
            for w in self.warnings:
                print(f"  - {w}")

        print("\n" + "=" * 60)
        print("END OF DATA QUALITY ASSESSMENT")
        print("=" * 60)


def _check_missing(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    result = {}
    for col in missing[missing > 0].index:
        result[col] = {
            "count": int(missing[col]),
            "pct": float(missing_pct[col]),
        }
    return result


def _check_duplicates(df: pd.DataFrame) -> dict[str, int]:
    result = {
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_patient_ids": 0,
        "duplicate_encounter_ids": 0,
    }
    if "patient_id" in df.columns:
        result["duplicate_patient_ids"] = int(df["patient_id"].duplicated().sum())
    if "encounter_id" in df.columns:
        result["duplicate_encounter_ids"] = int(df["encounter_id"].duplicated().sum())
    return result


def _check_outliers(
    df: pd.DataFrame,
    exclude: list[str] | None = None,
) -> list[dict[str, Any]]:
    exclude = exclude or [
        "readmitted_30d",
        "days_to_readmission",
        "has_diabetes",
        "has_hypertension",
        "has_ckd",
        "has_copd",
        "has_heart_failure",
        "had_surgery",
        "had_icu_stay",
        "discharge_to_home",
        "followup_booked",
    ]
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in exclude]

    outlier_summary = []
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        n_out = int(((df[col] < lower) | (df[col] > upper)).sum())
        if n_out > 0:
            outlier_summary.append(
                {
                    "column": col,
                    "n_outliers": n_out,
                    "pct_outliers": round(n_out / len(df) * 100, 2),
                    "lower_bound": round(float(lower), 2),
                    "upper_bound": round(float(upper), 2),
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2),
                }
            )
    return sorted(outlier_summary, key=lambda x: x["n_outliers"], reverse=True)


def _check_categoricals(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    summary = {}
    for col in cat_cols:
        vals = df[col].dropna().unique()
        sorted_vals = (
            sorted(vals.tolist()) if len(vals) < 20 else sorted(vals.tolist())[:15] + ["..."]
        )
        stripped = df[col].dropna().astype(str).str.strip().str.lower()
        case_inconsistency = stripped.nunique() < df[col].dropna().nunique()
        summary[col] = {
            "n_unique": len(vals),
            "values": sorted_vals,
            "case_inconsistency": case_inconsistency,
            "n_missing": int(df[col].isna().sum()),
        }
    return summary


def run_data_quality_checks(df: pd.DataFrame) -> DataQualityReport:
    """
    Run the full data quality assessment (logic from deliverable_1).

    Parameters
    ----------
    df : pd.DataFrame
        Raw or intermediate dataset.

    Returns
    -------
    DataQualityReport
    """
    missing = _check_missing(df)
    dups = _check_duplicates(df)
    outliers = _check_outliers(df)
    cats = _check_categoricals(df)

    warnings = []
    if missing:
        warnings.append(f"{len(missing)} column(s) contain missing values.")
    if dups["duplicate_rows"] > 0:
        warnings.append(f"{dups['duplicate_rows']} fully duplicate rows found.")
    for col, info in cats.items():
        if info.get("case_inconsistency"):
            warnings.append(f"Possible case/whitespace inconsistency in '{col}'.")

    return DataQualityReport(
        n_rows=len(df),
        n_columns=df.shape[1],
        columns=list(df.columns),
        missing_values=missing,
        duplicate_rows=dups["duplicate_rows"],
        duplicate_patient_ids=dups["duplicate_patient_ids"],
        duplicate_encounter_ids=dups["duplicate_encounter_ids"],
        outliers=outliers,
        categorical_summary=cats,
        warnings=warnings,
    )


if __name__ == "__main__":
    from src.data.ingestion import load_raw_data

    df = load_raw_data()
    report = run_data_quality_checks(df)
    report.print_report()
