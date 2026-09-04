# Netcare ML Platform

Production ML platform for **30-day hospital readmission prediction**, designed for deployment on **Google Cloud Platform (GCP)** with **Databricks on GCP**.

## 1. Platform objective

The platform turns hospital encounter data into a governed, production-ready machine-learning service that can:

- ingest and validate hospital data;
- build leakage-safe ML features;
- train and evaluate readmission models;
- track experiments and artifacts with MLflow;
- register and govern models in Unity Catalog;
- promote only quality-approved models to the `champion` alias;
- serve approved models through Databricks Model Serving;
- expose a stable external API through FastAPI and GCP API Gateway;
- monitor data, model performance and infrastructure;
- detect drift and trigger controlled retraining;
- support staged model releases and rollback.

## 2. Target production architecture

```text
Hospital / Clinical Source Systems
              │
              ▼
      GCP API / Data Ingestion
              │
              ▼
   Google Cloud Storage (GCS)
              │
              ▼
   ┌──────────────────────────┐
   │ Databricks on GCP        │
   │ Delta / Medallion        │
   │                          │
   │ Bronze → Silver → Gold   │
   └────────────┬─────────────┘
                │
                ▼
         Unity Catalog
      ┌─────────┴─────────┐
      │                   │
   Data assets       ML assets
                          │
                          ▼
                    MLflow Tracking
                          │
                          ▼
                  Quality Gate
                          │
                          ▼
                 UC Model Registry
                          │
                 champion alias
                          │
                          ▼
              Databricks Model Serving
                          │
                          ▼
                    Cloud Run
                     FastAPI
                          │
                          ▼
                  GCP API Gateway
                          │
                          ▼
                  Hospital Systems

Monitoring / Logging / Security span all layers.
```

## 3. Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Cloud | **GCP** | Primary cloud platform |
| Data lake | **Google Cloud Storage** | Raw and curated data storage |
| Data engineering | **Databricks on GCP** | Distributed processing and orchestration |
| Storage format | **Delta Lake** | Reliable analytical tables |
| Architecture | **Bronze / Silver / Gold** | Data quality and transformation boundaries |
| Governance | **Unity Catalog** | Catalogs, schemas, permissions, lineage and ML assets |
| Experiment tracking | **MLflow** | Parameters, metrics, artifacts and runs |
| Model registry | **Unity Catalog + MLflow** | Governed model versions and aliases |
| Training | **scikit-learn / HistGradientBoosting** | Readmission classification |
| Serving | **Databricks Model Serving** | Managed production inference |
| Integration | **FastAPI / Cloud Run** | Stable external API contract |
| API gateway | **GCP API Gateway** | External API entry point and controls |
| Secrets | **GCP Secret Manager** | Credential and secret management |
| CI/CD | **GitHub Actions** | Quality gates and deployment automation |
| Observability | **Cloud Monitoring / Cloud Logging** | Infrastructure and application monitoring |

## 4. Repository structure

```text
netcare-ml-platform/
├── src/
│   ├── config/              # Runtime and model configuration
│   ├── data/                # Ingestion, validation, preprocessing
│   ├── features/            # Feature construction
│   ├── models/              # Training, evaluation, registry, promotion
│   ├── serving/             # Production predictor and schemas
│   └── monitoring/          # Drift and performance monitoring
├── api/                     # FastAPI application
├── notebooks/               # Exploration and Databricks notebooks
├── databricks/
│   ├── databricks.yml       # Declarative Automation Bundle
│   ├── resources/           # Databricks jobs/resources
│   └── sql/                 # Unity Catalog bootstrap/governance SQL
├── infrastructure/          # Cloud infrastructure definitions
├── tests/                   # Automated tests
├── docs/                    # Architecture, governance and API docs
├── .github/workflows/       # CI/CD pipelines
└── run_pipeline.py          # Local end-to-end pipeline
```

## 5. Data architecture

### Bronze

Raw landing layer. Data is retained close to source format and is not used directly for model training.

### Silver

Validated and standardized clinical/encounter data. Typical processing includes schema checks, missing-value handling, categorical normalization and duplicate detection.

### Gold

Analytics- and ML-ready datasets containing approved features for downstream training and serving.

### Unity Catalog

The current governance design uses the `nectare` catalog:

```text
nectare
├── bronze
├── silver
├── gold
└── ml
```

The ML assets include:

```text
nectare.ml.readmission_features
nectare.ml.readmission_model
```

## 6. ML lifecycle

```text
Raw Data
   ↓
Validation
   ↓
Train/Test Split
   ↓
Leakage-safe Preprocessing
   ↓
Model Training
   ↓
Evaluation
   ↓
MLflow Experiment
   ↓
Quality Gate
   ↓
UC Registered Model
   ↓
Approved Version
   ↓
champion Alias
   ↓
Model Serving
```

A model is **not promoted merely because training succeeded**.

The quality gate requires:

- ROC-AUC ≥ 0.70;
- Recall ≥ 0.60;
- data validation passed;
- model tests passed;
- candidate performance must not regress against the production model when production comparison is required.

Unity Catalog aliases are used for lifecycle management rather than legacy MLflow model stages.

## 7. Current model baseline

The leakage-safe local pipeline currently evaluates:

| Model | Accuracy | ROC-AUC | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.653 | 0.710 | 0.692 | 0.509 |
| HistGradientBoosting | 0.713 | 0.711 | 0.628 | 0.533 |

These are development/assessment results on the supplied dataset, **not production clinical performance claims**.

## 8. Development, staging and production

The intended promotion path is:

```text
GitHub
   ↓
CI quality gates
   ↓
Databricks Bundle validation
   ↓
DEV
   ↓
STAGING
   ↓
PRODUCTION
```

Environment-specific configuration must be supplied through deployment configuration and secret management. Credentials must never be committed to the repository.

## 9. Production API

The external integration contract will be versioned independently of the model implementation:

```text
POST /v1/predictions/readmission
```

Example request:

```json
{
  "age": 67,
  "gender": "Female",
  "admission_type": "Emergency",
  "length_of_stay": 5,
  "creatinine": 1.4,
  "hemoglobin": 11.2
}
```

Example response:

```json
{
  "prediction": "high_risk",
  "probability": 0.78,
  "model_version": "4"
}
```

The final production contract will be aligned with the actual model-serving input schema before deployment.

## 10. Security

Production security design:

- GCP IAM and service accounts for workload identity;
- GCP Secret Manager for application and integration secrets;
- Databricks permissions and Unity Catalog grants for data/model access;
- least-privilege service accounts;
- no credentials in source code, notebooks or committed `.env` files;
- no raw patient-identifying values in MLflow prediction logs;
- API authentication and authorization at the integration layer.

## 11. Monitoring

### Infrastructure

- API latency
- request volume
- error rates
- endpoint availability
- Cloud Run health
- Databricks job failures

### Data

- schema changes
- missing-value rates
- categorical distribution changes
- feature drift

### Model

- prediction distribution
- confidence distribution
- ROC-AUC
- Recall
- Precision
- F1
- degradation against the approved baseline

### Outcome feedback

```text
Prediction
   ↓
Prediction Log
   ↓
Actual Outcome Arrives
   ↓
Prediction + Outcome Join
   ↓
Production Metrics
   ↓
Quality / Retraining Decision
```

## 12. Retraining

Retraining will be controlled rather than unconditional:

```text
Production Data
      ↓
Drift / New Labels / Schedule
      ↓
Retraining Job
      ↓
Validation
      ↓
Training
      ↓
Evaluation
      ↓
Quality Gate
   ┌──┴──┐
 Reject  Approve
   │       │
   │       ▼
   │   Register Version
   │       ↓
   │   Promote Alias
   │       ↓
   │   Deploy
   └───────┘
```

## 13. Release strategy

Production releases will support staged rollout:

```text
Model v1 → 100%

Model v1 → 90%     Model v2 → 10%

Model v1 → 50%     Model v2 → 50%

Model v2 → 100%
```

If v2 fails production checks, traffic can be returned to v1.

## 14. Delivery phases

1. **Production Data Science Pipeline** — complete
2. **MLflow Tracking and Registry** — foundation implemented
3. **GCP Data Lake + Databricks Medallion** — architecture and repository foundation
4. **Databricks Workflows** — bundle/job foundation
5. **Unity Catalog Governance** — catalog, schemas and grants foundation
6. **Model Registry and Promotion** — quality gate, UC aliases and promotion tests in progress
7. **CI/CD with GitHub Actions + Databricks** — DEV/STAGING/PROD deployment workflows
8. **Production Model Serving** — Databricks Model Serving
9. **Integration Layer** — Cloud Run/FastAPI + GCP API Gateway
10. **Security and Secrets** — IAM + Secret Manager + workload identity
11. **Monitoring and Observability** — Cloud Monitoring/Logging + data/model monitoring
12. **Drift Detection and Retraining** — automated controlled retraining
13. **Production Release Strategy** — canary/staged release and rollback

## 15. Current status

**Phase 6 — Model Registry and Promotion is the active phase.**

The next engineering objective is to complete the Phase 6 governed lifecycle, then move to Phase 7 CI/CD validation and deployment.

Cloud deployment is intentionally environment-dependent: the repository defines the architecture and deployment assets, while actual GCP and Databricks resources require the corresponding customer/workspace credentials and configuration.

## License

Proprietary – Netcare
