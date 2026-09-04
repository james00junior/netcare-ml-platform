"""FastAPI application for the Netcare readmission prediction service."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.config import settings
from src.serving.predictor import ReadmissionPredictor
from src.serving.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)

predictor: ReadmissionPredictor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model and its fitted preprocessing artifact once at startup."""
    del app
    global predictor
    model_path = Path("artifacts/gbdt_model_predictions.joblib")
    preprocessor_path = Path("artifacts/gbdt_model_preprocessor.joblib")

    if model_path.exists() and preprocessor_path.exists():
        predictor = ReadmissionPredictor(
            model_path=model_path,
            preprocessor_path=preprocessor_path,
            model_version="local-gbdt",
        )
        print(f"Model loaded from {model_path}")
    else:
        print(
            "WARNING: Model or fitted preprocessor not found under artifacts/. "
            "Endpoints will return 503 until both are available."
        )
    yield
    predictor = None


app = FastAPI(
    title="Netcare Readmission Prediction API",
    description="30-day hospital readmission risk scoring service",
    version="0.1.0",
    lifespan=lifespan,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Validate the optional API key when configured."""
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if predictor is not None else "degraded",
        model_loaded=predictor is not None,
        model_version=predictor.model_version if predictor else None,
        environment=settings.env,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict(request: PredictionRequest) -> PredictionResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    result = predictor.predict_single(request.features)
    return PredictionResponse(**result)


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    results = predictor.predict(request.records)
    return BatchPredictionResponse(predictions=[PredictionResponse(**r) for r in results])


@app.get("/", tags=["ops"])
def root():
    return {
        "service": "Netcare Readmission Prediction API",
        "version": "0.1.0",
        "docs": "/docs",
    }
