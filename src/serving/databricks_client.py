"""HTTP client for the governed Databricks Model Serving endpoint."""

from typing import Any

import httpx

from src.serving.observability import get_logger

logger = get_logger()


class DatabricksServingError(RuntimeError):
    """Raised when the Databricks serving endpoint cannot score a request."""


class DatabricksServingClient:
    """Call a Databricks Model Serving endpoint using the dataframe-records contract."""

    def __init__(self, endpoint_url: str, token: str, timeout: float = 30.0):
        if not endpoint_url:
            raise ValueError("A Databricks serving endpoint URL is required.")
        if not token:
            raise ValueError("A Databricks serving token is required.")

        self.endpoint_url = endpoint_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def predict(
        self, records: list[dict[str, Any]], request_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Score raw feature records without logging patient data."""
        if not records:
            raise ValueError("At least one record is required for prediction.")

        payload = {"dataframe_records": records}
        headers = {"Authorization": f"Bearer {self.token}"}
        log_context = {"request_id": request_id, "batch_size": len(records)}
        logger.info(
            "Databricks serving request started",
            extra={"event": "upstream_request_started", **log_context},
        )

        try:
            response = httpx.post(
                self.endpoint_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Databricks serving returned an HTTP error",
                extra={
                    "event": "upstream_request_failed",
                    "upstream_status": exc.response.status_code,
                    **log_context,
                },
            )
            raise DatabricksServingError(
                f"Databricks serving request failed with HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(
                "Databricks serving request failed",
                extra={"event": "upstream_request_failed", **log_context},
            )
            raise DatabricksServingError("Databricks serving request failed.") from exc

        body = response.json()
        predictions = body.get("predictions") if isinstance(body, dict) else None
        if not isinstance(predictions, list):
            logger.error(
                "Databricks serving response did not contain predictions",
                extra={"event": "upstream_response_invalid", **log_context},
            )
            raise DatabricksServingError(
                "Databricks serving response did not contain predictions."
            )

        result = [self._normalise_prediction(item) for item in predictions]
        logger.info(
            "Databricks serving request completed",
            extra={"event": "upstream_request_completed", **log_context},
        )
        return result

    @staticmethod
    def _normalise_prediction(item: Any) -> dict[str, Any]:
        """Validate the serving response shape before returning it to the API."""
        if not isinstance(item, dict):
            raise DatabricksServingError("Databricks returned an invalid prediction item.")

        required = {"predicted_label", "probability", "risk_tier"}
        if not required.issubset(item):
            raise DatabricksServingError(
                "Databricks prediction is missing one or more required output fields."
            )

        return {
            "predicted_label": int(item["predicted_label"]),
            "probability": float(item["probability"]),
            "risk_tier": str(item["risk_tier"]),
            "model_version": str(item.get("model_version", "champion")),
        }
