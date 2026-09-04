"""Central configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    env: str = "dev"
    project_name: str = "netcare-ml-platform"

    # Paths
    raw_data_path: str = "data/raw/hospital_readmissions.csv"
    processed_data_path: str = "data/processed"
    feature_store_path: str = "data/features"
    artifacts_path: str = "artifacts"

    # Model
    model_name: str = "readmission_xgboost"
    experiment_name: str = "/Shared/netcare-readmission"
    registered_model_name: str = "netcareaidatabricks.default.readmission_model"

    # MLflow / Unity Catalog
    mlflow_tracking_uri: str = "databricks"
    mlflow_registry_uri: str = "databricks-uc"

    # Databricks Model Serving
    databricks_serving_endpoint: str | None = None
    databricks_serving_token: str | None = None
    databricks_serving_timeout: float = 30.0

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str | None = None

    # Monitoring thresholds
    drift_threshold: float = 0.15
    performance_alert_threshold: float = 0.05

    # Train/test
    test_size: float = 0.30
    random_state: int = 42

    @property
    def is_production(self) -> bool:
        return self.env.lower() in ("prod", "production")

    def get_path(self, *parts: str) -> Path:
        return Path(*parts)


settings = Settings()
