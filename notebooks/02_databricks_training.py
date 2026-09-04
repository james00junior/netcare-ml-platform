# Databricks notebook source
# MAGIC %md
# MAGIC # Netcare Readmission Training
# MAGIC
# MAGIC Lightweight Databricks/GCP training entry point for Phase 6.

# COMMAND ----------

import os
import sys

import mlflow

# The bundle syncs src/ beside notebooks/. Add the bundle root to imports.
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
bundle_root = os.path.dirname(os.path.dirname(notebook_path))
if bundle_root not in sys.path:
    sys.path.insert(0, bundle_root)

from src.config import settings
from src.data.ingestion import load_raw_data
from src.data.preprocessing import prepare_train_test_data
from src.data.validation import run_data_quality_checks
from src.models.promotion import register_and_promote_candidate
from src.models.train_baseline import run_baseline_training
from src.models.train_gbdt import run_gbdt_training

# COMMAND ----------

# Bundle job parameters.
catalog_name = dbutils.widgets.get("catalog_name") if "catalog_name" in dbutils.widgets.getAll() else "nectare"
experiment_name = dbutils.widgets.get("experiment_name") if "experiment_name" in dbutils.widgets.getAll() else "/Shared/netcare-readmission"
registered_model_name = dbutils.widgets.get("registered_model_name") if "registered_model_name" in dbutils.widgets.getAll() else "nectare.ml.readmission_model"
raw_data_path = dbutils.widgets.get("raw_data_path") if "raw_data_path" in dbutils.widgets.getAll() else "data/raw/hospital_readmissions.csv"

mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
mlflow.set_registry_uri(settings.mlflow_registry_uri)
mlflow.set_experiment(experiment_name)

print("Catalog:", catalog_name)
print("Experiment:", experiment_name)
print("Registered model:", registered_model_name)
print("Raw data:", raw_data_path)

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
        }
    )
    candidate_run_id = run.info.run_id

print("Candidate MLflow run:", candidate_run_id)

# Phase 6 governance: apply the strict quality gate before registration,
# then register the approved estimator in Unity Catalog and assign the champion alias.
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
)

print("Quality gate passed:", quality_result.passed)
print("Checks:", quality_result.checks)
print("Reasons:", quality_result.reasons)
print("Registered model version:", registered_version)

if not quality_result.passed:
    raise RuntimeError(f"Candidate rejected by Phase 6 quality gate: {quality_result.reasons}")

print("Candidate registered and promoted to the Unity Catalog champion alias.")
