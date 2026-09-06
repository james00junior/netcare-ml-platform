"""FastAPI application for the Netcare readmission prediction service."""

from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.serving.databricks_client import DatabricksServingClient, DatabricksServingError
from src.serving.observability import configure_logging
from src.serving.predictor import ReadmissionPredictor
from src.serving.schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)

logger = configure_logging()
predictor: ReadmissionPredictor | DatabricksServingClient | None = None


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID and emit privacy-safe request lifecycle events."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started = perf_counter()
        logger.info(
            "API request started",
            extra={
                "event": "request_started",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        response = await call_next(request)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "API request completed",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the configured inference backend once at application startup."""
    del app
    global predictor

    if settings.databricks_serving_endpoint or settings.databricks_serving_token:
        if not settings.databricks_serving_endpoint or not settings.databricks_serving_token:
            raise RuntimeError(
                "Databricks serving requires both DATABRICKS_SERVING_ENDPOINT "
                "and DATABRICKS_SERVING_TOKEN."
            )
        predictor = DatabricksServingClient(
            endpoint_url=settings.databricks_serving_endpoint,
            token=settings.databricks_serving_token,
            timeout=settings.databricks_serving_timeout,
        )
        logger.info(
            "Configured governed Databricks Model Serving backend",
            extra={"event": "backend_configured"},
        )
    else:
        model_path = Path(settings.artifacts_path) / "gbdt_model_predictions.joblib"
        preprocessor_path = Path(settings.artifacts_path) / "gbdt_model_preprocessor.joblib"
        if model_path.exists() and preprocessor_path.exists():
            predictor = ReadmissionPredictor(
                model_path=model_path,
                preprocessor_path=preprocessor_path,
                model_version="local-gbdt",
            )
            logger.info("Local model loaded", extra={"event": "backend_configured"})
        else:
            logger.warning(
                "Local model or fitted preprocessor not found; inference is unavailable",
                extra={"event": "backend_unavailable"},
            )

    yield
    predictor = None


app = FastAPI(
    title="Netcare Readmission Prediction API",
    description="30-day hospital readmission risk scoring service",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(RequestObservabilityMiddleware)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Validate the optional API key when configured."""
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def _predict_records(records: list[Any], request_id: str | None = None) -> list[dict[str, Any]]:
    """Route validated feature records to the configured inference backend."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model serving backend not available")

    raw_records = [
        record.model_dump() if hasattr(record, "model_dump") else record for record in records
    ]

    try:
        if isinstance(predictor, DatabricksServingClient):
            return predictor.predict(raw_records, request_id=request_id)
        return predictor.predict(raw_records)
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
        model_version = "databricks-serving"

    return HealthResponse(
        status="ok" if predictor is not None else "degraded",
        model_loaded=predictor is not None,
        model_version=model_version,
        environment=settings.env,
    )


@app.post(
    "/v1/predictions/readmission",
    response_model=PredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict_readmission(request: PredictionRequest, http_request: Request) -> PredictionResponse:
    """Stable versioned integration contract for readmission prediction."""
    result = _predict_records([request.features], request_id=http_request.state.request_id)[0]
    return PredictionResponse(**result)


@app.post(
    "/v1/predictions/readmission/batch",
    response_model=BatchPredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict_readmission_batch(
    request: BatchPredictionRequest, http_request: Request
) -> BatchPredictionResponse:
    """Stable versioned batch integration contract."""
    results = _predict_records(request.records, request_id=http_request.state.request_id)
    return BatchPredictionResponse(predictions=[PredictionResponse(**r) for r in results])


@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict(request: PredictionRequest, http_request: Request) -> PredictionResponse:
    return predict_readmission(request, http_request)


@app.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["inference"],
    dependencies=[Security(verify_api_key)],
)
def predict_batch(request: BatchPredictionRequest, http_request: Request) -> BatchPredictionResponse:
    return predict_readmission_batch(request, http_request)


@app.get("/", tags=["ops"])
def root():
    return {
        "service": "Netcare Readmission Prediction API",
        "version": "0.1.0",
        "docs": "/docs",
    }
