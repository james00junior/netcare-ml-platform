# Netcare ML Platform

Production ML system for **30-day hospital readmission prediction**.

## Architecture

```
Development → Data Ingestion → Validation → Feature Engineering
    → Training → Experiment Tracking → Model Registry
    → Testing → Deployment → API Integration → Monitoring → Retraining
```

**Stack**
- **Azure Databricks** – data engineering, feature pipelines, training, MLflow
- **MLflow + Unity Catalog** – experiment tracking, model registry, lineage
- **Azure Machine Learning** – managed online / batch endpoints
- **FastAPI** – business/integration API layer
- **Azure API Management** – secure exposure to hospital systems
- **Azure Key Vault**, **Azure Monitor**, **GitHub Actions**, **ADLS Gen2**

## Project Structure

```
netcare-ml-platform/
├── src/
│   ├── config/          # Settings & model hyperparameters
│   ├── data/            # Ingestion, validation, preprocessing
│   ├── features/        # Feature matrix construction
│   ├── models/          # Train baseline / XGBoost, evaluate, registry
│   ├── serving/         # Predictor + Pydantic schemas
│   └── monitoring/      # Drift & performance monitoring
├── api/                 # FastAPI application
├── notebooks/           # Exploration & Databricks training notebooks
├── tests/
├── databricks/          # Databricks asset bundles
├── infrastructure/      # Terraform / Azure Bicep
├── .github/workflows/   # CI/CD
└── docs/
```

## Quick Start (Local)

```bash
# Install
pip install -e ".[dev,api,monitoring]"

# Place raw data
mkdir -p data/raw
cp /path/to/hospital_readmissions.csv data/raw/

# Run data quality
make validate-data

# Preprocess
make preprocess

# Train models
make train-baseline
make train-xgboost

# Evaluate
make evaluate

# Serve API
make serve
```

## Extracted Logic

| Original Assessment Script | Production Module |
|---------------------------|-------------------|
| `deliverable_1_data_quality.py` | `src/data/validation.py` |
| `deliverable_2_data_preparation.py` | `src/data/preprocessing.py` + `src/features/build_features.py` |
| `deliverable_3_baseline_model.py` | `src/models/train_baseline.py` + `src/models/train_xgboost.py` |
| `deliverable_4_evaluation_pack.py` | `src/models/evaluate.py` |

## Next Steps

1. Wire MLflow tracking (local or Databricks)
2. Add Databricks notebooks / jobs
3. Deploy Azure ML managed endpoint
4. Add CI/CD pipelines
5. Implement scheduled drift monitoring + retraining triggers

## License

Proprietary – Netcare