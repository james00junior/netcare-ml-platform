"""Model hyperparameter configurations."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class BaselineConfig:
    """Logistic Regression baseline configuration."""

    max_iter: int = 2000
    class_weight: str = "balanced"
    random_state: int = 42
    solver: str = "lbfgs"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_iter": self.max_iter,
            "class_weight": self.class_weight,
            "random_state": self.random_state,
            "solver": self.solver,
        }


@dataclass
class HistGBConfig:
    """HistGradientBoostingClassifier configuration (XGBoost replacement)."""

    max_iter: int = 100
    max_depth: int = 3
    learning_rate: float = 0.05
    min_samples_leaf: int = 20
    l2_regularization: float = 1.0
    max_bins: int = 255
    early_stopping: bool = True
    validation_fraction: float = 0.1
    n_iter_no_change: int = 10
    random_state: int = 42
    class_weight: str = "balanced"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_iter": self.max_iter,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "min_samples_leaf": self.min_samples_leaf,
            "l2_regularization": self.l2_regularization,
            "max_bins": self.max_bins,
            "early_stopping": self.early_stopping,
            "validation_fraction": self.validation_fraction,
            "n_iter_no_change": self.n_iter_no_change,
            "random_state": self.random_state,
            "class_weight": self.class_weight,
        }


# Backwards-compatible alias
XGBoostConfig = HistGBConfig


@dataclass
class ModelConfig:
    """Top-level model configuration."""

    baseline: BaselineConfig = field(default_factory=BaselineConfig)
    gbdt: HistGBConfig = field(default_factory=HistGBConfig)
    target_column: str = "readmitted_30d"
    test_size: float = 0.30
    random_state: int = 42

    drop_columns: tuple = (
        "patient_id",
        "encounter_id",
        "admission_date",
        "discharge_date",
        "days_to_readmission",
    )

    lab_columns: tuple = (
        "creatinine",
        "hemoglobin",
        "sodium",
        "potassium",
    )

    categorical_columns: tuple = (
        "sex",
        "admission_type",
        "admission_source",
        "discharge_disposition",
        "primary_diagnosis_group",
        "payer_type",
    )
