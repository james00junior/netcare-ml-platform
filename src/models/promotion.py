"""Governed model promotion workflow for Unity Catalog."""

from typing import Any, Dict, Optional

from src.models.quality_gate import QualityGateConfig, QualityGateResult, validate_candidate
from src.models.registry import set_model_alias


def promote_candidate(
    model_name: str,
    version: str,
    candidate_metrics: Dict[str, Any],
    *,
    production_metrics: Optional[Dict[str, Any]] = None,
    data_validation_passed: bool = True,
    model_tests_passed: bool = True,
    config: Optional[QualityGateConfig] = None,
    alias: str = "champion",
) -> QualityGateResult:
    """Validate and promote a registered model version to a UC alias.

    Registration and promotion are intentionally separate operations. A model
    version must already exist in Unity Catalog, then this function evaluates
    the production quality gate before assigning the deployment alias.
    """
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
