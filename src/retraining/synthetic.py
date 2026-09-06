"""Deterministic synthetic datasets for retraining demonstrations."""

from __future__ import annotations

import numpy as np
import pandas as pd


NUMERICAL_COLUMNS = ("age", "creatinine", "hemoglobin", "sodium", "potassium")
CATEGORICAL_COLUMNS = ("sex", "admission_type", "admission_source")


def make_reference_dataset(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    """Create a deterministic reference population for drift testing."""
    if n_rows < 10:
        raise ValueError("n_rows must be at least 10")
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "age": rng.normal(60, 12, n_rows).clip(18, 95),
            "creatinine": rng.normal(1.0, 0.2, n_rows).clip(0.3, 3.0),
            "hemoglobin": rng.normal(13.0, 1.2, n_rows).clip(7, 18),
            "sodium": rng.normal(139, 3, n_rows).clip(125, 150),
            "potassium": rng.normal(4.1, 0.4, n_rows).clip(2.5, 6),
            "sex": rng.choice(["Female", "Male"], n_rows, p=[0.55, 0.45]),
            "admission_type": rng.choice(
                ["Emergency", "Elective", "Urgent"], n_rows, p=[0.60, 0.25, 0.15]
            ),
            "admission_source": rng.choice(
                ["ER", "Clinic", "Transfer"], n_rows, p=[0.65, 0.25, 0.10]
            ),
        }
    )


def make_shifted_dataset(n_rows: int = 500, seed: int = 43) -> pd.DataFrame:
    """Create a deterministic population with an intentional distribution shift."""
    if n_rows < 10:
        raise ValueError("n_rows must be at least 10")
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "age": rng.normal(72, 12, n_rows).clip(18, 95),
            "creatinine": rng.normal(1.35, 0.25, n_rows).clip(0.3, 3.0),
            "hemoglobin": rng.normal(11.5, 1.2, n_rows).clip(7, 18),
            "sodium": rng.normal(136, 3, n_rows).clip(125, 150),
            "potassium": rng.normal(4.3, 0.4, n_rows).clip(2.5, 6),
            "sex": rng.choice(["Female", "Male"], n_rows, p=[0.35, 0.65]),
            "admission_type": rng.choice(
                ["Emergency", "Elective", "Urgent"], n_rows, p=[0.80, 0.10, 0.10]
            ),
            "admission_source": rng.choice(
                ["ER", "Clinic", "Transfer"], n_rows, p=[0.80, 0.10, 0.10]
            ),
        }
    )
