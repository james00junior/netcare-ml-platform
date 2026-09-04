"""
Model registry helpers (MLflow).

Provides a thin abstraction so the rest of the codebase does not
depend directly on MLflow APIs. Ready for Databricks Unity Catalog
or a local MLflow tracking server.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.models import infer_signature

from src.config import settings


def register_model(
    model: Any,
    model_name: str,
    X_sample: Any,
    y_sample: Any = None,
    metrics: Optional[Dict[str, float]] = None,
    params: Optional[Dict[str, Any]] = None,
    artifacts: Optional[Dict[str, str]] = None,
    registered_model_name: Optional[str] = None,
) -> str:
    """
    Log a model to MLflow and optionally register it.

    Returns the MLflow run ID.
    """
    registered_model_name = registered_model_name or settings.registered_model_name

    mlflow.set_experiment(settings.experiment_name)

    with mlflow.start_run() as run:
        if params:
            mlflow.log_params(params)
        if metrics:
            mlflow.log_metrics(metrics)

        signature = None
        try:
            preds = model.predict(X_sample)
            signature = infer_signature(X_sample, preds)
        except Exception:
            pass

        # Detect model type for the correct flavour
        model_type = type(model).__name__
        if "XGB" in model_type:
            mlflow.xgboost.log_model(
                model,
                artifact_path="model",
                signature=signature,
                registered_model_name=registered_model_name,
            )
        else:
            mlflow.sklearn.log_model(
                model,
                artifact_path="model",
                signature=signature,
                registered_model_name=registered_model_name,
            )

        if artifacts:
            for name, path in artifacts.items():
                mlflow.log_artifact(path, artifact_path=name)

        return run.info.run_id


def load_model(
    model_uri: str,
) -> Any:
    """
    Load a model from an MLflow URI.

    Examples
    --------
    - "models:/netcare-readmission-model/Production"
    - "runs:/<run_id>/model"
    """
    return mlflow.pyfunc.load_model(model_uri)


def load_model_local(path: Union[str, Path]) -> Any:
    """Load a model saved with joblib (local fallback)."""
    return joblib.load(path)


def save_model_local(model: Any, path: Union[str, Path]) -> Path:
    """Save a model with joblib."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path