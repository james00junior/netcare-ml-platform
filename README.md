# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

## Architecture

```text
Hospital / Clinical Sources
          ↓
          GCP
          ↓
Google Cloud Storage
          ↓
Databricks on GCP
Bronze → Silver → Gold
          ↓
Unity Catalog
          ↓
MLflow + Quality Gate
          ↓
UC Model Registry
          ↓
Databricks Model Serving
          ↓
FastAPI / Cloud Run
          ↓
GCP API Gateway
```

## Complete production lifecycle

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Project Engineering Foundation | **COMPLETE** |
| Phase 1 | Production ML Pipeline | **COMPLETE / FROZEN** |
| Phase 2 | MLflow Experiment Tracking | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 3 | GCS + Medallion Data Architecture | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 4 | Databricks Workflows | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 5 | Unity Catalog Governance | **FOUNDATION COMPLETE / FROZEN** |
| Phase 6 | Model Registry + Validation Gates | **COMPLETE / FROZEN** |
| Phase 7 | GitHub CI/CD + Databricks Bundles | **COMPLETE** |
| Phase 8 | Databricks Model Serving | **IN PROGRESS / v8 VALIDATED** |
| Phase 9 | Cloud Run Integration API | **NEXT** |
| Phase 10 | Security + Secrets + IAM | **PENDING** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

Phases 1–6 are closed and frozen. The permanent production baseline is protected. No Phase 1–6 component is modified as part of current serving work.

## Phase 8 — Databricks Model Serving

The first production serving implementation uses **Databricks Model Serving** rather than introducing another serving platform unnecessarily.

```text
Client System
      │ HTTPS
      ▼
Databricks Serving Endpoint
      │
      ▼
Production ML Model
      │
      ▼
Prediction
```

The model is exposed through the Databricks serving invocation API. The current validated candidate is model version `8` on an isolated serving endpoint.

### Current verified candidate: v8

Registered model:

```text
netcareaidatabricks.default.readmission_model
```

Model version:

```text
8
```

MLflow run:

```text
bf12e7f602084e78acdab4797c40c2b2
```

Isolated candidate endpoint:

```text
dev_james_mashiyane_za_dev-netcare-readmission-candidate
```

Verified v8 serving state:

```text
endpoint state:       READY
configuration:        NOT_UPDATING
served model:         readmission_model-8
model version:        8
traffic:              100%
deployment:           DEPLOYMENT_READY
workload:             Small / CPU
scale to zero:        enabled
```

`Scaled to zero` is an idle-state message and is not a deployment failure.

### v8 inference contract

Required inputs:

```text
age
sex
admission_type
admission_source
discharge_disposition
length_of_stay_days
icu_hours
num_prior_admissions_12m
num_ed_visits_12m
primary_diagnosis_group
secondary_diagnosis_count
elixhauser_score
wbc
has_diabetes
has_hypertension
has_ckd
has_copd
has_heart_failure
num_medications
had_surgery
had_icu_stay
discharge_to_home
followup_booked
payer_type
```

Optional inputs:

```text
creatinine
hemoglobin
sodium
potassium
```

Outputs:

```text
predicted_label
probability
risk_tier
model_version
```

The exact MLflow model signature has been verified from registered v8 metadata.

### Direct v8 inference validation

The exact 28-field contract was successfully sent through the existing `DatabricksServingClient` to the isolated v8 candidate endpoint. Inference executed on **Databricks Model Serving**, not on the local Mac.

Observed response:

```text
predicted_label: 0
probability: 0.30573779349128066
risk_tier: medium
model_version: champion
```

The endpoint configuration independently establishes that the served model was version `8` (`readmission_model-8`). The response `model_version: champion` is produced by the current serving wrapper and is not the serving entity version.

## Phase 9 — Cloud Run Integration API

Real client systems should not depend directly on internal ML infrastructure. The integration layer provides a stable external contract.

```text
Existing Hospital System
          │
          ▼
     GCP API Gateway
          │
          ▼
Integration Service
   (Cloud Run / FastAPI)
          │
          ▼
Databricks Model Serving
```

The integration service will handle:

- API versioning
- request validation
- authentication
- request transformation
- error handling
- model endpoint communication
- response formatting

The client contract will be:

```text
POST /v1/predictions/readmission
```

The internal model, features, Databricks model version, and serving infrastructure can evolve without breaking the external integration contract.

## Phase 10 — Security + Secrets + IAM

Production credentials must be managed through GCP-native controls.

```text
Google Secret Manager
        │
        ▼
Cloud Run / CI-CD / Databricks
```

Secrets must never be stored in committed `.env` files, Python source, or notebooks.

Production controls include:

- IAM
- service accounts
- Google Secret Manager
- Databricks secrets

## Phase 11 — Monitoring + Observability

Monitoring will operate at three levels.

### Infrastructure

Monitor API latency, errors, uptime, and throughput using **Cloud Monitoring** and **Cloud Logging**.

### Data

Monitor missing values, schema changes, data drift, and distribution changes.

### Model

Monitor prediction distribution, model confidence, actual outcomes, ROC-AUC, Recall, Precision, and F1.

The production outcome feedback loop is:

```text
Prediction
    │
    ▼
Prediction log
    │
    ▼
Actual outcome arrives later
    │
    ▼
Join prediction + outcome
    │
    ▼
Calculate production performance
```

## Phase 12 — Drift + Retraining

The production system will detect significant drift and trigger controlled retraining.

```text
Production Data
      │
      ▼
Drift Detection
      │
      ├── No drift → Continue
      │
      ▼
Significant drift
      │
      ▼
Retraining Workflow
      │
      ▼
Model Evaluation
      │
      ├── Worse → Reject
      │
      ▼
Better
      │
      ▼
Register New Version
      │
      ▼
Deploy
```

Retraining may be scheduled, triggered by drift, or triggered by new labelled data.

## Phase 13 — Canary + Production Releases

Production model releases will support gradual traffic shifting and rollback.

```text
Model v1 → Production
```

Then:

```text
Model v1 → 90%
Model v2 → 10%
```

If the new model performs safely:

```text
Model v1 → 50%
Model v2 → 50%
```

Finally:

```text
Model v2 → 100%
```

Rollback:

```text
Model v2 fails
      ↓
Traffic returns to v1
```

## Technology stack

- **Cloud:** GCP
- **Storage:** Google Cloud Storage
- **Data / orchestration:** Databricks on GCP
- **Storage format:** Delta Lake
- **Governance:** Unity Catalog
- **Experiment tracking:** MLflow
- **Models:** scikit-learn Logistic Regression and HistGradientBoosting
- **Serving:** Databricks Model Serving
- **Integration API:** FastAPI on Cloud Run
- **API Gateway:** GCP API Gateway
- **Secrets:** GCP Secret Manager and Databricks secrets
- **CI/CD:** GitHub Actions + Databricks Bundles
- **Observability:** Cloud Monitoring / Cloud Logging

The baseline workload is CPU-based tabular classification.

## Repository structure

```text
netcare-ml-platform/
├── src/
├── api/
├── notebooks/
├── databricks/
├── infrastructure/
├── tests/
├── docs/
├── .github/workflows/
└── run_pipeline.py
```

## Data architecture

**Bronze** — raw landing data.

**Silver** — validated and standardized encounter data.

**Gold** — approved analytics and ML features.

### Unity Catalog

Verified registered model:

```text
netcareaidatabricks.default.readmission_model
```

The registered model uses the verified `default` schema.

## ML lifecycle

```text
Data → Validation → Leakage-safe preprocessing
     → Train/Test → Evaluation → MLflow candidate
     → Quality Gate → Register → Promote champion
     → Databricks Model Serving
     → Integration API → Production Release
```

Quality gates require ROC-AUC ≥ 0.70, Recall ≥ 0.60, data validation, model tests, and no unacceptable regression when a production comparison is available.

## Development and deployment

GitHub is the source of truth for application code and deployment configuration.

```text
GitHub → CI → Bundle validation → DEV → STAGING → PRODUCTION
```

Credentials and tokens must never be committed.

## Engineering principles

- Evidence before claims.
- Freeze known-good components before debugging unknown components.
- Make small, targeted changes.
- Repair failed candidates instead of unnecessarily abandoning them.
- Preserve rollback paths.
- Match infrastructure to workload requirements.
- Minimize patient data in logs and telemetry.

Detailed engineering investigations belong in `docs/`; the README records the current verified architecture and status.
