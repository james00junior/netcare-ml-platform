"""Tests for governed model promotion."""

from unittest.mock import patch

from src.models.promotion import promote_candidate


@patch("src.models.promotion.set_model_alias")
def test_promote_candidate_assigns_champion_when_gate_passes(mock_set_alias):
    result = promote_candidate(
        "nectare.ml.readmission_model",
        "4",
        {"roc_auc": 0.72, "recall": 0.64},
        production_metrics={"roc_auc": 0.71, "recall": 0.63},
    )

    assert result.passed
    assert result.checks["better_than_production"]
    mock_set_alias.assert_called_once_with("nectare.ml.readmission_model", "4", alias="champion")


@patch("src.models.promotion.set_model_alias")
def test_promote_candidate_rejects_regression(mock_set_alias):
    result = promote_candidate(
        "nectare.ml.readmission_model",
        "5",
        {"roc_auc": 0.70, "recall": 0.64},
        production_metrics={"roc_auc": 0.71, "recall": 0.63},
    )

    assert not result.passed
    assert not result.checks["better_than_production"]
    mock_set_alias.assert_not_called()


@patch("src.models.promotion.set_model_alias")
def test_promote_candidate_rejects_failed_quality_gate(mock_set_alias):
    result = promote_candidate(
        "nectare.ml.readmission_model",
        "6",
        {"roc_auc": 0.69, "recall": 0.64},
        production_metrics={"roc_auc": 0.68, "recall": 0.63},
    )

    assert not result.passed
    assert not result.checks["roc_auc"]
    mock_set_alias.assert_not_called()
