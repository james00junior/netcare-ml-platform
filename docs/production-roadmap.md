# Netcare ML Platform — Production Roadmap

This document is the source-of-truth roadmap for the production lifecycle. Completed milestones are frozen once validated by evidence. The verification and change-control procedure is defined in [`docs/verification-record.md`](verification-record.md).

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
| Phase 10 | Security + Secrets + IAM | **DEPLOYMENT AUTHENTICATION + PRODUCTION DEPLOYMENT VALIDATED** |
| Phase 11 | Monitoring + Observability | **COMPLETE / FROZEN — VERIFIED MONITORING SCOPE** |
| Phase 12 | Drift + Retraining | **COMPLETE / FROZEN — SYNTHETIC VALIDATION SCOPE** |
| Phase 13 | Canary + Production Releases | **NEXT / FINAL LIFECYCLE PHASE** |

**Freeze rule:** Phases 1–12 are closed for their validated scopes. The protected v1 serving baseline remains frozen while Phase 13 is evaluated.

## Evidence rule

A milestone is not complete because code or documentation exists. The required sequence is:

```text
Inspect actual state
      ↓
Record exact evidence
      ↓
Make one targeted change
      ↓
Run lint / format / tests
      ↓
Verify CI for the exact commit
      ↓
Verify deployment for the exact commit (when applicable)
      ↓
Verify live Databricks state (when applicable)
      ↓
Update documentation
      ↓
Freeze checkpoint
```

Do not use an earlier or different commit's CI/deployment result as evidence for the current commit. Do not infer an unobserved Databricks configuration, table, permission, model version, or runtime value.

## Latest Phase 12 evidence checkpoint — 2026-09-06

```text
Phase: Drift + Retraining
Status: COMPLETE / FROZEN — SYNTHETIC VALIDATION SCOPE

Implementation commit:
97899df9c52bec2aa90e38e8a09aa92ee5756886

GitHub Actions CI:
34058671816 → SUCCESS

GitHub Actions Deploy Dev:
34058671804 → SUCCESS

Tests:
72 passed, 3 warnings
```

The Phase 12 implementation provides deterministic synthetic reference/current populations, reuses the existing drift detector, and evaluates an explicit auditable retraining policy. It does not claim a live production drift feed or automatic production retraining trigger.

The exact CI environment recorded Python `3.11.16`, Black `26.5.1`, Ruff `0.16.6`, Pytest `9.1.1`, MLflow `3.16.0`, Databricks SDK `0.135.0`, NumPy `1.26.4`, Pandas `3.0.5`, and SciPy `1.11.1`. Phase 12 did not change dependency versions or serving versions.

The protected serving baseline remains:

```text
cidev-netcare-readmission → readmission_model-1
```

The isolated candidate remains:

```text
cidev-netcare-readmission-candidate → readmission_model-8
```

## Architecture Decision — Simplified Databricks-Centric Serving

The assessment does not require a separate Cloud Run or API Gateway layer. Databricks Model Serving already provides the production model-serving boundary required for the readmission prediction workload.

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
cidev-netcare-readmission-candidate
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

## Phase 10 — Security and Secrets

Phase 10 deployment authentication and production bundle deployment have been validated.

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
Production Databricks Resources
```

Production application/runtime credentials remain outside source control. GitHub CI/CD uses Databricks GitHub OIDC rather than a long-lived Databricks token.

## Phase 11 — Monitoring and Observability

**Status: COMPLETE / FROZEN FOR THE VERIFIED MONITORING SCOPE.**

Phase 11 established and tested repository monitoring contracts and verified the live Databricks serving-monitoring surfaces.

The verified `system.serving.endpoint_usage` query for served entity `362c5dbb1cf448789afbb4ee6a687712` returned zero rows; no prediction/probability or labelled-outcome source is inferred from that table.

**Phase 11 exit criterion: achieved for the verified monitoring scope.**

## Phase 12 — Drift Detection and Retraining

**Status: COMPLETE / FROZEN — SYNTHETIC VALIDATION SCOPE.**

Phase 12 provides a deterministic CI-tested drift-to-retraining decision path. It uses the existing drift detector and an explicit auditable retraining policy.

The phase verifies both no-drift and intentional-drift scenarios and passes the resulting drift report into the retraining policy. The exact implementation commit and CI/deployment evidence are recorded above.

No live production drift dataset or automatic production retraining trigger is claimed. Any future production retraining orchestration requires independently verified source, trigger, permissions, job configuration, training result, quality gate, registry action, and promotion path.

**Phase 12 exit criterion: achieved for the synthetic validation scope.**

## Phase 13 — Canary and Production Release

**Status: NEXT / FINAL LIFECYCLE PHASE.**

Phase 13 is the final project phase. It will validate the controlled model-release path using the already established candidate/protected serving architecture.

### Phase 13 scope

1. Inspect the actual current candidate and protected serving configuration before any change.
2. Establish the exact release/rollback contract from the verified Databricks serving configuration.
3. Validate candidate readiness without changing the protected v1 baseline prematurely.
4. If a controlled traffic change is supported and required by the actual serving configuration, perform only the explicitly validated change.
5. Verify post-release serving health and exact model/traffic state.
6. Verify rollback behavior or the strongest directly testable rollback contract without risking the protected baseline.
7. Record the exact GitHub commit, CI/deployment result, and live Databricks state.
8. Freeze the final project checkpoint.

### Phase 13 no-guessing boundary

No production promotion, traffic split, or rollback operation will be claimed until the relevant Databricks serving configuration and supported operation are inspected. The protected endpoint `cidev-netcare-readmission` / model v1 remains unchanged unless an evidence-backed Phase 13 release operation explicitly requires a controlled change.

## Final lifecycle target

```text
Data → Validation → Training → MLflow
     → Quality Gate → Unity Catalog Registry
     → Databricks Model Serving
     → Existing System Integration
     → Security / IAM
     → Monitoring
     → Drift Detection
     → Retraining Decision → Validation
     → Canary / Controlled Release
     → Production Verification
     → Rollback Contract
```

Phase 13 is the final remaining lifecycle phase. Cloud Run and API Gateway remain deliberately excluded from the baseline architecture unless a concrete requirement is introduced.
