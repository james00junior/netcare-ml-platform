"""Deterministic API tests for the FastAPI inference boundary."""

from fastapi.testclient import TestClient

from api import main as api_main


SAMPLE_FEATURES = {
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
    "creatinine": 1.2,
    "hemoglobin": 12.5,
    "wbc": 8.4,
    "sodium": 138.0,
    "potassium": 4.1,
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
}


def test_root():
    with TestClient(api_main.app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "Netcare Readmission Prediction API"


def test_health_without_backend(monkeypatch):
    monkeypatch.setattr(api_main.settings, "databricks_serving_endpoint", None)
    monkeypatch.setattr(api_main.settings, "databricks_serving_token", None)
    monkeypatch.setattr(api_main.Path, "exists", lambda self: False)
    with TestClient(api_main.app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "degraded",
        "model_loaded": False,
        "model_version": None,
        "environment": "dev",
    }


def test_predict_without_backend(monkeypatch):
    monkeypatch.setattr(api_main.settings, "databricks_serving_endpoint", None)
    monkeypatch.setattr(api_main.settings, "databricks_serving_token", None)
    monkeypatch.setattr(api_main.Path, "exists", lambda self: False)
    with TestClient(api_main.app) as client:
        resp = client.post("/v1/predictions/readmission", json={"features": SAMPLE_FEATURES})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "Model serving backend not available"


def test_versioned_prediction_uses_databricks_backend(monkeypatch):
    class FakeDatabricksServingClient:
        def __init__(self, endpoint_url, token, timeout):
            assert endpoint_url == "https://example.test/invocations"
            assert token == "stub"
            assert timeout == 30.0

        def predict(self, records):
            assert records == [SAMPLE_FEATURES]
            return [{
                "predicted_label": 0,
                "probability": 0.30573779349128066,
                "risk_tier": "medium",
                "model_version": "champion",
            }]

    monkeypatch.setattr(api_main.settings, "databricks_serving_endpoint", "https://example.test/invocations")
    monkeypatch.setattr(api_main.settings, "databricks_serving_token", "stub")
    monkeypatch.setattr(api_main, "DatabricksServingClient", FakeDatabricksServingClient)
    with TestClient(api_main.app) as client:
        resp = client.post("/v1/predictions/readmission", json={"features": SAMPLE_FEATURES})
    assert resp.status_code == 200
    assert resp.json() == {
        "predicted_label": 0,
        "probability": 0.30573779349128066,
        "risk_tier": "medium",
        "model_version": "champion",
    }


def test_versioned_batch_prediction_uses_databricks_backend(monkeypatch):
    class FakeDatabricksServingClient:
        def __init__(self, endpoint_url, token, timeout):
            pass

        def predict(self, records):
            assert records == [SAMPLE_FEATURES, SAMPLE_FEATURES]
            return [
                {"predicted_label": 0, "probability": 0.30, "risk_tier": "medium", "model_version": "champion"},
                {"predicted_label": 1, "probability": 0.82, "risk_tier": "high", "model_version": "champion"},
            ]

    monkeypatch.setattr(api_main.settings, "databricks_serving_endpoint", "https://example.test/invocations")
    monkeypatch.setattr(api_main.settings, "databricks_serving_token", "stub")
    monkeypatch.setattr(api_main, "DatabricksServingClient", FakeDatabricksServingClient)
    with TestClient(api_main.app) as client:
        resp = client.post("/v1/predictions/readmission/batch", json={"records": [SAMPLE_FEATURES, SAMPLE_FEATURES]})
    assert resp.status_code == 200
    assert resp.json() == {"predictions": [
        {"predicted_label": 0, "probability": 0.30, "risk_tier": "medium", "model_version": "champion"},
        {"predicted_label": 1, "probability": 0.82, "risk_tier": "high", "model_version": "champion"},
    ]}
