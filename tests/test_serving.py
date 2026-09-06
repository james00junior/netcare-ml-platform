"""Unit tests for production serving components."""

import pandas as pd
import pytest
from pydantic import ValidationError

from src.serving.databricks_client import (
    DatabricksServingClient,
    DatabricksServingError,
)
from src.serving.mlflow_model import ReadmissionServingModel
from src.serving.schemas import PredictionRequest

VALID_FEATURES = {
    "age": 67,
    "sex": "Female",
    "admission_type": "Emergency",
    "admission_source": "Emergency Room",
    "discharge_disposition": "Home",
    "length_of_stay_days": 4,
    "icu_hours": 12,
    "num_prior_admissions_12m": 1,
    "num_ed_visits_12m": 2,
    "primary_diagnosis_group": "Circulatory",
    "secondary_diagnosis_count": 2,
    "elixhauser_score": 3,
    "wbc": 8.4,
    "has_diabetes": 1,
    "has_hypertension": 1,
    "has_ckd": 0,
    "has_copd": 0,
    "has_heart_failure": 1,
    "num_medications": 8,
    "had_surgery": 0,
    "had_icu_stay": 1,
    "discharge_to_home": 1,
    "followup_booked": 1,
    "payer_type": "Private",
    "creatinine": 1.2,
    "hemoglobin": 12.5,
    "sodium": 138.0,
    "potassium": 4.1,
}


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
    client = DatabricksServingClient("https://test.invalid/invocations", "token")

    with pytest.raises(ValueError, match="At least one record"):
        client.predict([])


def test_databricks_client_validates_response(monkeypatch):
    client = DatabricksServingClient("https://test.invalid/invocations", "token")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"unexpected": []}

    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: Response())

    with pytest.raises(DatabricksServingError, match="did not contain predictions"):
        client.predict([{"age": 65}])


def test_databricks_client_sends_request_id_without_payload_logging(monkeypatch):
    client = DatabricksServingClient("https://test.invalid/invocations", "token")
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"predictions": [{"predicted_label": 0, "probability": 0.2, "risk_tier": "low"}]}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        captured["json"] = kwargs["json"]
        return Response()

    monkeypatch.setattr("httpx.post", fake_post)

    result = client.predict([{"age": 65}], request_id="request-123")

    assert result[0]["risk_tier"] == "low"
    assert captured["url"] == "https://test.invalid/invocations"
    assert captured["headers"] == {"Authorization": "Bearer token"}
    assert captured["json"] == {"dataframe_records": [{"age": 65}]}


def test_prediction_request_accepts_canonical_contract():
    request = PredictionRequest(features=VALID_FEATURES)

    assert request.features.age == 67
    assert request.features.creatinine == 1.2


def test_prediction_request_rejects_missing_required_feature():
    invalid = VALID_FEATURES.copy()
    del invalid["age"]

    with pytest.raises(ValidationError):
        PredictionRequest(features=invalid)


def test_prediction_request_rejects_unknown_feature():
    invalid = VALID_FEATURES | {"patient_id": "p1"}

    with pytest.raises(ValidationError):
        PredictionRequest(features=invalid)


def test_prediction_request_rejects_invalid_binary_feature():
    invalid = VALID_FEATURES | {"has_diabetes": 2}

    with pytest.raises(ValidationError):
        PredictionRequest(features=invalid)
