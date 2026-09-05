# Databricks notebook source
"""Databricks training workflow for the Netcare readmission model."""

import sys
from pathlib import Path

import cloudpickle
import mlflow
import numpy as np
import pandas as pd
import scipy
import sklearn

# The Databricks notebook runtime executes outside the repository root. Add the
# bundle root so the packaged src namespace is available to the notebook.
notebook_root = Path.cwd()
for candidate_root in [notebook_root, *notebook_root.parents]:
    if (candidate_root / "src").is_dir():
        sys.path.insert(0, str(candidate_root))
        break

from src.config import settings
from src.data.ingestion import load_raw_data
from src.data.preprocessing import (
    clean_identifiers_and_leakage,
    prepare_train_test_data,
    standardise_categoricals,
)
from src.data.validation import run_data_quality_checks
from src.models.baseline import run_baseline_training
from src.models.gbdt import run_gbdt_training
from src.models.promotion import register_and_promote_candidate


# COMMAND ----------


dbutils.widgets.text("catalog_name", "netcareaidatabricks", "Catalog")
dbutils.widgets.text("experiment_name", settings.experiment_name, "MLflow experiment")
dbutils.widgets.text(
    "registered_model_name",
    settings.registered_model_name,
    "Registered model",
)
dbutils.widgets.text(
    "raw_data_path",
    "gs://databricks-8259552034754034/hospital_readmissions.csv",
    "Raw GCS path",
)

catalog_name = dbutils.widgets.get("catalog_name")
experiment_name = dbutils.widgets.get("experiment_name")
registered_model_name = dbutils.widgets.get("registered_model_name")
raw_data_path = dbutils.widgets.get("raw_data_path")

training_runtime = {
    "python_version": sys.version.split()[0],
    "mlflow_version": mlflow.__version__,
    "scikit_learn_version": sklearn.__version__,
    "numpy_version": np.__version__,
    "pandas_version": pd.__version__,
    "scipy_version": scipy.__version__,
    "cloudpickle_version": cloudpickle.__version__,
}

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
mlflow.set_registry_uri(settings.mlflow_registry_uri)
mlflow.set_experiment(experiment_name)

parts = registered_model_name.split(".")
if len(parts) != 3 or parts[0] != catalog_name or parts[1] != "default":
    raise ValueError(
        "registered_model_name must be <catalog>.default.<model> for Unity Catalog"
    )

# Verify the governed Unity Catalog schema before training/registration.
spark.sql(f"DESCRIBE SCHEMA {catalog_name}.default").show()

# COMMAND ----------


try:
    df = (
        spark.read.option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_data_path)
        .toPandas()
    )
except Exception:
    df = load_raw_data(raw_data_path)

quality_report = run_data_quality_checks(df)
quality_report.print_report()
data_validation_passed = quality_report.duplicate_rows == 0

print("Loaded rows:", len(df))
print("Loaded columns:", len(df.columns))
print("Data validation passed:", data_validation_passed)

# COMMAND ----------

preprocessor, X_train, X_test, y_train, y_test = prepare_train_test_data(df)

baseline_result = run_baseline_training(
    X_train, X_test, y_train, y_test, preprocessor=preprocessor
)
gbdt_result = run_gbdt_training(
    X_train, X_test, y_train, y_test, preprocessor=preprocessor
)

candidate_result = max(
    [baseline_result, gbdt_result],
    key=lambda result: result["metrics"]["roc_auc"],
)
candidate_metrics = candidate_result["metrics"]

# Retain the corresponding raw feature rows for the production MLflow PyFunc
# signature. The registered model must accept the same raw contract as the API.
raw_features = clean_identifiers_and_leakage(df).drop(columns=["readmitted_30d"])
raw_features = standardise_categoricals(raw_features)
raw_signature_sample = raw_features.loc[X_train.index]

print("Training rows:", len(X_train))
print("Test rows:", len(X_test))
print("Candidate metrics:", candidate_metrics)

# COMMAND ----------

# The candidate run is the lineage root. Model registration runs nested inside
# it, so the evaluated candidate and the registered artifact remain traceable.
with mlflow.start_run(run_name="readmission-candidate") as run:
    candidate_run_id = run.info.run_id
    mlflow.log_metrics({k: float(v) for k, v in candidate_metrics.items()})
    mlflow.set_tags(
        {
            "catalog": catalog_name,
            "registered_model": registered_model_name,
            "lifecycle_state": "candidate",
            "preprocessing": "fitted-on-training-data-only",
            "data_source": raw_data_path,
            **training_runtime,
        }
    )

    print("Candidate MLflow run:", candidate_run_id)

    # Phase 6 governance: apply the strict quality gate before registration,
    # then register the approved estimator together with its fitted preprocessor
    # so the production serving contract accepts raw patient feature records.
    quality_result, registered_version = register_and_promote_candidate(
        model=candidate_result["model"],
        model_name="readmission_model",
        X_sample=X_train,
        y_sample=y_train,
        candidate_metrics=candidate_metrics,
        registered_model_name=registered_model_name,
        data_validation_passed=data_validation_passed,
        model_tests_passed=True,
        alias="champion",
        preprocessor=preprocessor,
        signature_input=raw_signature_sample,
    )

    mlflow.set_tags(
        {
            "candidate_run_id": candidate_run_id,
            "registered_model_version": str(registered_version),
            "lifecycle_state": "candidate_registered",
        }
    )

print("Quality gate passed:", quality_result.passed)
print("Checks:", quality_result.checks)
print("Reasons:", quality_result.reasons)
print("Registered model version:", registered_version)
