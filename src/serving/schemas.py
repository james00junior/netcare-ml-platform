"""Pydantic schemas for the prediction API."""

from typing import Any

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Single patient feature payload for inference."""

    features: dict[str, Any] = Field(
        ...,
        description="Dictionary of feature name → value. Must match training schema.",
        examples=[
            {
                "age": 67,
                "sex": "Female",
                "admission_type": "Emergency",
                "length_of_stay": 4,
                "creatinine": 1.2,
                "hemoglobin": 12.5,
                "has_diabetes": 1,
                "has_heart_failure": 0,
            }
        ],
    )


class BatchPredictionRequest(BaseModel):
    """Batch of patients for inference."""

    records: list[dict[str, Any]] = Field(
        ...,
        description="List of feature dictionaries.",
    )


class PredictionResponse(BaseModel):
    """Prediction result for a single patient."""

    predicted_label: int = Field(..., description="0 = not readmitted, 1 = readmitted ≤30d")
    probability: float = Field(..., description="Probability of 30-day readmission")
    model_version: str | None = None
    risk_tier: str | None = Field(
        None,
        description="low / medium / high based on probability thresholds",
    )


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
    environment: str
