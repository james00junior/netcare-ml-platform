"""Unit tests for production serving components."""

import pandas as pd
import pytest
from pydantic import ValidationError

from src.serving.databricks_client import DatabricksServingClient, DatabricksServingError
from src.serving.mlflow_model import ReadmissionServingModel
from src.serving.schemas import PredictionRequest


VALID_FEATURES = {
