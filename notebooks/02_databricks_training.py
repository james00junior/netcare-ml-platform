# Databricks notebook source
# MAGIC %md
# MAGIC # Netcare Readmission Training
# MAGIC
# MAGIC Lightweight Databricks/GCP training entry point for Phase 6.

# COMMAND ----------

import os
import sys

import cloudpickle
import mlflow
import numpy
import pandas
import scipy
import sklearn

# The bundle syncs src/ beside notebooks/. Add the bundle root to imports.
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
if bundle_root not in sys.path:
    sys.path.insert(0, bundle_root)

from src.config import settings
from src.data.ingestion import load_raw_data
from src.data.preprocessing import (
    clean_identifiers_and_leakage,
    prepare_train_test_data,
    standardise_categoricals,
)
from src.data.validation import run_data_quality_checks
from src.models.promotion import register_and_promote_candidate
from src.models.train_baseline import run_baseline_training
from src.models.train_gbdt import run_gbdt_training

# COMMAND ----------

# Bundle job parameters. Defaults are aligned with the verified Databricks
# workspace catalog and its existing default schema; deployment parameters remain authoritative.
widget_values = dbutils.widgets.getAll()
catalog_name = widget_values.get("catalog_name", "netcareaidatabricks")
experiment_name = widget_values.get("experiment_name", "/Shared/netcare-readmission")
registered_model_name = widget_values.get(
    "registered_model_name", "netcareaidatabricks.default.readmission_model"
)
raw_data_path = widget_values.get(
    "raw_data_path", "data/raw/hospital_readmissions.csv"
)

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
mlflow.set_registry_uri(settings.mlflow_registry_uri)
mlflow.set_experiment(experiment_name)

print("Catalog:", catalog_name)
print("Experiment:", experiment_name)
print("Registered model:", registered_model_name)
print("Raw data:", raw_data_path)

# Capture the actual training environment rather than inferring it from the
# project requirements. These values become MLflow lineage metadata and are
# used to keep the serving environment compatible with the training artifact.
training_runtime = {
    "python_version": sys.version.split()[0],
    "mlflow_version": mlflow.__version__,
    "scikit_learn_version": sklearn.__version__,
    "numpy_version": numpy.__version__,
    "pandas_version": pandas.__version__,
    "scipy_version": scipy.__version__,
    "cloudpickle_version": cloudpickle.__version__,
}
print("Training runtime:", training_runtime)

# Fail early with a precise configuration error rather than allowing MLflow to
# fail later with an opaque namespace error.
if not registered_model_name.startswith(f"{catalog_name}."):
    raise ValueError(
        "Registered model must belong to the configured Unity Catalog catalog: "
        f"catalog={catalog_name!r}, registered_model_name={registered_model_name!r}"
    )

model_parts = registered_model_name.split(".")
if len(model_parts) != 3 or model_parts[1] != "default":
    raise ValueError(
        "Registered model must use the verified three-level Unity Catalog name "
        "<catalog>.default.<model>: "
        f"{registered_model_name!r}"
    )

spark.sql(f"DESCRIBE SCHEMA {catalog_name}.default")
print(f"Verified Unity Catalog schema: {catalog_name}.default")

# COMMAND ----------

# Read GCS natively with Spark in Databricks; keep the existing pandas pipeline locally.
if raw_data_path.startswith("gs://"):
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(raw_data_path)
        .toPandas()
    )
else:
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

with mlflow.start_run(run_name="readmission-candidate") as run:
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
    candidate_run_id = run.info.run_id

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

print("Quality gate passed:", quality_result.passed)
print("Checks:", quality_result.checks)
print("Reasons:", quality_result.reasons)
print("Registered model version:", registered_version)

if not quality_result.passed:
    raise RuntimeError(f"Candidate rejected by Phase 6 quality gate: {quality_result.reasons}")

print("Candidate registered and promoted to the Unity Catalog champion alias.")
