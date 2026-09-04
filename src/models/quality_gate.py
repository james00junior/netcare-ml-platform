"""Model quality gates used before model registration or promotion."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class QualityGateConfig:
    """Minimum validation criteria for a candidate model."""

    min_roc_auc: float = 0.70
    min_recall: float = 0.60
    require_data_validation: bool = True
    require_model_tests: bool = True
    require_production_comparison: bool = True


@dataclass(frozen=True)
class QualityGateResult:
    """Auditable result of candidate-model validation."""

    passed: bool
    checks: Dict[str, bool]
    reasons: tuple[str, ...]


def evaluate_quality_gate(
    metrics: Dict[str, Any],
    *,
    data_validation_passed: bool = True,
    model_tests_passed: bool = True,
    config: Optional[QualityGateConfig] = None,
) -> QualityGateResult:
    """Validate a candidate model against explicit production criteria."""
    config = config or QualityGateConfig()

    roc_auc = float(metrics.get("roc_auc", 0.0))
    recall = float(metrics.get("recall", 0.0))

    checks = {
        "roc_auc": roc_auc >= config.min_roc_auc,
        "recall": recall >= config.min_recall,
        "data_validation": (not config.require_data_validation) or data_validation_passed,
        "model_tests": (not config.require_model_tests) or model_tests_passed,
    }

    reasons = tuple(f"{name} failed" for name, passed in checks.items() if not passed)

    return QualityGateResult(
        passed=all(checks.values()),
        checks=checks,
        reasons=reasons,
    )


def compare_with_production(
    candidate_metrics: Dict[str, Any],
    production_metrics: Optional[Dict[str, Any]],
    *,
    primary_metric: str = "roc_auc",
) -> bool:
    """Return True when the candidate is at least as good as production."""
    if production_metrics is None:
        return True

    candidate = float(candidate_metrics.get(primary_metric, float("-inf")))
    production = float(production_metrics.get(primary_metric, float("-inf")))
    return candidate >= production


def validate_candidate(
    candidate_metrics: Dict[str, Any],
    *,
    production_metrics: Optional[Dict[str, Any]] = None,
    data_validation_passed: bool = True,
    model_tests_passed: bool = True,
    config: Optional[QualityGateConfig] = None,
) -> QualityGateResult:
    """Run quality gates and reject candidates that regress against production."""
    config = config or QualityGateConfig()
    result = evaluate_quality_gate(
        candidate_metrics,
        data_validation_passed=data_validation_passed,
        model_tests_passed=model_tests_passed,
        config=config,
    )

    production_check = True
    if config.require_production_comparison and production_metrics is not None:
        production_check = compare_with_production(candidate_metrics, production_metrics)

    checks = {**result.checks, "better_than_production": production_check}
    reasons = result.reasons
    if not production_check:
        reasons = (*reasons, "candidate is worse than production")

    return QualityGateResult(
        passed=result.passed and production_check,
        checks=checks,
        reasons=reasons,
    )
