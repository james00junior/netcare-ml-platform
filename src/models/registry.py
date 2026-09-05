"""
Model registry helpers (MLflow).

Provides a thin abstraction so the rest of the codebase does not
depend directly on MLflow APIs. Supports Databricks Unity Catalog
with aliases for governed candidate/champion lifecycle management.
"""

from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.exceptions import MlflowException
from mlflow.models import infer_signature

from src.config import settings
from src.serving.mlflow_model import ReadmissionServingModel


# These are only fallbacks. Production artifacts build their requirements from
# the actual training environment below so sklearn/cloudpickle serialization is
# reproduced exactly by Databricks Model Serving.
MLFLOW_SERVING_REQUIREMENTS = [
    "mlflow==3.16.0",
    "pandas==3.0.5",
    "numpy==1.26.4",
    "scikit-learn==1.3.0",
    "pydantic-settings>=2.0.0",
    "scipy==1.11.1",
    "cloudpickle==3.1.2",
]


def _serving_requirements() -> list[str]:
    """Return exact versions of serialization-sensitive training dependencies.

    Databricks Model Serving creates a fresh Python environment. Pinning the
    versions from the training environment prevents sklearn/cloudpickle model
    deserialization failures caused by incompatible internal sklearn classes.
    The function intentionally covers only dependencies used by the serving
    artifact, keeping the serving environment deterministic and minimal.
    """
    requirements = [
        f"mlflow=={package_version('mlflow')}",
        f"pandas=={package_version('pandas')}",
        f"numpy=={package_version('numpy')}",
        f"scikit-learn=={package_version('scikit-learn')}",
        f"scipy=={package_version('scipy')}",
        f"cloudpickle=={package_version('cloudpickle')}",
        f"pydantic-settings=={package_version('pydantic-settings')}",
    ]
    return requirements


def register_model(
    model: Any,
    model_name: str,
    X_sample: Any,
    y_sample: Any = None,
    metrics: dict[str, float] | None = None,
    params: dict[str, Any] | None = None,
    artifacts: dict[str, str] | None = None,
    registered_model_name: str | None = None,
    preprocessor: Any = None,
    signature_input: Any = None,
) -> str:
    """Log a model and return its registered version.

    When called from an active MLflow candidate run, model registration is
    recorded as a nested run. This preserves explicit lineage from the
    candidate evaluation run to the model artifact and registered version.

    When a fitted preprocessor is supplied, the registered artifact is a
    self-contained MLflow PyFunc model. It accepts raw feature records and
    applies deterministic cleaning plus the fitted training transformer before
    calling the estimator. This is the production serving path.
    """
    del model_name, y_sample
    registered_model_name = registered_model_name or settings.registered_model_name

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_registry_uri(settings.mlflow_registry_uri)
    mlflow.set_experiment(settings.experiment_name)

    active_run = mlflow.active_run()
    with mlflow.start_run(nested=active_run is not None) as run:
        if active_run is not None:
            mlflow.set_tag("candidate_run_id", active_run.info.run_id)
            mlflow.set_tag("parent_run_id", active_run.info.run_id)
            mlflow.set_tag("lifecycle_state", "registered")

        if params:
            mlflow.log_params(params)
        if metrics:
            mlflow.log_metrics(metrics)

        if preprocessor is not None:
            serving_model = ReadmissionServingModel(
                model=model,
                preprocessor=preprocessor,
                drop_columns=(
                    "patient_id",
                    "encounter_id",
                    "admission_date",
                    "discharge_date",
                    "days_to_readmission",
                ),
                categorical_columns=(
                    "sex",
                    "admission_type",
                    "admission_source",
                    "discharge_disposition",
                    "primary_diagnosis_group",
                    "payer_type",
                ),
            )
            serving_input = signature_input if signature_input is not None else X_sample
            serving_predictions = serving_model.predict(None, serving_input)
            signature = infer_signature(serving_input, serving_predictions)

            # Databricks executes the training notebook outside the repository's
            # local working directory. Preserve the src package explicitly so
            # cloudpickle can resolve the original import path when serving.
            source_root = Path(__file__).resolve().parents[1]
            model_info = mlflow.pyfunc.log_model(
                name="model",
                python_model=serving_model,
                code_paths=[str(source_root)],
                pip_requirements=_serving_requirements(),
                signature=signature,
                input_example=serving_input.head(2) if hasattr(serving_input, "head") else None,
                registered_model_name=registered_model_name,
            )
        else:
            signature = None
            try:
                preds = model.predict(X_sample)
                signature = infer_signature(X_sample, preds)
            except (ValueError, TypeError, MlflowException):
                signature = None

            model_type = type(model).__name__
            model_log_kwargs = {
                "name": "model",
                "signature": signature,
                "registered_model_name": registered_model_name,
            }
            if "XGB" in model_type:
                model_info = mlflow.xgboost.log_model(model, **model_log_kwargs)
            else:
                model_info = mlflow.sklearn.log_model(model, **model_log_kwargs)

        if artifacts:
            for name, path in artifacts.items():
                mlflow.log_artifact(path, artifact_path=name)

        registered_version = getattr(model_info, "registered_model_version", None)
        return str(registered_version or run.info.run_id)


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
