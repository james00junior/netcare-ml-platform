# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed as a **Databricks-centric production ML system on GCP**.

## Architecture

```text
Hospital / Clinical Sources
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
Existing Hospital / Application Systems
```

GitHub provides source control and CI/CD; GCS provides cloud data storage; Databricks provides the ML lifecycle, governance, orchestration, registry, and serving platform.

The architecture deliberately avoids an additional API compute layer unless a future enterprise requirement justifies it. Cloud Run and API Gateway are not required for the core ML serving path.

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
| Phase 7 | GitHub CI/CD + Databricks Bundles | **COMPLETE / FROZEN** |
| Phase 8 | Databricks Model Serving | **COMPLETE / FROZEN — Serving v2 / Model v8 VALIDATED** |
| Phase 9 | Existing-System Integration via Databricks Serving | **NEXT** |
| Phase 10 | Security + Secrets + IAM | **PENDING** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

Phases 1–8 are closed and frozen. The protected production baseline and validated serving candidate are not modified while later lifecycle work proceeds.

## Phase 8 — Databricks Model Serving

The production serving implementation uses **Databricks Model Serving** directly rather than introducing another serving platform unnecessarily.

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

The validated Phase 8 candidate is **Serving v2**, serving **registered model version 8** on an isolated serving endpoint.

### Current verified candidate: Serving v2 → Model v8

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

Verified serving state:

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

**Phase 8 is frozen.**

## Phase 9 — Existing-System Integration

The production integration boundary is deliberately simple: existing hospital or application systems call the Databricks serving endpoint over HTTPS using the approved authentication mechanism.

```text
Existing Hospital System
          │
          │ HTTPS + JSON
          ▼
Databricks Model Serving
          │
          ▼
Serving v2
          │
          ▼
Registry Model v8
          │
          ▼
Prediction
```

### Integration contract

```text
POST <Databricks serving endpoint>/invocations
```

Request contract:

```text
{
  "dataframe_records": [
    { ... model features ... }
  ]
}
```

Response contract:

```text
{
  "predictions": [
    {
      "predicted_label": 0,
      "probability": 0.30,
      "risk_tier": "medium",
      "model_version": "champion"
    }
  ]
}
```

The integration client already validates the serving response and normalises it into the application contract. FastAPI remains available as a local integration adapter/test harness, but is not a required production runtime component.

This design keeps the external integration contract stable while allowing the underlying model, model version, preprocessing implementation, and serving deployment to evolve independently.

### Why no Cloud Run or API Gateway?

Databricks Model Serving already provides the required HTTPS model inference boundary. Adding Cloud Run and API Gateway would introduce another runtime and authentication boundary without being necessary for the stated assessment requirements.

Additional GCP API infrastructure should only be introduced if the enterprise requires capabilities such as:

- custom business logic outside model inference
- protocol transformation
- API management policies
- a separate application security boundary
- aggregation of multiple backend services
- organisation-specific networking requirements

This minimises infrastructure cost and operational complexity while preserving a production-grade model lifecycle.

## Phase 10 — Security + Secrets + IAM

Production authentication will use approved Databricks identity mechanisms and least-privilege access.

```text
Hospital System / Service Identity
              │
              ▼
      Databricks Authentication
              │
              ▼
        Model Serving
              │
              ▼
        Unity Catalog
```

Secrets and credentials must never be stored in committed `.env` files, Python source, or notebooks.

Production controls include:

- least-privilege identities
- service principals where appropriate
- Unity Catalog permissions
- Databricks secret management
- credential rotation
- audit logging

## Phase 11 — Monitoring + Observability

Monitoring will operate at three levels.

### Infrastructure / Serving

- request latency
- error rate
- availability
- throughput
- serving resource utilisation

### Data

- missing values
- schema changes
- feature distribution changes
- data drift
- data quality failures

### Model

- prediction distribution
- confidence distribution
- actual outcomes
- ROC-AUC
- Recall
- Precision
- F1

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

Monitoring and alerting will be implemented primarily with Databricks-native telemetry, tables, jobs, and dashboards, with GCP monitoring used where appropriate for the underlying cloud resources.

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
      └── Significant drift
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

Databricks Model Serving supports controlled model deployment and traffic management.

```text
Trusted Model
      │
      ▼
Candidate Model
      │
      ▼
Validation
      │
      ▼
Controlled Traffic Shift
      │
      ├── Healthy → Increase traffic
      │
      └── Unhealthy → Roll back
```

A production release maintains a previously trusted model so rollback can be performed without retraining.

## Technology stack

- **Cloud:** GCP
- **Storage:** Google Cloud Storage
- **Data / orchestration:** Databricks on GCP
- **Storage format:** Delta Lake
- **Governance:** Unity Catalog
- **Experiment tracking:** MLflow
- **Models:** scikit-learn Logistic Regression and HistGradientBoosting
- **Serving:** Databricks Model Serving
- **Integration:** HTTPS / JSON directly to Databricks Model Serving
- **CI/CD:** GitHub Actions + Databricks Bundles
- **Monitoring:** Databricks-native telemetry, tables and dashboards + GCP monitoring where appropriate

The baseline workload is CPU-based tabular classification.

## Repository structure

```text
netcare-ml-platform/
├── src/
├── api/
├── notebooks/
├── databricks/
├── tests/
├── docs/
├── .github/workflows/
└── run_pipeline.py
```

The `api/` package is retained as a local/test integration adapter; it is not required as a production serving layer.

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
     → Existing System Integration
     → Monitoring → Drift Detection
     → Retraining → Validation → Controlled Release
```

Quality gates require ROC-AUC ≥ 0.70, Recall ≥ 0.60, data validation, model tests, and no unacceptable regression when a production comparison is available.

## Development and deployment

GitHub is the source of truth for application code and deployment configuration.

```text
Developer
   ↓
GitHub
   ↓
CI/CD
   ↓
Databricks Bundle Validation
   ↓
Databricks DEV
   ↓
STAGING
   ↓
PRODUCTION
```

Credentials and tokens must never be committed.

## Engineering principles

- Evidence before claims.
- Freeze known-good components before debugging unknown components.
- Make small, targeted changes.
- Repair failed candidates instead of unnecessarily abandoning them.
- Preserve rollback paths.
- Match infrastructure to workload requirements.
- Prefer the minimum architecture that satisfies the requirements.
- Minimize patient data in logs and telemetry.

Detailed engineering investigations belong in `docs/`; the README records the current verified architecture and status.
