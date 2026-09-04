"""
Deprecated compatibility shim.

XGBoost was replaced by HistGradientBoostingClassifier
(see train_gbdt.py) to avoid the OpenMP dependency on macOS.

This module re-exports the GBDT functions under the old names
so any remaining references keep working.
"""

from src.models.train_gbdt import (  # noqa: F401
    predict_gbdt as predict_xgboost,
)
