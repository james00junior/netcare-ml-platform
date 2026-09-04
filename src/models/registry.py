"""
Model registry helpers (MLflow).

Provides a thin abstraction so the rest of the codebase does not
depend directly on MLflow APIs. Supports Databricks Unity Catalog
with aliases for governed candidate/champion lifecycle management.
"""

from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.exceptions import MlflowException
from mlflow.models import infer_signature

from src.config import settings


def register_model(
    model: Any,
    model_name: str,
    X_sample: Any,
    y_sample: Any = None,
    metrics: dict[str, float] | None = None,
    params: dict[str, Any] | None = None,
    artifacts: dict[str, str] | None = None,
    registered_model_name: str | None = None,
) -> str:
    """Log a model to MLflow and optionally register it in Unity Catalog."""
    del model_name, y_sample
    registered_model_name = registered_model_name or settings.registered_model_name

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_registry_uri(settings.mlflow_registry_uri)
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
        except (ValueError, TypeError, MlflowException):
            # Signature inference is optional; model logging must still proceed.
            pass

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


def load_model(model_uri: str) -> Any:
    """Load a model from an MLflow URI or Unity Catalog alias."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_registry_uri(settings.mlflow_registry_uri)
    return mlflow.pyfunc.load_model(model_uri)


def get_model_version(model_name: str, alias: str = "champion") -> str:
    """Return the model version currently assigned to a Unity Catalog alias."""
    mlflow.set_registry_uri(settings.mlflow_registry_uri)
    client = mlflow.MlflowClient()
    model_version = client.get_model_version_by_alias(model_name, alias)
    return str(model_version.version)


def set_model_alias(
    model_name: str,
    version: str | int,
    alias: str = "champion",
) -> None:
    """Assign a governed Unity Catalog alias to a registered model version."""
    mlflow.set_registry_uri(settings.mlflow_registry_uri)
    client = mlflow.MlflowClient()
    client.set_registered_model_alias(model_name, alias, str(version))


def load_model_alias(
    model_name: str | None = None,
    alias: str = "champion",
) -> Any:
    """Load the model version assigned to a Unity Catalog alias."""
    name = model_name or settings.registered_model_name
    return load_model(f"models:/{name}@{alias}")


def load_model_local(path: str | Path) -> Any:
    """Load a model saved with joblib (local fallback)."""
    return joblib.load(path)


def save_model_local(model: Any, path: str | Path) -> Path:
    """Save a model with joblib."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path
