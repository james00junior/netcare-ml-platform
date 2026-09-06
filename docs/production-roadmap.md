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
| Phase 9 | Existing-System Integration via Databricks Serving | **COMPLETE / FROZEN** |
| Phase 10 | Security + Secrets + IAM | **IN PROGRESS** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–9 are closed. Their validated implementation is not modified while Phase 10–13 work proceeds. The protected v1 production baseline is never touched.

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

Phase 9 is complete and frozen around the already validated Databricks serving boundary rather than adding a separate Cloud Run/API Gateway layer.

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

The completed Phase 9 boundary includes request/response validation, authentication handling, retry/error handling, serving version awareness, and rollback-compatible model integration.

### Phase 9 success criterion — achieved

A representative client integration can authenticate to Databricks Model Serving and obtain a prediction from the validated Serving v2 / Model v8 endpoint without requiring Cloud Run or API Gateway.

## Phase 10 — Security and Secrets

Phase 10 is now implementing security around the actual production boundary.

```text
GitHub Actions
      │
      │ OIDC / Workload Identity Federation
      ▼
Databricks Authentication
      │
      ▼
Databricks Bundles
      │
      ▼
Model Serving
```

Production application/runtime credentials remain outside source control. GitHub CI/CD uses Databricks GitHub OIDC rather than a long-lived Databricks token.

Current Phase 10 controls include:

- `SecretStr` for runtime API keys and Databricks serving tokens
- GitHub OIDC authentication for Databricks deployment workflows
- `id-token: write` and `contents: read` workflow permissions
- environment-scoped Databricks host and client configuration
- standardised `DATABRICKS_HOST` bundle configuration across dev, staging, and prod
- pinned CI formatter/linter versions based on observed CI
- a committed record of verified build/runtime versions

A full dependency lock has not yet been committed; transitive dependency reproducibility therefore remains an explicit follow-up item.

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
     → Security / IAM
     → Monitoring → Drift Detection
     → Retraining → Validation → Controlled Release
```

Phases 1–9 remain frozen. Phase 10 is the active security and identity hardening phase. Cloud Run and API Gateway remain deliberately excluded from the baseline architecture unless a concrete requirement is introduced.
