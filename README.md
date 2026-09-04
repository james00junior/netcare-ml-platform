# Netcare ML Platform

Production ML system for **30-day hospital readmission prediction**.

## Architecture

The platform is designed for **GCP**, with **Google Cloud Storage (GCS)** as the data lake and **Databricks on GCP** as the data engineering and ML platform.

```text
                         Google Cloud Platform
                                  │
                         Google Cloud Storage
                                  │
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
              BRONZE           SILVER             GOLD
             Raw data       Clean/validated     ML-ready
                                  │              features
                                  └───────┬────────┘
                                          ▼
                                  Databricks on GCP
                                          │
                                      MLflow
                                  ┌───────┴────────┐
                                  ▼                ▼
                            Experiments      Model Registry
                                                   │
                                                   ▼
                                             Model Serving
                                                   │
                                                   ▼
                                                FastAPI
                                                   │
                                                   ▼
                                           Hospital systems
```

**Stack**
- **Google Cloud Storage (GCS)** – cloud data lake and raw/processed data storage
- **Databricks on GCP** – ingestion, validation, transformation, feature engineering and model training
- **Delta Lake / Medallion Architecture** – Bronze, Silver and Gold data layers
- **MLflow** – experiment tracking, model artifacts, model registry and lineage
- **FastAPI** – prediction and integration API layer
- **GitHub Actions** – CI/CD and automated testing

## Project Structure

```text
netcare-ml-platform/
├── src/
│   ├── config/          # Settings & model hyperparameters
│   ├── data/            # Ingestion, validation, preprocessing
│   ├── features/        # Feature matrix construction
│   ├── models/          # Training, evaluation and model registry
│   ├── serving/         # Predictor + Pydantic schemas
│   └── monitoring/      # Drift & performance monitoring
├── api/                 # FastAPI application
├── notebooks/           # Exploration & Databricks training notebooks
├── tests/               # Automated tests
├── databricks/          # Databricks asset bundles and jobs
├── infrastructure/      # Cloud infrastructure definitions
├── .github/workflows/   # CI/CD
└── docs/                # Architecture and technical documentation
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

The complete local pipeline can also be executed with:

```bash
python run_pipeline.py
```

## Extracted Logic

| Original Assessment Script | Production Module |
|---------------------------|-------------------|
| `deliverable_1_data_quality.py` | `src/data/validation.py` |
| `deliverable_2_data_preparation.py` | `src/data/preprocessing.py` + `src/features/build_features.py` |
| `deliverable_3_baseline_model.py` | `src/models/train_baseline.py` + `src/models/train_xgboost.py` |
| `deliverable_4_evaluation_pack.py` | `src/models/evaluate.py` |

## Delivery Roadmap

1. **Production data science pipeline** – leakage-safe preprocessing, reproducible training and evaluation
2. **MLflow tracking and model registry** – track datasets, parameters, metrics, artifacts and model versions
3. **GCP data lake + Databricks medallion architecture** – GCS Bronze → Silver → Gold data processing
4. **Databricks workflows** – orchestrate ingestion, validation, feature engineering, training and evaluation
5. **Production serving and monitoring** – FastAPI inference, drift detection, performance monitoring and retraining triggers

## License

Proprietary – Netcare
