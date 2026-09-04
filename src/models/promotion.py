"""Governed model registration and promotion workflow for Unity Catalog."""

from typing import Any

import mlflow

from src.models.quality_gate import QualityGateConfig, QualityGateResult, validate_candidate
from src.models.registry import register_model, set_model_alias


def register_and_promote_candidate(
    model: Any,
    model_name: str,
    X_sample: Any,
    candidate_metrics: dict[str, Any],
    *,
    y_sample: Any = None,
    params: dict[str, Any] | None = None,
    artifacts: dict[str, str] | None = None,
    registered_model_name: str | None = None,
    production_metrics: dict[str, Any] | None = None,
    data_validation_passed: bool = True,
    model_tests_passed: bool = True,
    config: QualityGateConfig | None = None,
    alias: str = "champion",
    preprocessor: Any = None,
    signature_input: Any = None,
) -> tuple[QualityGateResult, str | None]:
    """Gate, register, package, and promote an approved candidate.

    Custom PyFunc models are serialized with CloudPickle. Because the serving
    environment is isolated from the training workspace, the project's Python
    package must be bundled with the registered model before it is deployed.
    """
    result = validate_candidate(
        candidate_metrics,
        production_metrics=production_metrics,
        data_validation_passed=data_validation_passed,
        model_tests_passed=model_tests_passed,
        config=config,
    )

    if not result.passed:
        return result, None

    registered_version = register_model(
        model=model,
        model_name=model_name,
        X_sample=X_sample,
        y_sample=y_sample,
        metrics={key: float(value) for key, value in candidate_metrics.items()},
        params=params,
        artifacts=artifacts,
        registered_model_name=registered_model_name,
        preprocessor=preprocessor,
        signature_input=signature_input,
    )

    model_uri_name = registered_model_name or model_name
    if not model_uri_name:
        raise ValueError("A registered model name is required for promotion")

    packaged_info = mlflow.models.add_libraries_to_model(
        f"models:/{model_uri_name}/{registered_version}"
    )
    packaged_version = getattr(packaged_info, "registered_model_version", None)
    if packaged_version is None:
        raise RuntimeError(
            "MLflow did not return a registered model version for the packaged serving model"
        )

    set_model_alias(model_uri_name, str(packaged_version), alias=alias)
    return result, str(packaged_version)


def promote_candidate(
    model_name: str,
    version: str,
    candidate_metrics: dict[str, Any],
    *,
    production_metrics: dict[str, Any] | None = None,
    data_validation_passed: bool = True,
    model_tests_passed: bool = True,
    config: QualityGateConfig | None = None,
    alias: str = "champion",
) -> QualityGateResult:
    """Validate an existing registered version and assign its UC alias."""
    result = validate_candidate(
        candidate_metrics,
        production_metrics=production_metrics,
        data_validation_passed=data_validation_passed,
        model_tests_passed=model_tests_passed,
        config=config,
    )

    if not result.passed:
        return result

    set_model_alias(model_name, version, alias=alias)
    return result
