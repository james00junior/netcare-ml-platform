"""Deterministic API tests for the FastAPI inference boundary."""

from api import main as api_main
from fastapi.testclient import TestClient


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
