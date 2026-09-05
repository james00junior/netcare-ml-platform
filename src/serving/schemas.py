"""Pydantic schemas for the prediction API."""

from typing import Any

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Single patient feature payload for inference."""

    features: dict[str, Any] = Field(
        ...,
        description="Dictionary of feature name → value matching the registered model serving schema.",
        examples=[
            {
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
        ],
    )


class BatchPredictionRequest(BaseModel):
    """Batch of patients for inference."""

    records: list[dict[str, Any]] = Field(
        ...,
        description="List of feature dictionaries matching the registered model serving schema.",
    )


class PredictionResponse(BaseModel):
    """Prediction result for a single patient."""

    predicted_label: int = Field(..., description="0 = not readmitted, 1 = readmitted ≤30d")
    probability: float = Field(..., description="Probability of 30-day readmission")
    model_version: str = Field(..., description="Serving model identifier")
    risk_tier: str = Field(..., description="low / medium / high based on probability thresholds")


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
    environment: str
