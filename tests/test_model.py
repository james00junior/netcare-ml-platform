"""Tests for model training and evaluation."""

import pandas as pd
import pytest
from sklearn.datasets import make_classification

from src.models.evaluate import compute_metrics
from src.models.train_baseline import predict_baseline, train_baseline_model
from src.models.train_gbdt import predict_gbdt, train_gbdt_model


@pytest.fixture
def synthetic_data():
    """Synthetic data for unit tests (does not use the real hospital CSV)."""
    X, y = make_classification(
        n_samples=200,
        n_features=10,
        n_informative=6,
        n_redundant=2,
        random_state=42,
        weights=[0.7, 0.3],
    )
    X = pd.DataFrame(X, columns=[f"f{i}" for i in range(10)])
    y = pd.Series(y, name="target")
    return X, y


def test_train_baseline(synthetic_data):
    X, y = synthetic_data
    model = train_baseline_model(X, y)
    preds, probs = predict_baseline(model, X)
    assert len(preds) == len(X)
    assert len(probs) == len(X)
    assert set(preds.unique()).issubset({0, 1})
    assert probs.min() >= 0 and probs.max() <= 1


def test_train_gbdt(synthetic_data):
    X, y = synthetic_data
    model = train_gbdt_model(X, y)
    preds, probs = predict_gbdt(model, X)
    assert len(preds) == len(X)
    assert set(preds.unique()).issubset({0, 1})
    assert 0 <= probs.min() <= probs.max() <= 1


def test_compute_metrics(synthetic_data):
    X, y = synthetic_data
    model = train_baseline_model(X, y)
    preds, probs = predict_baseline(model, X)
    metrics = compute_metrics(y, preds, probs, model_name="test")
    assert "accuracy" in metrics
    assert "roc_auc" in metrics
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["roc_auc"] <= 1
