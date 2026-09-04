# Architecture

## Overview

The Netcare ML Platform implements a production ML lifecycle for **30-day hospital readmission prediction** on **Google Cloud Platform (GCP)**.

Google Cloud Storage (GCS) provides the cloud data lake. Databricks runs on GCP and implements the medallion data architecture, feature engineering and model training. MLflow provides experiment tracking and model registry. FastAPI provides the prediction/integration API.

```text
┌─────────────────────┐
│ Google Cloud        │
│ Storage (GCS)       │
│                     │
│ raw / bronze /      │
│ silver / gold       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Databricks on GCP   │
│                     │
│ ingestion           │
│ validation          │
│ transformation      │
│ feature engineering │
│ training            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ MLflow               │
│                     │
│ experiments          │
│ artifacts            │
│ model registry       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Model Serving        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FastAPI              │
│ prediction API       │
└──────────┬──────────┘
           │
           ▼
     Hospital systems
```

## Components

| Component | Responsibility |
|-----------|----------------|
| Google Cloud Storage (GCS) | Cloud data lake and raw/processed data storage |
| Databricks on GCP | Ingestion, validation, transformation, feature engineering and training |
| Delta Lake / Medallion Architecture | Bronze, Silver and Gold data layers |
| MLflow | Experiment tracking, model artifacts, model registry and lineage |
| FastAPI | Lightweight prediction and integration API |
| GitHub Actions | CI/CD and automated testing |

## Data Flow

1. Raw hospital data lands in GCS.
2. Databricks ingests and validates the data into the **Bronze** layer.
3. Cleaning, standardisation and quality rules produce the **Silver** layer.
4. Feature engineering produces ML-ready **Gold** tables.
5. Databricks training jobs log parameters, metrics and model artifacts to MLflow.
6. The selected model is registered in the MLflow Model Registry.
7. The registered model is exposed through the serving layer and FastAPI.
8. Hospital systems call the prediction API.
9. Monitoring detects data drift and model performance degradation and can trigger retraining workflows.

## Medallion Architecture

```text
GCS Raw Data
     │
     ▼
  BRONZE
Raw, immutable source data
     │
     ▼
  SILVER
Validated and standardised data
     │
     ▼
   GOLD
ML-ready feature tables
     │
     ▼
Model Training + Evaluation
```

## Model Promotion

```text
Development
    │
    ▼
Databricks Training
    │
    ▼
MLflow Experiment
    │
    ▼
MLflow Model Registry
    │
    ▼
Production Model Serving
    │
    ▼
FastAPI
```

The architecture keeps the current local Python pipeline as the reproducible development baseline while progressively moving production data processing and ML workflows into Databricks on GCP.
