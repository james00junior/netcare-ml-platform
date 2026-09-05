# Netcare ML Platform — Production Roadmap

This document is the source-of-truth roadmap for the production lifecycle. Completed milestones are frozen once validated by evidence.

## Milestone Status

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Project Engineering Foundation | **COMPLETE / FROZEN** |
| Phase 1 | Production ML Pipeline | **COMPLETE / FROZEN** |
| Phase 2 | MLflow Experiment Tracking | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 3 | GCS + Medallion Data Architecture | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 4 | Databricks Workflows | **IMPLEMENTED / VALIDATED / FROZEN** |
| Phase 5 | Unity Catalog Governance | **FOUNDATION COMPLETE / FROZEN** |
| Phase 6 | Model Registry + Validation Gates | **COMPLETE / FROZEN** |
| Phase 7 | GitHub CI/CD + Databricks Bundles | **COMPLETE / FROZEN** |
| Phase 8 | Databricks Model Serving | **COMPLETE / FROZEN — Serving v2 / Model v8 VALIDATED** |
| Phase 9 | Cloud Run Integration API | **CORE INTEGRATION VALIDATED — CLOUD RUN / API GATEWAY PENDING** |
| Phase 10 | Security + Secrets + IAM | **PENDING** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–8 are closed. Their validated implementation is not modified while Phase 9–13 work proceeds. The protected v1 production baseline is never touched.

## Phase 8 — Production Model Serving

The first serving implementation uses **Databricks Model Serving** rather than introducing another serving platform unnecessarily.

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

### Validated milestone: Serving v2 → Registry Model v8

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

Direct inference was successfully validated using the exact 28-field model contract. Observed response:

```text
predicted_label: 0
probability: 0.30573779349128066
risk_tier: medium
model_version: champion
```

The endpoint configuration independently establishes that the served model is Registry version `8`. The response `model_version: champion` is produced by the serving wrapper and is not the serving entity version.

**Phase 8 is now frozen.**

## Phase 9 — Integration Layer for Existing Systems

Real client systems should not depend directly on internal ML infrastructure.

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

### Validated milestone: FastAPI → Databricks inference boundary

FastAPI on `0.0.0.0:8080` was validated with the governed Databricks backend.

Health:

```text
status:         ok
model_loaded:   true
model_version:  databricks-serving
environment:    dev
```

Single-record inference through FastAPI:

```text
predicted_label: 0
probability: 0.30573779349128066
model_version: champion
risk_tier: medium
```

Batch inference through FastAPI:

```text
record 1 → label=0, probability=0.30573779349128066, risk_tier=medium
record 2 → label=0, probability=0.24432526104648977, risk_tier=low
```

The complete validated local integration boundary is:

```text
FastAPI :8080
      ↓
DatabricksServingClient
      ↓
Serving v2
      ↓
Registry Model v8
      ↓
Prediction
```

**Phase 9 core inference integration is now frozen.** Remaining Phase 9 work is infrastructure deployment only: Cloud Run and GCP API Gateway.

Client contract:

```text
POST /v1/predictions/readmission
```

The integration service provides:

- API versioning
- request validation
- authentication
- transformation
- error handling
- model endpoint communication
- response formatting

## Phase 10 — Security and Secrets

GCP-native security controls:

```text
Google Secret Manager
       │
       ▼
Databricks / Cloud Run / CI-CD
```

Never store API keys, GCP credentials, Databricks tokens, or database passwords in committed `.env` files, Python source, or Databricks notebooks.

Use:

- IAM
- service accounts
- Google Secret Manager
- Databricks secrets

## Phase 11 — Monitoring and Observability

Three monitoring layers will be implemented.

### Infrastructure

- API latency
- errors
- uptime
- throughput

Use Cloud Monitoring and Cloud Logging.

### Data

- missing values
- schema changes
- data drift
- distribution changes

### Model

- prediction distribution
- model confidence
- actual outcomes
- ROC-AUC
- Recall
- Precision
- F1

## Phase 12 — Drift Detection and Retraining

```text
Production Data
      │
      ▼
Drift Detection
      │
      ├── No drift → Continue
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
      ▼
Better
      │
      ▼
Register New Version
      │
      ▼
Deploy
```

Retraining can be scheduled, triggered by drift, or triggered by new labelled data.

## Phase 13 — Production Model Release Strategy

Production releases will support gradual traffic shifting and rollback.

```text
Model v1 → Production
Model v1 → 90%   / Model v2 → 10%
Model v1 → 50%   / Model v2 → 50%
Model v2 → 100%
```

Rollback returns traffic to the previously trusted production model.

## Complete lifecycle

```text
Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
                                                        ↓
Phase 7 → Phase 8 → Phase 9 → Phase 10 → Phase 11 → Phase 12 → Phase 13
```

Phases 1–8 are frozen. Phase 9 core inference integration is frozen. Remaining work begins with Phase 9 Cloud Run deployment and GCP API Gateway exposure, followed by Phases 10–13.
