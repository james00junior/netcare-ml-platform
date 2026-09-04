"""
Data preprocessing and preparation.

Extracted and refactored from deliverable_2_data_preparation.py.
"""

from typing import Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import settings
from src.config.model_config import ModelConfig


def clean_identifiers_and_leakage(
    df: pd.DataFrame,
    drop_columns: Optional[Tuple[str, ...]] = None,
) -> pd.DataFrame:
    """Drop identifier and leakage columns."""
    cfg = ModelConfig()
    cols = drop_columns or cfg.drop_columns
    to_drop = [c for c in cols if c in df.columns]
    return df.drop(columns=to_drop)


def standardise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise categorical value casing and known inconsistencies.
    Logic from deliverable_2.
    """
    df = df.copy()

    # admission_type: title case + map Er → Emergency
    if "admission_type" in df.columns:
        df["admission_type"] = (
            df["admission_type"]
            .astype(str)
            .str.strip()
            .str.title()
            .replace({"Er": "Emergency"})
        )

    # admission_source: uppercase
    if "admission_source" in df.columns:
        df["admission_source"] = (
            df["admission_source"].astype(str).str.strip().str.upper()
        )

    # Remaining categoricals → title case
    for col in ["sex", "discharge_disposition", "primary_diagnosis_group", "payer_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()

    return df


def impute_lab_values(
    df: pd.DataFrame,
    lab_columns: Optional[Tuple[str, ...]] = None,
) -> pd.DataFrame:
    """Median imputation for laboratory columns."""
    cfg = ModelConfig()
    labs = lab_columns or cfg.lab_columns
    df = df.copy()

    for col in labs:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    return df


def encode_features(
    df: pd.DataFrame,
    target_column: str = "readmitted_30d",
    categorical_columns: Optional[Tuple[str, ...]] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    One-hot encode categorical features and separate target.

    Returns
    -------
    X_encoded : pd.DataFrame
    y : pd.Series
    """
    cfg = ModelConfig()
    cat_cols = list(categorical_columns or cfg.categorical_columns)
    cat_cols = [c for c in cat_cols if c in df.columns]

    y = df[target_column].astype(int)
    X = df.drop(columns=[target_column])

    X_encoded = pd.get_dummies(
        X,
        columns=cat_cols,
        drop_first=False,
        dtype=int,
    )
    return X_encoded, y


def preprocess_data(
    df: pd.DataFrame,
    config: Optional[ModelConfig] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Full preprocessing pipeline (clean → standardise → impute → encode).

    Returns
    -------
    X : pd.DataFrame  (encoded features)
    y : pd.Series     (target)
    """
    config = config or ModelConfig()

    df = clean_identifiers_and_leakage(df, config.drop_columns)
    df = standardise_categoricals(df)
    df = impute_lab_values(df, config.lab_columns)
    X, y = encode_features(df, config.target_column, config.categorical_columns)

    return X, y


def train_test_split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: Optional[float] = None,
    random_state: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified train/test split."""
    test_size = test_size if test_size is not None else settings.test_size
    random_state = random_state if random_state is not None else settings.random_state

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )


if __name__ == "__main__":
    from src.data.ingestion import load_raw_data, save_processed_data

    df = load_raw_data()
    print("Original shape:", df.shape)

    X, y = preprocess_data(df)
    print("After preprocessing:", X.shape, y.shape)

    X_train, X_test, y_train, y_test = train_test_split_data(X, y)
    print(f"Train: {X_train.shape} | Test: {X_test.shape}")
    print(f"Train target rate: {y_train.mean():.3f} | Test: {y_test.mean():.3f}")

    save_processed_data(X_train, "X_train")
    save_processed_data(X_test, "X_test")
    save_processed_data(y_train.to_frame(), "y_train")
    save_processed_data(y_test.to_frame(), "y_test")
    print("Processed datasets saved.")