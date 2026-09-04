"""Tests for data ingestion, validation and preprocessing."""

import pandas as pd
import pytest

from src.data.preprocessing import (
    clean_identifiers_and_leakage,
    impute_lab_values,
    preprocess_data,
    standardise_categoricals,
)
from src.data.validation import run_data_quality_checks


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": [1, 2, 3, 4],
            "encounter_id": [10, 20, 30, 40],
            "admission_date": ["2024-01-01"] * 4,
            "discharge_date": ["2024-01-05"] * 4,
            "days_to_readmission": [10, None, 5, None],
            "age": [65, 70, 55, 80],
            "sex": ["female", "Male", "FEMALE", "male"],
            "admission_type": ["Emergency", "er", "Elective", "Urgent"],
            "admission_source": ["er", "Clinic", "er", "Transfer"],
            "discharge_disposition": ["home", "Home", "snf", "Home"],
            "primary_diagnosis_group": ["Cardiac", "respiratory", "Cardiac", "Other"],
            "payer_type": ["medical aid", "Private", "medical aid", "Government"],
            "creatinine": [1.1, None, 0.9, 1.4],
            "hemoglobin": [13.0, 12.0, None, 11.5],
            "sodium": [140, 138, 142, None],
            "potassium": [4.0, 3.8, 4.2, 4.1],
            "has_diabetes": [1, 0, 1, 0],
            "readmitted_30d": [0, 1, 0, 1],
        }
    )


def test_clean_identifiers_and_leakage(sample_df):
    cleaned = clean_identifiers_and_leakage(sample_df)
    assert "patient_id" not in cleaned.columns
    assert "encounter_id" not in cleaned.columns
    assert "days_to_readmission" not in cleaned.columns
    assert "age" in cleaned.columns


def test_standardise_categoricals(sample_df):
    std = standardise_categoricals(sample_df)
    assert set(std["sex"].unique()) <= {"Female", "Male"}
    assert "Emergency" in std["admission_type"].values
    assert (
        "ER" in std["admission_source"].str.upper().values
        or "Er" not in std["admission_type"].values
    )


def test_impute_lab_values(sample_df):
    imputed = impute_lab_values(sample_df)
    assert imputed["creatinine"].isnull().sum() == 0
    assert imputed["hemoglobin"].isnull().sum() == 0
    assert imputed["sodium"].isnull().sum() == 0


def test_preprocess_pipeline(sample_df):
    X, y = preprocess_data(sample_df)
    assert len(X) == len(y) == 4
    assert y.dtype == int or str(y.dtype).startswith("int")
    assert "readmitted_30d" not in X.columns


def test_data_quality_report(sample_df):
    report = run_data_quality_checks(sample_df)
    assert report.n_rows == 4
    assert report.n_columns == sample_df.shape[1]
    assert isinstance(report.missing_values, dict)
    assert isinstance(report.outliers, list)
