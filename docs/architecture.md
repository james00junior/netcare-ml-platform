# Architecture

## Overview

The Netcare ML Platform implements a full production ML lifecycle for 30-day hospital readmission prediction.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  ADLS Gen2      │────▶│  Azure Databricks │────▶│  MLflow +       │
│  (raw/curated)  │     │  (Spark, FE,     │     │  Unity Catalog  │
└─────────────────┘     │   training)      │     └────────┬────────┘
                        └────────┬─────────┘              │
                                 │                        │
                                 ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Azure ML        │◀────│  Model Registry │
                        │  Online / Batch  │     └─────────────────┘
                        │  Endpoints       │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  FastAPI         │────▶│  Azure API Mgmt │
                        │  (optional)      │     │  (hospital APIs) │
                        └──────────────────┘     └─────────────────┘
```

## Components

| Component | Responsibility |
|-----------|----------------|
| ADLS Gen2 | Raw, bronze, silver, gold data zones |
| Databricks | Ingestion, validation, feature engineering, training, experiment tracking |
| MLflow + Unity Catalog | Model versioning, lineage, governance |
| Azure ML | Managed online & batch inference endpoints |
| FastAPI | Lightweight business API / orchestration layer |
| Azure API Management | Auth, throttling, routing for hospital systems |
| Azure Key Vault | Secrets |
| Azure Monitor / App Insights | Infra + API monitoring |
| GitHub Actions | CI/CD |

## Data Flow

1. Raw hospital data lands in ADLS Gen2 (`raw/`)
2. Databricks Auto Loader / Spark jobs validate and clean → `bronze/` → `silver/`
3. Feature pipelines produce training tables → `gold/` / Feature Store
4. Training jobs log to MLflow; best model is registered
5. Model is deployed to Azure ML endpoint
6. Hospital systems call via APIM → (optional FastAPI) → Azure ML endpoint
7. Monitoring jobs detect drift / performance degradation and trigger retraining

## Model Promotion

```
Development (Databricks) → Staging (MLflow stage) → Production (Azure ML endpoint)
```