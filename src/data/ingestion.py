"""Data ingestion utilities."""

from pathlib import Path

import pandas as pd

from src.config import settings


def load_raw_data(path: str | Path | None = None) -> pd.DataFrame:
    """
    Load the raw hospital readmissions dataset.

    Local filesystem paths are read with pandas. Cloud URIs (for example
    ``gs://...``) are read through pandas' fsspec-compatible storage layer.
    """
    data_path = str(path) if path else settings.raw_data_path

    if "://" in data_path:
        try:
            return pd.read_csv(data_path)
        except Exception as exc:
            raise FileNotFoundError(
                f"Raw data could not be read from {data_path}. "
                "Verify the cloud path and Databricks storage permissions."
            ) from exc

    local_path = Path(data_path)
    if not local_path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {local_path}. "
            "Place hospital_readmissions.csv in the configured path or pass an explicit path."
        )

    return pd.read_csv(local_path)


def save_processed_data(
    df: pd.DataFrame,
    name: str,
    path: str | Path | None = None,
) -> Path:
    """Save a processed dataframe to the processed data directory."""
    out_dir = Path(path) if path else Path(settings.processed_data_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.csv"
    df.to_csv(out_path, index=False)
    return out_path
