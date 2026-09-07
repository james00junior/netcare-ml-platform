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
| Phase 13 | Canary + Production Releases | **COMPLETE / FROZEN — MODEL v8 PRODUCTION RELEASE VALIDATED** |

**Freeze rule:** Phases 1–13 are closed for their validated scopes. The protected v1 endpoint and the verified v8 production release are not changed without a new, independently validated change.

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

## Latest Phase 13 production release evidence — 2026-09-07

```text
Phase: Canary + Production Releases
Status: COMPLETE / FROZEN — MODEL v8 PRODUCTION RELEASE VALIDATED

Production endpoint: dev-netcare-readmission
Production registered model: netcareaidatabricks.default.readmission_model
Production model version: 8
Served model: readmission_model-8
Configuration version: 2
Endpoint state: READY
Configuration update: NOT_UPDATING
Served entities: 1
Traffic: 100% → readmission_model-8
Deployment state: DEPLOYMENT_READY
Workload: Small / CPU
Scale to zero: enabled
Usage tracking: enabled

Release mechanism:
GitHub Actions manual workflow: Release Production
Selected release version: 8

Repository release commit:
fcca6f929cf05ebfc7c19fa720cbae08b3f8d4bf
```

The live Databricks response independently verifies that production is serving registered model version 8 at 100% traffic and is stable (`READY` / `NOT_UPDATING`). The endpoint contains exactly one served entity, `readmission_model-8`, in `DEPLOYMENT_READY` state.

The workflow's explicit rollback choice remains model version 1. No rollback was executed in this release. No canary traffic percentage is claimed because the verified candidate and protected resources are separate endpoints; the release path is controlled promotion/rollback rather than an invented traffic split.

**Phase 13 exit criterion: achieved.**

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

## Phase 13 — Canary and Production Release

Phase 13 is complete and frozen for the validated controlled-release scope.

The implemented manual GitHub Actions release workflow accepts only the verified release choices:

```text
8 → controlled promotion of the verified candidate model
1 → explicit rollback to the protected baseline model
```

The workflow uses the existing production OIDC environment, Python `3.11.16`, Databricks CLI `1.15.0`, bundle validation, deployment-plan preview, bundle deployment, and post-deployment serving verification.

The verified production release selected model version 8 and produced the live state recorded above. The release did not invent a traffic split and did not modify the isolated candidate endpoint.

**Phase 13 is frozen.** Future production releases require a new evidence-backed change under the repository change-control procedure.

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
     → Controlled Release
     → Production Verification
     → Rollback Contract
```

**Production lifecycle baseline complete.** Future work is treated as a new, independently scoped change rather than an extension of the completed Phase 13 implementation.
