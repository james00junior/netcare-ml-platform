"""Governed model registration and promotion workflow for Unity Catalog."""

from typing import Any

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
) -> tuple[QualityGateResult, str | None]:
    """Gate a candidate, register it only when approved, then promote it."""
    result = validate_candidate(
        candidate_metrics,
        production_metrics=production_metrics,
        data_validation_passed=data_validation_passed,
        model_tests_passed=model_tests_passed,
        config=config,
    )

    if not result.passed:
        return result, None

    run_id = register_model(
        model=model,
        model_name=model_name,
        X_sample=X_sample,
        y_sample=y_sample,
        metrics={key: float(value) for key, value in candidate_metrics.items()},
        params=params,
        artifacts=artifacts,
        registered_model_name=registered_model_name,
    )

    model_uri_name = registered_model_name or model_name
    if not model_uri_name:
        raise ValueError("A registered model name is required for promotion")

    set_model_alias(model_uri_name, run_id, alias=alias)
    return result, run_id


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
