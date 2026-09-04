"""API tests (require a loaded model for full coverage)."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "model_loaded" in data


def test_predict_without_model():
    """When no model is loaded, /predict should return 503."""
    resp = client.post(
        "/predict",
        json={"features": {"age": 65, "sex": "Female"}},
    )
    # Either 503 (no model) or 200 (if a model happened to be present)
    assert resp.status_code in (200, 503)
