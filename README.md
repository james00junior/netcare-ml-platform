# Netcare ML Platform

Production ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

> **Platform constraint:** Azure is not part of this architecture or implementation. All cloud, data, ML lifecycle, serving and CI/CD decisions in this repository target GCP + Databricks on GCP.

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

## 6. ML lifecycle and Phase 6 governance

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
MLflow Experiment
   ↓
Candidate Evaluation
   ↓
Quality Gate
   ↓
Register Candidate
   ↓
Compare with Champion
   ↓
Promote `champion` Alias
   ↓
Model Serving
```

A model is **not promoted merely because training succeeded**.

The Phase 6 quality gate requires:

- ROC-AUC ≥ 0.70;
- Recall ≥ 0.60;
- data validation passed;
- model tests passed;
- candidate performance must not regress against the production model when production comparison is required.

Registration and promotion are separate operations. A registered model version receives the `champion` Unity Catalog alias only after the promotion gate passes. Unity Catalog aliases are used instead of legacy MLflow model stages.

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

## 9. Production inference architecture

The local FastAPI predictor uses the **same fitted preprocessing artifact produced during training**. This prevents production inference from independently refitting or reconstructing preprocessing logic.

The intended managed production path is:

```text
Client
  ↓
GCP API Gateway
  ↓
Cloud Run / FastAPI integration
  ↓
Databricks Model Serving
  ↓
Champion model
```

External API contract:

```text
POST /v1/predictions/readmission
```

The final production contract will be aligned with the actual Databricks serving input schema before deployment.

## 10. Databricks on GCP

Databricks resources are managed as code through the Declarative Automation Bundle under `databricks/`.

The current environment model is:

```text
                 databricks.yml
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
         DEV       STAGING       PROD
          │           │           │
          └────── Databricks ─────┘
                      │
                Unity Catalog
                      │
              Training / Serving
```

Actual workspace deployment remains environment-dependent. The repository contains the deployment definitions, but a real deployment requires the target GCP/Databricks workspace and authenticated deployment configuration.

## 11. Security

Production security design:

- GCP IAM and service accounts for workload identity;
- GCP Secret Manager for application and integration secrets;
- Databricks permissions and Unity Catalog grants for data/model access;
- no credentials or tokens committed to GitHub;
- least-privilege access to Bronze, Silver, Gold and ML assets;
- MLflow logging excludes raw patient input values from inference telemetry.

## 12. Monitoring

### Infrastructure

- API latency
- request/error rates
- service availability
- throughput
- Cloud Monitoring and Cloud Logging

### Data

- missing values
- schema changes
- distribution changes
- data drift

### Model

- prediction distribution
- confidence distribution
- ROC-AUC
- Recall
- Precision
- F1
- production degradation

### Outcome feedback

```text
Prediction
    ↓
Prediction log
    ↓
Actual outcome arrives later
    ↓
Join prediction + outcome
    ↓
Calculate production performance
```

## 13. Retraining strategy

```text
Production Data
      ↓
Drift / New Labels
      ↓
Retraining Workflow
      ↓
Candidate Evaluation
      ↓
Quality Gate
      ├── Fail → Reject
      ↓
Register Model Version
      ↓
Compare with Champion
      ├── Worse → Reject
      ↓
Promote Champion
      ↓
Deploy
```

Retraining may be scheduled, triggered by significant drift, or triggered by availability of new outcome labels.

## 14. Release and rollback strategy

The production model uses Unity Catalog aliases so that deployment targets a governed model reference rather than a hard-coded version.

Example staged rollout:

```text
Model v1 → 100% production

Model v2 → candidate

Model v2 → 10% traffic
Model v1 → 90% traffic

Model v2 → 50% traffic
Model v1 → 50% traffic

Model v2 → 100% traffic
```

If the new model fails production checks, traffic can be returned to the previous approved model version.

## 15. CI/CD

GitHub Actions is the source-controlled automation layer.

The normal CI quality gate is intentionally **immutable**:

```text
Push / Pull Request
       ↓
Install dependencies
       ↓
Ruff
       ↓
Black --check
       ↓
Pytest
       ↓
Coverage reporting
```

Automated format-and-commit workflows are not part of the permanent CI design.

## 16. Implementation roadmap

### Phase 1 — Production Data Science Pipeline

**Status: COMPLETE**

- leakage-safe preprocessing
- train/test split
- baseline model
- HistGradientBoosting model
- evaluation
- persisted model artifacts
- persisted fitted preprocessing
- production inference consistency
- automated tests

### Phase 2 — MLflow Tracking and Registry

**Status: PARTIAL**

- experiment tracking foundations
- model logging
- registry integration foundations
- Unity Catalog registry configuration

Remaining work is integrated governed lifecycle validation.

### Phase 3 — GCP Data Lake + Databricks Medallion

**Status: PARTIAL**

- GCS architecture
- Bronze/Silver/Gold design
- Databricks processing architecture

Actual cloud deployment and validation remain environment-dependent.

### Phase 4 — Databricks Workflows

**Status: PARTIAL**

- Databricks Bundle foundation
- environment targets
- training job resource

Actual workspace deployment and execution remain pending.

### Phase 5 — Unity Catalog

**Status: FOUNDATION COMPLETE**

- `nectare` catalog design
- Bronze/Silver/Gold/ML schemas
- governance SQL
- least-privilege grant templates
- governance documentation

### Phase 6 — Model Registry and Promotion

**Status: IN PROGRESS — CURRENT PHASE**

- quality gate implementation
- candidate-vs-production comparison
- Unity Catalog alias helpers
- governed promotion workflow
- promotion tests
- CI quality cleanup
- production preprocessing consistency fix

Remaining Phase 6 work: integrate the full candidate registration/promotion flow and validate it end-to-end.

### Phase 7 — CI/CD with GitHub Actions + Databricks

**Status: NEXT**

```text
GitHub
  ↓
GitHub Actions
  ↓
Quality Gates
  ↓
Databricks Bundle
  ↓
DEV
  ↓
STAGING
  ↓
PRODUCTION
```

### Phase 8 — Production Model Serving

**Status: PENDING**

Deploy approved Unity Catalog model versions through Databricks Model Serving.

### Phase 9 — Integration Layer

**Status: PENDING**

Build the GCP API Gateway → Cloud Run/FastAPI → Databricks Serving integration.

### Phase 10 — Security and Secrets

**Status: PENDING**

Implement production IAM, service accounts, Secret Manager and deployment secret handling.

### Phase 11 — Monitoring and Observability

**Status: PENDING**

Implement infrastructure, data, model and outcome monitoring.

### Phase 12 — Drift Detection and Retraining

**Status: PENDING**

Automate drift detection, retraining, validation and governed model promotion.

### Phase 13 — Production Model Release Strategy

**Status: PENDING**

Implement staged rollout, monitoring gates and rollback to the previous approved model.

## 17. Current engineering state

**Current phase: Phase 6 — Model Registry and Promotion.**

The repository is intentionally being advanced phase-by-phase. Before moving to the next phase, the current phase must be implemented, tested and documented.

### Source of truth

**GitHub `main` is the source of truth.** The development workflow is:

```text
Inspect GitHub
    ↓
Implement on GitHub
    ↓
Update README / architecture documentation
    ↓
CI verification
    ↓
User pulls main locally
    ↓
User runs local verification
    ↓
Continue to next phase
```

Do not introduce Azure resources, Azure deployment instructions or Azure-specific Databricks architecture into this repository. The target cloud architecture is **GCP + Databricks on GCP**.
