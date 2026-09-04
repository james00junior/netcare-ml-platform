"""
Inference wrapper used by the API and batch scoring jobs with MLflow tracking.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient
import numpy as np
import pandas as pd

from src.data.preprocessing import clean_identifiers_and_leakage, standardise_categoricals


class ReadmissionPredictor:
    """
    Production predictor that reuses the fitted training preprocessor.

    The preprocessor must have been fitted on training data only. This avoids
    training/inference preprocessing drift and ensures unknown categories are
    handled consistently.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        model: Any = None,
        preprocessor_path: Optional[Union[str, Path]] = None,
        preprocessor: Any = None,
        feature_columns: Optional[List[str]] = None,
        model_version: str = "local",
        experiment_name: str = "/Shared/netcare-readmission-production-inference",
    ):
        if model is not None:
            self.model = model
        elif model_path is not None:
            self.model = joblib.load(model_path)
        else:
            raise ValueError("Either model or model_path must be provided.")

        if preprocessor is not None:
            self.preprocessor = preprocessor
        elif preprocessor_path is not None:
            self.preprocessor = joblib.load(preprocessor_path)
        else:
            raise ValueError(
                "A fitted preprocessor or preprocessor_path must be provided."
            )

        if feature_columns is not None:
            self.feature_columns = feature_columns
        elif hasattr(self.preprocessor, "get_feature_names_out"):
            self.feature_columns = list(self.preprocessor.get_feature_names_out())
        elif hasattr(self.model, "feature_names_in_"):
            self.feature_columns = list(self.model.feature_names_in_)
        else:
            self.feature_columns = None

        self.model_version = model_version

        # Initialize MLflow tracking client. Prediction remains available when
        # MLflow is unavailable; logging failures are handled in _log_prediction.
        self.client = MlflowClient()
        self.experiment_name = experiment_name
        self.experiment_id = None
        try:
            experiment = self.client.get_experiment_by_name(experiment_name)
            if experiment is not None:
                self.experiment_id = experiment.experiment_id
        except (MlflowException, ValueError, TypeError):
            self.experiment_id = None

    def _prepare_features(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply the fitted training preprocessor to raw feature dictionaries."""
        if not records:
            raise ValueError("At least one record is required for prediction.")

        df = pd.DataFrame(records)
        df = clean_identifiers_and_leakage(df)
        df = standardise_categoricals(df)

        transformed = self.preprocessor.transform(df)

        if hasattr(self.preprocessor, "get_feature_names_out"):
            columns = list(self.preprocessor.get_feature_names_out())
        elif self.feature_columns is not None:
            columns = self.feature_columns
        else:
            columns = [f"feature_{i}" for i in range(transformed.shape[1])]

        return pd.DataFrame(transformed, columns=columns, index=df.index)

    def _log_prediction(self, probabilities: np.ndarray, labels: np.ndarray) -> None:
        """Log non-identifying batch inference metadata to MLflow."""
        if self.experiment_id is None:
            return

        try:
            with mlflow.start_run(
                experiment_id=self.experiment_id,
                tags={
                    "model_version": self.model_version,
                    "inference_type": "single" if len(labels) == 1 else "batch",
                },
            ):
                mlflow.log_metric("prediction_count", len(labels))
                mlflow.log_metric("mean_predicted_probability", float(probabilities.mean()))
                mlflow.log_metric("predicted_positive_rate", float(labels.mean()))
        except (MlflowException, ValueError, TypeError) as mlflow_err:
            print(f"MLflow Logging Failed: {mlflow_err}")

    def predict(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run inference on a list of patient feature dictionaries."""
        X = self._prepare_features(records)
        probs = self.model.predict_proba(X)[:, 1]
        labels = (probs >= 0.5).astype(int)

        results = [
            {
                "predicted_label": int(label),
                "probability": float(prob),
                "risk_tier": self._risk_tier(float(prob)),
                "model_version": self.model_version,
            }
            for label, prob in zip(labels, probs)
        ]

        self._log_prediction(probs, labels)
        return results

    def predict_single(self, features: Dict[str, Any]) -> Dict[str, Any]:
        return self.predict([features])[0]

    @staticmethod
    def _risk_tier(prob: float) -> str:
        if prob < 0.3:
            return "low"
        if prob < 0.6:
            return "medium"
        return "high"
