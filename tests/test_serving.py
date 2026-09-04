"""Unit tests for production serving components."""

import pandas as pd
import pytest

from src.serving.databricks_client import DatabricksServingClient, DatabricksServingError
from src.serving.mlflow_model import ReadmissionServingModel


class FakePreprocessor:
    def __init__(self):
        self.seen = None

    def transform(self, features):
        self.seen = features.copy()
        return features[["age"]].to_numpy()


class FakeModel:
    def predict_proba(self, features):
        return [[0.2, 0.8] for _ in range(len(features))]


def test_serving_model_applies_production_preprocessing():
    preprocessor = FakePreprocessor()
    serving_model = ReadmissionServingModel(
        model=FakeModel(),
        preprocessor=preprocessor,
        drop_columns=("patient_id", "encounter_id"),
        categorical_columns=("sex", "admission_type"),
    )

    result = serving_model.predict(
        None,
        pd.DataFrame(
            [
                {
                    "patient_id": "p1",
                    "age": 65,
                    "sex": "female",
                    "admission_type": "er",
                }
            ]
        ),
    )

    assert list(result["predicted_label"]) == [1]
    assert list(result["risk_tier"]) == ["high"]
    assert "patient_id" not in preprocessor.seen.columns
    assert preprocessor.seen.loc[0, "sex"] == "Female"
    assert preprocessor.seen.loc[0, "admission_type"] == "Emergency"


def test_serving_model_rejects_empty_input():
    serving_model = ReadmissionServingModel(
        model=FakeModel(),
        preprocessor=FakePreprocessor(),
        drop_columns=(),
        categorical_columns=(),
    )

    with pytest.raises(ValueError, match="At least one record"):
        serving_model.predict(None, pd.DataFrame())


def test_databricks_client_rejects_empty_records():
    client = DatabricksServingClient("https://example.com/invocations", "token")

    with pytest.raises(ValueError, match="At least one record"):
        client.predict([])


def test_databricks_client_validates_response(monkeypatch):
    client = DatabricksServingClient("https://example.com/invocations", "token")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": []}

    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: Response())

    with pytest.raises(DatabricksServingError, match="did not contain predictions"):
        client.predict([{"age": 65}])
