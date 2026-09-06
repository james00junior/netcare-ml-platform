"""Pydantic schemas for the versioned prediction API contract."""

from pydantic import BaseModel, ConfigDict, Field


class ReadmissionFeatures(BaseModel):
    """Canonical 28-field input contract for the registered readmission model."""

    model_config = ConfigDict(extra="forbid")

    age: int = Field(..., ge=0, description="Patient age in years")
    sex: str
    admission_type: str
    admission_source: str
    discharge_disposition: str
    length_of_stay_days: float = Field(..., ge=0)
    icu_hours: float = Field(..., ge=0)
    num_prior_admissions_12m: int = Field(..., ge=0)
    num_ed_visits_12m: int = Field(..., ge=0)
    primary_diagnosis_group: str
    secondary_diagnosis_count: int = Field(..., ge=0)
    elixhauser_score: float
    wbc: float = Field(..., ge=0)
    has_diabetes: int = Field(..., ge=0, le=1)
    has_hypertension: int = Field(..., ge=0, le=1)
    has_ckd: int = Field(..., ge=0, le=1)
    has_copd: int = Field(..., ge=0, le=1)
    has_heart_failure: int = Field(..., ge=0, le=1)
    num_medications: int = Field(..., ge=0)
    had_surgery: int = Field(..., ge=0, le=1)
    had_icu_stay: int = Field(..., ge=0, le=1)
    discharge_to_home: int = Field(..., ge=0, le=1)
    followup_booked: int = Field(..., ge=0, le=1)
    payer_type: str

    # Optional because the production model's fitted imputer handles missing labs.
    creatinine: float | None = None
    hemoglobin: float | None = None
    sodium: float | None = None
    potassium: float | None = None


class PredictionRequest(BaseModel):
    """Single patient feature payload for inference."""

    features: ReadmissionFeatures


class BatchPredictionRequest(BaseModel):
    """Batch of patients for inference."""

    records: list[ReadmissionFeatures] = Field(..., min_length=1)


class PredictionResponse(BaseModel):
    """Prediction result for a single patient."""

    predicted_label: int = Field(..., description="0 = not readmitted, 1 = readmitted ≤30d")
    probability: float = Field(..., ge=0, le=1, description="Probability of 30-day readmission")
    model_version: str = Field(..., description="Serving model identifier")
    risk_tier: str = Field(..., description="low / medium / high based on probability thresholds")


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
    environment: str
