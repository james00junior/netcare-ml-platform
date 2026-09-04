"""
Inference wrapper used by the API and batch scoring jobs with MLflow tracking.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

import joblib
import mlflow
from mlflow.tracking import MlflowClient
import numpy as np
import pandas as pd

from src.config import settings
from src.config.model_config import ModelConfig
from src.data.preprocessing import standardise_categoricals, impute_lab_values


class ReadmissionPredictor:
    """
    Production predictor that applies the same preprocessing
    used at training time, returns calibrated risk scores, and logs to MLflow.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        model: Any = None,
        feature_columns: Optional[List[str]] = None,
        model_version: str = "local",
        experiment_name: str = "/Shared/netcare-readmission-production-inference"
    ):
        if model is not None:
            self.model = model
        elif model_path is not None:
            self.model = joblib.load(model_path)
        else:
            raise ValueError("Either model or model_path must be provided.")

        if feature_columns is not None:
            self.feature_columns = feature_columns
        elif hasattr(self.model, "feature_names_in_"):
            self.feature_columns = list(self.model.feature_names_in_)
        else:
            self.feature_columns = None

        self.model_version = model_version
        self.config = ModelConfig()

        # --- Initialize MLflow Tracking Client ---
        # It reads MLFLOW_TRACKING_URI from your system environment defaults if set
        self.client = MlflowClient()
        try:
            self.experiment_id = self.client.get_experiment_by_name(experiment_name).experiment_id
        except Exception:
            self.experiment_id = self.client.create_experiment(experiment_name)

    def _prepare_features(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Apply training-time preprocessing to raw feature dicts."""
        df = pd.DataFrame(records)

        # Apply same categorical standardisation
        df = standardise_categoricals(df)
        df = impute_lab_values(df, self.config.lab_columns)

        # One-hot encode (must match training columns)
        cat_cols = [c for c in self.config.categorical_columns if c in df.columns]
        df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=False, dtype=int)

        # Align to training feature set
        if self.feature_columns is not None:
            for col in self.feature_columns:
                if col not in df_encoded.columns:
                    df_encoded[col] = 0
            df_encoded = df_encoded[self.feature_columns]

        return df_encoded

    def predict(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run inference on a list of patient feature dictionaries and log runs to MLflow.
        """
        X = self._prepare_features(records)
        probs = self.model.predict_proba(X)[:, 1]
        labels = (probs >= 0.5).astype(int)

        results = []
        for i, (label, prob) in enumerate(zip(labels, probs)):
            risk = self._risk_tier(prob)
            results.append(
                {
                    "predicted_label": int(label),
                    "probability": float(prob),
                    "risk_tier": risk,
                    "model_version": self.model_version,
                }
            )

            # --- Log individual prediction metadata to MLflow ---
            try:
                # Create a unique tracking run for this inference cycle
                run = self.client.create_run(
                    experiment_id=self.experiment_id, 
                    tags={
                        "model_version": self.model_version,
                        "inference_type": "single" if len(records) == 1 else "batch",
                        "request_id": str(uuid.uuid4())
                    }
                )
                
                # Log critical input features as parameters
                raw_record = records[i]
                for key, val in raw_record.items():
                    # Flatten or truncate feature values safely for MLflow string params
                    self.client.log_param(run.info.run_id, f"input_{key}", str(val))
                
                # Log outputs as metrics
                self.client.log_metric(run.info.run_id, "predicted_probability", float(prob))
                self.client.log_metric(run.info.run_id, "predicted_label", int(label))
                self.client.set_tag(run.info.run_id, "risk_tier", risk)
                
                # Terminate the active prediction run safely
                self.client.set_terminated(run.info.run_id)
            except Exception as mlflow_err:
                # Gracefully catch errors so API calls don't crash if MLflow server is down
                print(f"MLflow Logging Failed: {mlflow_err}")

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
