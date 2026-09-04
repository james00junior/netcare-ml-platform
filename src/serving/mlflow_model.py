"""Self-contained MLflow model for raw-feature production serving."""

from typing import Any

import mlflow
import numpy as np
import pandas as pd


class ReadmissionServingModel(mlflow.pyfunc.PythonModel):
    """Apply production preprocessing and inference inside the served model."""

    def __init__(
        self,
        model: Any,
        preprocessor: Any,
        drop_columns: tuple[str, ...],
        categorical_columns: tuple[str, ...],
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.drop_columns = drop_columns
        self.categorical_columns = categorical_columns

    def _prepare_features(self, model_input: pd.DataFrame) -> Any:
        """Apply the same deterministic cleaning and fitted transformation used in training."""
        if not isinstance(model_input, pd.DataFrame):
            raise TypeError("Model input must be a pandas DataFrame.")
        if model_input.empty:
            raise ValueError("At least one record is required for prediction.")

        features = model_input.copy()
        features = features.drop(
            columns=[column for column in self.drop_columns if column in features.columns]
        )

        if "admission_type" in features.columns:
            features["admission_type"] = (
                features["admission_type"]
                .astype("string")
                .str.strip()
                .str.title()
                .replace({"Er": "Emergency"})
            )
        if "admission_source" in features.columns:
            features["admission_source"] = (
                features["admission_source"].astype("string").str.strip().str.upper()
            )
        for column in self.categorical_columns:
            if column in features.columns and column not in {"admission_type", "admission_source"}:
                features[column] = features[column].astype("string").str.strip().str.title()

        return self.preprocessor.transform(features)

    def predict(
        self,
        context: Any,
        model_input: pd.DataFrame,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Return labels, probabilities and risk tiers for raw patient feature rows."""
        del context, params

        transformed = self._prepare_features(model_input)
        probabilities = np.asarray(self.model.predict_proba(transformed))[:, 1]
        labels = (probabilities >= 0.5).astype(int)
        risk_tiers = np.select(
            [probabilities < 0.3, probabilities < 0.6],
            ["low", "medium"],
            default="high",
        )

        return pd.DataFrame(
            {
                "predicted_label": labels.astype(int),
                "probability": probabilities.astype(float),
                "risk_tier": risk_tiers,
                "model_version": "champion",
            },
            index=model_input.index,
        )
