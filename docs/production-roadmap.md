# Netcare ML Platform — Production Roadmap

This document is the source-of-truth roadmap for the production lifecycle after the frozen Phase 1–6 foundations.

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

The model is exposed as an API. The current Phase 8 candidate is model version 8, validated on an isolated Databricks serving endpoint with successful direct inference.

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

The integration service provides a stable external contract and handles:

- API versioning
- request validation
- authentication
- transformation
- error handling
- model endpoint communication
- response formatting

Client contract:

```text
POST /v1/predictions/readmission
```

Internal model choice, features, Databricks model version, and serving infrastructure can evolve without breaking existing clients.

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

Monitor:

- API latency
- errors
- uptime
- throughput

Use Cloud Monitoring and Cloud Logging.

### Data

Monitor:

- missing values
- schema changes
- data drift
- distribution changes

### Model

Monitor:

- prediction distribution
- model confidence
- actual outcomes
- ROC-AUC
- Recall
- Precision
- F1

Outcome feedback loop:

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

## Phase 12 — Drift Detection and Retraining

The production lifecycle becomes:

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

Retraining can be:

- scheduled
- triggered by drift
- triggered by new labelled data

## Phase 13 — Production Model Release Strategy

Production releases will support gradual traffic shifting and rollback.

```text
Model v1 → Production
```

Then:

```text
Model v1 → 90%
Model v2 → 10%
```

Monitor the new model before increasing traffic:

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

## Complete lifecycle

```text
┌─────────────────────────────────────┐
│          PHASE 0                    │
│  Project Engineering Foundation     │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 1                    │
│  Production ML Pipeline             │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 2                    │
│  MLflow Experiment Tracking         │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 3                    │
│  GCS + Medallion Data Architecture  │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 4                    │
│  Databricks Workflows               │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 5                    │
│  Unity Catalog Governance           │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 6                    │
│  Model Registry + Validation Gates  │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 7                    │
│  GitHub CI/CD + Databricks Bundles  │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 8                    │
│  Databricks Model Serving           │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 9                    │
│  Cloud Run Integration API          │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 10                   │
│  Security + Secrets + IAM           │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 11                   │
│  Monitoring + Observability         │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 12                   │
│  Drift + Retraining                 │
└──────────────────┬──────────────────┘
                   ▼
┌─────────────────────────────────────┐
│          PHASE 13                   │
│  Canary + Production Releases       │
└─────────────────────────────────────┘
```

Phases 1–6 remain frozen. Phase 7 is the completed CI/CD and Databricks Bundles foundation. Phase 8 is the current active production-serving phase; Phases 9–13 follow in order.