"""
Feature engineering module.

Currently the feature set is produced by the preprocessing pipeline
(one-hot encoding of categoricals + numeric labs/flags).
This module provides a clean entry point for future feature enrichment
and Feature Store integration.
"""

import pandas as pd

from src.config.model_config import ModelConfig
from src.data.preprocessing import preprocess_data


def build_feature_matrix(
    df: pd.DataFrame,
    config: ModelConfig | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Build the feature matrix and target from raw data.

    This is the single public entry point for feature creation.
    Today it delegates to the preprocessing pipeline; later it can
    call a Databricks Feature Store or additional engineered features.

    Parameters
    ----------
    df : pd.DataFrame
        Raw hospital readmissions data.
    config : ModelConfig, optional

    Returns
    -------
    X : pd.DataFrame
    y : pd.Series
    """
    config = config or ModelConfig()
    X, y = preprocess_data(df, config)
    return X, y


def get_feature_names(X: pd.DataFrame) -> list:
    """Return ordered list of feature names."""
    return list(X.columns)
