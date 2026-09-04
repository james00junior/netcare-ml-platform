"""Tests for feature building."""

import pandas as pd
import pytest

from src.features.build_features import build_feature_matrix, get_feature_names


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "patient_id": [1, 2],
            "encounter_id": [10, 20],
            "admission_date": ["2024-01-01", "2024-01-02"],
            "discharge_date": ["2024-01-05", "2024-01-06"],
            "days_to_readmission": [None, 3],
            "age": [65, 70],
            "sex": ["Female", "Male"],
            "admission_type": ["Emergency", "Elective"],
            "admission_source": ["ER", "CLINIC"],
            "discharge_disposition": ["Home", "Home"],
            "primary_diagnosis_group": ["Cardiac", "Respiratory"],
            "payer_type": ["Medical Aid", "Private"],
            "creatinine": [1.1, 0.9],
            "hemoglobin": [13.0, 12.0],
            "sodium": [140, 138],
            "potassium": [4.0, 3.8],
            "has_diabetes": [1, 0],
            "readmitted_30d": [0, 1],
        }
    )


def test_build_feature_matrix(sample_df):
    X, y = build_feature_matrix(sample_df)
    assert len(X) == 2
    assert len(y) == 2
    assert list(y.values) == [0, 1]
    names = get_feature_names(X)
    assert isinstance(names, list)
    assert len(names) == X.shape[1]