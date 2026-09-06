"""HTTP client for the governed Databricks Model Serving endpoint."""

import time
from typing import Any

import httpx

from src.serving.observability import get_logger

logger = get_logger()


class DatabricksServingError(RuntimeError):
    """Raised when the Databricks serving endpoint cannot score a request."""


class DatabricksServingClient:
    """Call a Databricks Model Serving endpoint using the dataframe-records contract."""

    def __init__(
        self,
        endpoint_url: str,
        token: str,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_backoff: float = 0.25,
    ):
        if not endpoint_url:
            raise ValueError("A Databricks serving endpoint URL is required.")
        if not token:
            raise ValueError("A Databricks serving token is required.")
        if timeout <= 0:
            raise ValueError("Serving timeout must be greater than zero.")
        if max_retries < 0:
            raise ValueError("Maximum retries cannot be negative.")
        if retry_backoff < 0:
            raise ValueError("Retry backoff cannot be negative.")

        self.endpoint_url = endpoint_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def predict(
        self, records: list[dict[str, Any]], request_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Score raw feature records without logging patient data."""
        if not records:
            raise ValueError("At least one record is required for prediction.")

        payload = {"dataframe_records": records}
        headers = {"Authorization": f"Bearer {self.token}"}
        if request_id:
            headers["X-Request-ID"] = request_id

        log_context = {"request_id": request_id, "batch_size": len(records)}
        logger.info(
            "Databricks serving request started",
            extra={"event": "upstream_request_started", **log_context},
        )

        response = self._request(payload, headers, log_context)

        try:
            body = response.json()
        except ValueError as exc:
            logger.error(
                "Databricks serving returned malformed JSON",
                extra={"event": "upstream_response_invalid", **log_context},
            )
            raise DatabricksServingError(
                "Databricks serving response was not valid JSON."
            ) from exc

        predictions = body.get("predictions") if isinstance(body, dict) else None
        if not isinstance(predictions, list):
            logger.error(
                "Databricks serving response did not contain predictions",
                extra={"event": "upstream_response_invalid", **log_context},
            )
            raise DatabricksServingError("Databricks serving response did not contain predictions.")

        if len(predictions) != len(records):
            logger.error(
                "Databricks serving returned an unexpected prediction count",
                extra={
                    "event": "upstream_response_invalid",
                    "prediction_count": len(predictions),
                    "batch_size": len(records),
                    **log_context,
                },
            )
            raise DatabricksServingError(
                "Databricks serving returned a prediction count that does not match the request."
            )

        try:
            result = [self._normalise_prediction(item) for item in predictions]
        except (TypeError, ValueError) as exc:
            logger.error(
                "Databricks serving returned an invalid prediction",
                extra={"event": "upstream_response_invalid", **log_context},
            )
            raise DatabricksServingError("Databricks returned an invalid prediction.") from exc

        logger.info(
            "Databricks serving request completed",
            extra={"event": "upstream_request_completed", **log_context},
        )
        return result

    def _request(
        self,
        payload: dict[str, Any],
        headers: dict[str, str],
        log_context: dict[str, Any],
    ) -> httpx.Response:
        """Send the request, retrying only transient upstream failures."""
        attempts = self.max_retries + 1

        for attempt in range(attempts):
            try:
                response = httpx.post(
                    self.endpoint_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code < 500 or attempt == self.max_retries:
                    logger.error(
                        "Databricks serving returned an HTTP error",
                        extra={
                            "event": "upstream_request_failed",
                            "upstream_status": status_code,
                            "attempt": attempt + 1,
                            **log_context,
                        },
                    )
                    raise DatabricksServingError(
                        f"Databricks serving request failed with HTTP {status_code}."
                    ) from exc
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                if attempt == self.max_retries:
                    logger.error(
                        "Databricks serving request failed after retries",
                        extra={
                            "event": "upstream_request_failed",
                            "attempt": attempt + 1,
                            "error_type": type(exc).__name__,
                            **log_context,
                        },
                    )
                    raise DatabricksServingError("Databricks serving request failed.") from exc

            if self.retry_backoff:
                time.sleep(self.retry_backoff * (2**attempt))

        raise DatabricksServingError("Databricks serving request failed.")

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
