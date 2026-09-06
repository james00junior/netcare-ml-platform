"""Typed integration contract for existing systems calling model serving."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.serving.schemas import ReadmissionFeatures


class ServingRequest(BaseModel):
    """Databricks dataframe-records request sent by an existing client system."""

    model_config = ConfigDict(extra="forbid")

    dataframe_records: list[ReadmissionFeatures] = Field(..., min_length=1)

    def as_payload(self) -> dict[str, Any]:
        """Serialize the request using Databricks Model Serving's invocation contract."""
        return {"dataframe_records": [record.model_dump() for record in self.dataframe_records]}


class ServingPrediction(BaseModel):
    """Validated prediction returned by the serving endpoint."""

    predicted_label: int = Field(..., ge=0, le=1)
    probability: float = Field(..., ge=0, le=1)
    risk_tier: str
    model_version: str


class ServingResponse(BaseModel):
    """Validated response contract for an existing client system."""

    model_config = ConfigDict(extra="forbid")

    predictions: list[ServingPrediction]
