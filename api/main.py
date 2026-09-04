"""FastAPI application for the Netcare readmission prediction service."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.config import settings
from src.serving.databricks_client import DatabricksServingClient, DatabricksServingError
from src.serving.predictor import ReadmissionPredictor
from src.serving.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)

predictor: ReadmissionPredictor | DatabricksServingClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the configured inference backend once at application startup."""
    del app
    global predictor

    if settings.is_production:
        if not settings.databricks_serving_endpoint or not settings.databricks_serving_token:
            raise RuntimeError(
                "Production requires DATABRICKS_SERVING_ENDPOINT and "
                "DATABRICKS_SERVING_TOKEN."
            )
        predictor = DatabricksServingClient(
            endpoint_url=settings.databricks_serving_endpoint,
            token=settings.databricks_serving_token,
            timeout=settings.databricks_serving_timeout,
        )
        print("Configured governed Databricks Model Serving backend.")
    else:
        model_path = Path(settings.artifacts_path) / "gbdt_model_predictions.joblib"
        preprocessor_path = Path(settings.artifacts_path) / "gbdt_model_preprocessor.joblib"

        if model_path.exists() and preprocessor_path.exists():
            predictor = ReadmissionPredictor(
                model_path=model_path,
                preprocessor_path=preprocessor_path,
                model_version="local-gbdt",
            )
            print(f"Local model loaded from {model_path}")
        else:
            print(
                "WARNING: Local model or fitted preprocessor not found under artifacts/. "
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


def _predict_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Route prediction requests to the configured local or governed backend."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model serving backend not available")

    try:
        if isinstance(predictor, DatabricksServingClient):
            return predictor.predict(records)
        return predictor.predict(records)
    except DatabricksServingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    model_version = None
    if isinstance(predictor, ReadmissionPredictor):
        model_version = predictor.model_version
    elif isinstance(predictor, DatabricksServingClient):
        model_version = "champion"

    return HealthResponse(
        status="ok" if predictor is not None else "degraded",
        model_loaded=predictor is not None,
        model_version=model_version,
        environment=settings.env,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict(request: PredictionRequest) -> PredictionResponse:
    result = _predict_records([request.features])[0]
    return PredictionResponse(**result)


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    results = _predict_records(request.records)
    return BatchPredictionResponse(predictions=[PredictionResponse(**r) for r in results])


@app.get("/", tags=["ops"])
def root():
    return {
        "service": "Netcare Readmission Prediction API",
        "version": "0.1.0",
        "docs": "/docs",
    }
