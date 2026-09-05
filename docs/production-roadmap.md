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
| Phase 9 | Existing-System Integration via Databricks Serving | **REDESIGNED — IN PROGRESS** |
| Phase 10 | Security + Secrets + IAM | **PENDING** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–8 are closed. Their validated implementation is not modified while Phase 9–13 work proceeds. The protected v1 production baseline is never touched.

## Architecture Decision — Simplified Databricks-Centric Serving

The assessment does not require a separate Cloud Run or API Gateway layer. Databricks Model Serving already provides the production model-serving boundary required for the readmission prediction workload.

The simplified architecture is:

```text
Existing Hospital / Client System
              │
              │ HTTPS + JSON
              ▼
      Databricks Model Serving
              │
              ▼
          Model v8
              │
              ▼
          Prediction
```

GitHub remains the source of truth for application code and deployment configuration. GCS remains the data-storage layer already implemented in Phase 3. Databricks remains the primary ML platform for workflows, MLflow, Unity Catalog, registry, governance, and serving.

**Decision:** do not introduce Cloud Run or GCP API Gateway unless a concrete future requirement justifies a separate integration boundary, custom API orchestration, protocol transformation, or API-management capability.

## Phase 8 — Production Model Serving

The validated serving implementation uses Databricks Model Serving.

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

Direct inference was successfully validated using the exact 28-field model contract.

Observed response:

```text
predicted_label: 0
probability: 0.30573779349128066
risk_tier: medium
model_version: champion
```

The endpoint configuration independently establishes that the served model is Registry version `8`. The response `model_version: champion` is produced by the serving wrapper and is not the serving entity version.

**Phase 8 is frozen.**

## Phase 9 — Existing-System Integration

Phase 9 is redesigned around the already validated Databricks serving boundary rather than adding a separate Cloud Run/API Gateway layer.

```text
Existing Hospital System
          │
          │ HTTPS / JSON
          ▼
Databricks Model Serving
          │
          ▼
     Serving v2
          │
          ▼
       Model v8
```

The external integration contract is based on the Databricks serving invocation API. The model remains independently versioned and governed in Unity Catalog.

The existing FastAPI/Databricks client implementation remains useful as a local integration adapter and test harness, but it is **not required as production infrastructure** for the simplified architecture.

Phase 9 implementation will document and validate:

- request/response contract
- authentication
- request validation
- error handling
- client-system integration
- serving endpoint versioning
- rollback-compatible model promotion

### Phase 9 success criterion

A representative client system can authenticate to Databricks Model Serving and successfully obtain a prediction from the validated Serving v2 / Model v8 endpoint without requiring Cloud Run or API Gateway.

## Phase 10 — Security and Secrets

Security will be implemented around the actual production boundary.

```text
Client Identity / Service Principal
              │
              ▼
     Databricks Authentication
              │
              ▼
        Model Serving
```

Never store API keys, Databricks tokens, GCP credentials, or database passwords in committed `.env` files, Python source, or notebooks.

Use least-privilege identity, service principals, Databricks secrets, and appropriate GCP controls for the GCS data layer.

## Phase 11 — Monitoring and Observability

Monitoring will operate at three levels.

### Platform

- serving latency
- request volume
- errors
- endpoint availability

### Data

- missing values
- schema changes
- feature distribution changes
- data drift

### Model

- prediction distribution
- confidence
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
      ▼
Better
      │
      ▼
Register New Version
      │
      ▼
Controlled Serving Release
```

Retraining can be scheduled, triggered by drift, or triggered by new labelled outcomes.

## Phase 13 — Production Model Release Strategy

Production releases will use Databricks Model Serving traffic controls and versioned model artifacts.

```text
Trusted Model
     │
     ▼
Candidate Model
     │
     ▼
Validation Gates
     │
     ▼
Controlled Traffic Shift
     │
     ▼
Production
```

Rollback returns traffic to the previously trusted model version.

## Complete lifecycle

```text
Data → Validation → Training → MLflow
     → Quality Gate → Unity Catalog Registry
     → Databricks Model Serving
     → Existing System Integration
     → Monitoring → Drift Detection
     → Retraining → Validation → Controlled Release
```

Phases 1–8 remain frozen. Phase 9 is now the Databricks-native existing-system integration boundary. Cloud Run and API Gateway are deliberately excluded from the baseline architecture unless a concrete requirement is introduced.
