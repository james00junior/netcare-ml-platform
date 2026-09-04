"""Deterministic API tests for the local development inference path."""

from fastapi.testclient import TestClient

from api import main as api_main


def test_root():
    with TestClient(api_main.app) as client:
        resp = client.get("/")

    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Netcare Readmission Prediction API"


def test_health_without_local_model(monkeypatch):
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


def test_predict_without_local_model(monkeypatch):
    monkeypatch.setattr(api_main.Path, "exists", lambda self: False)

    with TestClient(api_main.app) as client:
        resp = client.post(
            "/predict",
            json={"features": {"age": 65, "sex": "Female"}},
        )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "Model serving backend not available"
