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

## Phase status

| Phase | Status |
|---|---|
| Phase 1 — Production Data Science Pipeline | **COMPLETE** |
| Phase 2 — MLflow Tracking / Registry | **IMPLEMENTED / VALIDATED** |
| Phase 3 — GCP Data Lake + Databricks Medallion | **IMPLEMENTED / VALIDATED** |
| Phase 4 — Databricks Workflows | **IMPLEMENTED / VALIDATED** |
| Phase 5 — Unity Catalog | **FOUNDATION COMPLETE** |
| Phase 6 — Model Registry & Promotion | **COMPLETE** |
| Phase 7 — Production Model Serving & Inference | **IN PROGRESS** |
| Phase 8–13 | **PENDING** |

## Technology stack

- **Cloud:** GCP
- **Storage:** Google Cloud Storage
- **Data / orchestration:** Databricks on GCP
- **Storage format:** Delta Lake
- **Governance:** Unity Catalog
- **Experiment tracking:** MLflow
- **Models:** scikit-learn Logistic Regression and HistGradientBoosting
- **Serving:** Databricks Model Serving
- **API:** FastAPI, Cloud Run, GCP API Gateway
- **Secrets:** GCP Secret Manager
- **CI/CD:** GitHub Actions
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
     → Explicit serving deployment
```

Quality gates require ROC-AUC ≥ 0.70, Recall ≥ 0.60, data validation, model tests, and no unacceptable regression when a production comparison is available.

## Phase 6 — Model Registry & Promotion

Phase 6 is complete. Models are evaluated before registration and promotion. Unity Catalog provides governed model versions and the `champion` alias.

The deployment process resolves the approved alias to an explicit model version before serving deployment.

## Phase 7 — Production Model Serving & Inference

Phase 7 is validating the model artifact, serving, and inference boundaries.

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
deployment:            DEPLOYMENT_READY
workload:              Small / CPU
scale to zero:         enabled
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

The exact MLflow model signature has been verified from the registered v8 model metadata.

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

### Current Phase 7 position

```text
v8 training                 ✓
v8 registration             ✓
v8 model signature           ✓
v8 isolated deployment       ✓ DEPLOYMENT_READY
v8 direct inference          ✓ VALIDATED
FastAPI integration          → NEXT
Serving/integration tests    →
```

No production baseline is modified as part of this investigation.

Detailed serving evidence and historical candidate failures are maintained in `docs/phase-7-serving-debugging.md`.

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
