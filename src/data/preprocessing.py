"""
Data preprocessing and preparation.

Leakage-safe preprocessing for the Netcare readmission model.

The preprocessing workflow is:

    raw data
        ↓
    remove identifiers / known leakage
        ↓
    train/test split
        ↓
    fit preprocessing on training data only
        ↓
    transform train and test with the same fitted transformer
"""

from typing import Optional, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import settings
from src.config.model_config import ModelConfig


def clean_identifiers_and_leakage(
    df: pd.DataFrame,
    drop_columns: Optional[Tuple[str, ...]] = None,
) -> pd.DataFrame:
    """Drop identifier and known leakage columns."""
    cfg = ModelConfig()
    cols = drop_columns or cfg.drop_columns
    to_drop = [c for c in cols if c in df.columns]
    return df.drop(columns=to_drop)


def standardise_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise categorical value casing and known inconsistencies.

    This transformation does not learn statistics from the data, so it
    can safely be applied before the train/test split.
    """
    df = df.copy()

    if "admission_type" in df.columns:
        df["admission_type"] = (
            df["admission_type"]
            .astype("string")
            .str.strip()
            .str.title()
            .replace({"Er": "Emergency"})
        )

    if "admission_source" in df.columns:
        df["admission_source"] = (
            df["admission_source"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

    for col in [
        "sex",
        "discharge_disposition",
        "primary_diagnosis_group",
        "payer_type",
    ]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.title()
            )

    return df


def impute_lab_values(
    df: pd.DataFrame,
    lab_columns: Optional[Tuple[str, ...]] = None,
) -> pd.DataFrame:
    """
    Legacy helper for direct dataframe preprocessing.

    For model training, use build_preprocessor() so that imputation
    statistics are fitted on training data only.
    """
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
    Legacy helper for direct dataframe encoding.

    For model training, use build_preprocessor() so that the encoder
    is fitted on training data only.
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


def build_preprocessor(
    X: pd.DataFrame,
    config: Optional[ModelConfig] = None,
) -> ColumnTransformer:
    """
    Build a leakage-safe sklearn preprocessing transformer.

    The returned transformer must be fitted on training data only.
    Numeric imputation therefore learns medians only from X_train.
    OneHotEncoder learns its categories only from X_train.
    """
    config = config or ModelConfig()

    categorical_columns = [
        col for col in config.categorical_columns if col in X.columns
    ]

    numeric_columns = [
        col for col in X.columns if col not in categorical_columns
    ]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                    dtype=int,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def prepare_train_test_data(
    df: pd.DataFrame,
    config: Optional[ModelConfig] = None,
):
    """
    Prepare raw data using a leakage-safe train/test workflow.

    Returns
    -------
    preprocessor
        Fitted sklearn ColumnTransformer.

    X_train
        Transformed training features.

    X_test
        Transformed test features.

    y_train
        Training target.

    y_test
        Test target.
    """
    config = config or ModelConfig()

    df = clean_identifiers_and_leakage(
        df,
        config.drop_columns,
    )

    df = standardise_categoricals(df)

    if config.target_column not in df.columns:
        raise ValueError(
            f"Target column '{config.target_column}' not found in dataset."
        )

    y = df[config.target_column].astype(int)
    X = df.drop(columns=[config.target_column])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )

    preprocessor = build_preprocessor(
        X_train,
        config,
    )

    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)

    feature_names = preprocessor.get_feature_names_out()

    X_train_transformed = pd.DataFrame(
        X_train_transformed,
        columns=feature_names,
        index=X_train.index,
    )

    X_test_transformed = pd.DataFrame(
        X_test_transformed,
        columns=feature_names,
        index=X_test.index,
    )

    return (
        preprocessor,
        X_train_transformed,
        X_test_transformed,
        y_train,
        y_test,
    )


def preprocess_data(
    df: pd.DataFrame,
    config: Optional[ModelConfig] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Backwards-compatible full preprocessing helper.

    NOTE:
        This helper is retained for existing callers and exploratory use.
        Model training should use prepare_train_test_data() to prevent
        train/test leakage.
    """
    config = config or ModelConfig()

    df = clean_identifiers_and_leakage(
        df,
        config.drop_columns,
    )
    df = standardise_categoricals(df)
    X, y = encode_features(
        df,
        config.target_column,
        config.categorical_columns,
    )

    return X, y


def train_test_split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: Optional[float] = None,
    random_state: Optional[int] = None,
):
    """Stratified train/test split for already-prepared data."""
    test_size = (
        test_size
        if test_size is not None
        else settings.test_size
    )

    random_state = (
        random_state
        if random_state is not None
        else settings.random_state
    )

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
