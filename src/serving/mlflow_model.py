"""MLflow model wrapper for production readmission serving."""

from typing import Any

import mlflow
import numpy as np
import pandas as pd

from src.data.preprocessing import clean_identifiers_and_leakage, standardise_categoricals


class ReadmissionServingModel(mlflow.pyfunc.PythonModel):
    """Apply the fitted preprocessing pipeline before model inference."""

    def __init__(self, model: Any, preprocessor: Any):
        self.model = model
        self.preprocessor = preprocessor

    def predict(
        self,
        context: Any,
        model_input: pd.DataFrame,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Return readmission predictions for raw patient feature rows."""
        del context, params

        if not isinstance(model_input, pd.DataFrame):
            raise TypeError("Model input must be a pandas DataFrame.")
        if model_input.empty:
            raise ValueError("At least one record is required for prediction.")

        features = clean_identifiers_and_leakage(model_input)
        features = standardise_categoricals(features)
        transformed = self.preprocessor.transform(features)

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
            },
            index=model_input.index,
        )
