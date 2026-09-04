# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

> **Platform constraint:** Azure is not part of this architecture or implementation. All cloud, data, ML lifecycle, serving and CI/CD decisions in this repository target GCP + Databricks on GCP.

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| Phase 1 — Production Data Science Pipeline | COMPLETE | Leakage-safe preprocessing, baseline models, evaluation, persisted artifacts and automated tests |
| Phase 2 — MLflow Tracking / Registry | IMPLEMENTED / VALIDATED | MLflow tracking and registry foundations exercised in Databricks |
| Phase 3 — GCP Data Lake + Databricks Medallion | IMPLEMENTED / VALIDATED | GCS dataset accessed successfully from Databricks |
| Phase 4 — Databricks Workflows | IMPLEMENTED / VALIDATED | Bundle deployment and repeated successful DEV training runs |
| Phase 5 — Unity Catalog | FOUNDATION COMPLETE | Verified catalog/schema and governance configuration |
| Phase 6 — Model Registry & Promotion | **COMPLETE** | UC model registered successfully; model versions READY; version 3 promoted to `champion` |
| Phase 7 — Production Model Serving & Inference | **IN PROGRESS** | Serving endpoint exists; packaging fix being validated before promotion to serving |
| Phase 8–13 | PENDING | — |

## 1. Platform objective

The platform turns hospital encounter data into a governed machine-learning service that can:

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
| Data lake | **Google Cloud Storage** | Durable raw and curated data storage |
| Data engineering | **Databricks on GCP** | Processing and orchestration |
| Storage format | **Delta Lake** | Reliable analytical tables |
| Architecture | **Bronze / Silver / Gold** | Data quality and transformation boundaries |
| Governance | **Unity Catalog** | Data/model governance, permissions and lineage |
| Experiment tracking | **MLflow** | Parameters, metrics, artifacts and runs |
| Model registry | **Unity Catalog + MLflow** | Governed model versions and aliases |
| Training | **scikit-learn / HistGradientBoosting** | Readmission classification |
| Serving | **Databricks Model Serving** | Managed inference |
| Integration | **FastAPI / Cloud Run** | External API integration |
| API gateway | **GCP API Gateway** | External API entry point |
| Secrets | **GCP Secret Manager** | Secret management |
| CI/CD | **GitHub Actions** | Automated quality and deployment gates |
| Observability | **Cloud Monitoring / Cloud Logging** | Infrastructure and application monitoring |

The current ML workload is **CPU-only**. No GPU is required for the baseline readmission models because the workload is small tabular classification rather than GPU-oriented deep learning.

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
├── docs/                    # Architecture and governance docs
├── .github/workflows/       # CI/CD pipelines
└── run_pipeline.py          # Local end-to-end pipeline
```

## 5. Data architecture

### Bronze
Raw landing layer. Source data is retained close to its original representation and is not used directly for model training.

### Silver
Validated and standardized encounter data. Processing includes schema validation, missing-value handling, categorical normalization and duplicate handling as appropriate.

### Gold
Analytics- and ML-ready datasets containing approved features for downstream training and serving.

### Unity Catalog

The verified DEV Unity Catalog namespace currently used by the model registry is:

```text
netcareaidatabricks.default.readmission_model
```

The verified catalog currently exposes `default` and `information_schema` schemas. The model is **not** registered under a separate `ml` schema.

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
Serving Deployment
```

The Phase 6 quality gate requires:

- ROC-AUC ≥ 0.70;
- Recall ≥ 0.60;
- data validation passed;
- model tests passed;
- no unacceptable regression against the production model when a production comparison is available.

Phase 6 has now been demonstrated in the target Databricks environment. The verified Unity Catalog model is `netcareaidatabricks.default.readmission_model`; versions 1, 2 and 3 are READY, and **version 3 currently owns the `champion` alias**.

### Quality-gate remediation

An early candidate reached the quality gate but was rejected because recall was missing from the returned metric dictionary. The gate was correctly strict. The training/evaluation implementation was fixed to calculate recall explicitly rather than weakening the acceptance threshold.

## 7. Current model baseline

| Model | Accuracy | ROC-AUC | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.653 | 0.710 | 0.692 | 0.509 |
| HistGradientBoosting | 0.713 | 0.711 | 0.628 | 0.533 |

These are development/assessment results on the supplied dataset and **must not be interpreted as production clinical performance claims**.

## 8. Development, staging and production

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

Environment-specific configuration belongs in deployment configuration and secret management. Credentials must never be committed to the repository.

## 9. Phase 7 — Production Model Serving & Inference

Phase 7 is currently focused on proving that the governed UC model can be packaged and loaded reliably by Databricks Model Serving.

### Serving contract

The production model accepts raw patient feature records matching the MLflow signature. The model applies the fitted preprocessing pipeline and returns:

```text
predicted_label
probability
risk_tier
model_version
```

The external API contract is:

```text
POST /v1/predictions/readmission
```

### Champion deployment model

The Unity Catalog `champion` alias is mutable, while a Databricks serving configuration uses an explicit model version. Therefore deployment resolves the approved `champion` version and deploys that concrete version.

```text
Quality Gate
     ↓
UC registered version
     ↓
champion alias
     ↓
Resolve champion → concrete version
     ↓
Databricks Model Serving
```

A later promotion does not silently change an already deployed serving configuration; the deployment process must explicitly reconcile the endpoint with the newly promoted version.

### Current serving validation

A DEV serving endpoint has been created:

```text
dev_james_mashiyane_za_dev-netcare-readmission
```

The endpoint's existing version 1 configuration remains healthy. A subsequent configuration using model version 2 failed during model loading with:

```text
ModuleNotFoundError: No module named 'src'
```

The diagnostic showed the failure occurs while MLflow/cloudpickle deserializes `python_model.pkl`, not during installation of the declared PyPI dependencies.

The model artifact for the current champion version was inspected before another endpoint update. Its `MLmodel` contains:

```text
python_model: python_model.pkl
code: null
```

and the artifact contains no packaged `src/` tree. This explains why a model serialized with the class path `src.serving.mlflow_model.ReadmissionServingModel` cannot be loaded by the serving container.

The remediation is therefore being made at the **MLflow model packaging boundary**, before changing the healthy serving endpoint again.

### Phase 7 acceptance sequence

```text
Fix deterministic model packaging
          ↓
Local Ruff + Black + Pytest
          ↓
Databricks training
          ↓
Register new model version
          ↓
Inspect downloaded MLflow artifact
          ↓
Confirm serving code is self-contained
          ↓
Deploy candidate to Databricks Serving
          ↓
Wait for DEPLOYMENT_READY
          ↓
Direct serving inference test
          ↓
FastAPI integration test
          ↓
Phase 7 complete
```

The healthy serving configuration is retained as a rollback path until the new serving version passes deployment and inference validation.

## 10. Databricks on GCP

Databricks resources are managed as code through the Declarative Automation Bundle under `databricks/`.

The training job uses:

```text
GCS dataset
    ↓
Databricks on GCP
    ↓
c4-standard-4 preferred CPU node
    ↓
compatible alternate CPU node types
    ↓
Single-node DEV execution
```

The baseline workload is tabular classification using Logistic Regression and HistGradientBoosting. GPU infrastructure is not justified for this workload.

## 11. Infrastructure engineering decisions and lessons learned

The initial training configuration used small single-node CPU compute to minimize DEV cost and complexity. A real target-environment run exposed GCP capacity exhaustion:

```text
GCP_INSUFFICIENT_CAPACITY
ZONE_RESOURCE_POOL_EXHAUSTED
```

The response was to retain the CPU architecture while introducing automatic zone selection and compatible alternate CPU node types. This addresses placement rigidity without incorrectly adding GPUs or unnecessarily scaling the workload.

The broader engineering pattern is:

```text
Design assumption
      ↓
Target-environment execution
      ↓
Observed failure
      ↓
Layer-specific diagnosis
      ↓
Targeted remediation
      ↓
Repeat validation
```

## 12. Repeated target-environment validation

Successful DEV training runs have repeatedly demonstrated:

- Databricks compute provisioning;
- packaged wheel installation;
- `src` imports inside the training runtime;
- GCS dataset access;
- data validation and preprocessing;
- candidate training and evaluation;
- strict quality-gate execution;
- Unity Catalog registration and promotion.

The latest verified training execution completed with `TERMINATED SUCCESS` and produced a new registered model version.

## 13. Security

Production security design:

- GCP IAM and service accounts for workload identity;
- GCP Secret Manager for application and integration secrets;
- Databricks permissions and Unity Catalog grants for data/model access;
- no credentials or tokens committed to GitHub;
- least-privilege access to data and ML assets;
- inference telemetry should avoid logging raw patient input values.

## 14. Monitoring

### Infrastructure
- API latency
- request/error rates
- service availability
- throughput
- Cloud Monitoring
- Cloud Logging

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

## 15. Retraining strategy

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

## 16. Release and rollback strategy

The deployment process resolves the governed `champion` alias to a concrete model version before updating the serving endpoint. The previous healthy serving version remains available until the replacement passes deployment and inference checks.

```text
Champion v3
    ↓
Deploy concrete v3
    ↓
DEPLOYMENT_READY
    ↓
Direct inference validation
    ↓
Traffic update
```

If the replacement fails, retain the previous healthy serving configuration and investigate the failed candidate rather than destabilizing production.

## 17. CI/CD

GitHub Actions is the source-controlled automation layer.

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

CI should reject defects rather than automatically weakening tests or quality thresholds.

## 18. Implementation roadmap

### Phase 1 — Production Data Science Pipeline
**Status: COMPLETE**

### Phase 2 — MLflow Tracking and Registry
**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

### Phase 3 — GCP Data Lake + Databricks Medallion
**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

### Phase 4 — Databricks Workflows
**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

### Phase 5 — Unity Catalog
**Status: FOUNDATION COMPLETE**

### Phase 6 — Model Registry & Promotion
**Status: COMPLETE**

Verified target-environment result:

```text
Model: netcareaidatabricks.default.readmission_model
Versions: 1, 2, 3 → READY
Champion: version 3
```

### Phase 7 — Production Model Serving & Inference
**Status: IN PROGRESS**

Current blocker is deterministic MLflow packaging of the serving PythonModel. The healthy serving configuration remains untouched while the packaging fix is validated.

Acceptance criteria:

- [ ] serving artifact is self-contained;
- [ ] Databricks Serving deployment reaches `DEPLOYMENT_READY`;
- [ ] direct inference succeeds;
- [ ] response contract is validated;
- [ ] FastAPI production integration succeeds;
- [ ] automated serving/integration tests pass;
- [ ] architecture documentation reflects the verified implementation.

### Phase 8–13
**Status: PENDING**

## 19. Engineering principles

- Evidence before claims.
- GitHub is the source of truth for application code.
- Target-environment validation is required for deployment claims.
- Small, explicit changes are preferred over speculative refactoring.
- Quality gates should be strict and explainable.
- Security and patient-data minimization are design requirements.
- Infrastructure should match workload requirements rather than assumptions.
- A failed deployment should preserve a known-good rollback path.
