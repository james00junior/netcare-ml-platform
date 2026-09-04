"""Data ingestion utilities."""

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from src.config import settings


def load_raw_data(path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load the raw hospital readmissions dataset.

    Parameters
    ----------
    path : str or Path, optional
        Path to the CSV file. Defaults to settings.raw_data_path.

    Returns
    -------
    pd.DataFrame
        Raw dataset.
    """
    data_path = Path(path) if path else Path(settings.raw_data_path)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {data_path}. "
            "Place hospital_readmissions.csv in the configured path or pass an explicit path."
        )

    df = pd.read_csv(data_path)
    return df


def save_processed_data(
    df: pd.DataFrame,
    name: str,
    path: Optional[Union[str, Path]] = None,
) -> Path:
    """Save a processed dataframe to the processed data directory."""
    out_dir = Path(path) if path else Path(settings.processed_data_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{name}.csv"
    df.to_csv(out_path, index=False)
    return out_path