from src.models.quality_gate import (
    QualityGateConfig,
    compare_with_production,
    evaluate_quality_gate,
    validate_candidate,
)


def test_quality_gate_passes_valid_candidate():
    result = evaluate_quality_gate(
        {"roc_auc": 0.72, "recall": 0.64},
        data_validation_passed=True,
        model_tests_passed=True,
    )
    assert result.passed
    assert all(result.checks.values())


def test_quality_gate_rejects_low_auc():
    result = evaluate_quality_gate(
        {"roc_auc": 0.69, "recall": 0.70},
    )
    assert not result.passed
    assert not result.checks["roc_auc"]


def test_quality_gate_rejects_low_recall():
    result = evaluate_quality_gate(
        {"roc_auc": 0.72, "recall": 0.59},
    )
    assert not result.passed
    assert not result.checks["recall"]


def test_candidate_must_not_regress_against_production():
    assert compare_with_production({"roc_auc": 0.72}, {"roc_auc": 0.71})
    assert not compare_with_production({"roc_auc": 0.70}, {"roc_auc": 0.71})


def test_validation_requires_data_and_model_tests():
    config = QualityGateConfig()
    result = validate_candidate(
        {"roc_auc": 0.72, "recall": 0.64},
        data_validation_passed=False,
        model_tests_passed=True,
        config=config,
    )
    assert not result.passed
    assert not result.checks["data_validation"]
