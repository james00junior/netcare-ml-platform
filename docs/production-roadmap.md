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
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–12 are closed for their validated scopes. The protected v1 serving baseline remains frozen while later lifecycle work proceeds.

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

## Latest Phase 11 evidence checkpoint

```text
Date: 2026-09-06

Protected endpoint:
cidev-netcare-readmission
  served model: readmission_model-1
  registered version: 1
  state: READY
  deployment: DEPLOYMENT_READY
  traffic: 100%

Candidate endpoint:
cidev-netcare-readmission-candidate
  served model: readmission_model-8
  registered version: 8
  served entity ID: 362c5dbb1cf448789afbb4ee6a687712
  state: READY
  config update: NOT_UPDATING
  deployment: DEPLOYMENT_READY
  traffic: 100% within candidate endpoint

Governed sources:
system.serving.endpoint_usage      → query succeeded; v8 rows observed: 0
system.serving.served_entities     → query/schema/identity verified
```

The candidate and protected endpoints both have serving usage tracking enabled. The candidate telemetry snapshot exposed CPU, memory, request/error, latency, model-queue-time, and provisioned-concurrency metrics. Request/error counters and histogram observations were zero in the supplied snapshot. This is recorded as observed telemetry, not as evidence of serving failure.

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

Phase 11 has established and tested the repository monitoring contracts and verified the live Databricks serving-monitoring surfaces. Detailed evidence is maintained in [`docs/monitoring.md`](monitoring.md).

### Verified implementation

The repository supports:

- serving health normalization from observed endpoint state;
- preservation of missing telemetry as unknown rather than fabricated zero values;
- exact governed queries for verified serving system-table columns;
- served-entity resolution;
- explicit input schema/null checks;
- feature/prediction drift calculations using caller-supplied baselines;
- labelled-outcome performance metrics when labels are available;
- performance degradation comparison against an explicit baseline.

### Verified Databricks evidence

```text
Protected endpoint: cidev-netcare-readmission
  model version: 1
  state: READY
  deployment: DEPLOYMENT_READY
  usage tracking: enabled

Candidate endpoint: cidev-netcare-readmission-candidate
  model version: 8
  served entity ID: 362c5dbb1cf448789afbb4ee6a687712
  state: READY
  config update: NOT_UPDATING
  deployment: DEPLOYMENT_READY
  usage tracking: enabled

system.serving.endpoint_usage
  query: SUCCEEDED
  v8 matching rows: 0

system.serving.served_entities
  schema: verified
  v8 identity: verified
```

### Explicit data boundary

The verified `endpoint_usage` table currently contains **zero rows for the v8 candidate served entity**. It exposes request metadata, not prediction/probability fields. Therefore the project does not claim that live prediction records or labelled outcomes are available from this table.

Likewise, no live Databricks alert or dashboard deployment is claimed because no such configuration was evidenced in this checkpoint.

This is a deliberate completion boundary: the monitoring framework is complete and frozen for the verified scope, while data-dependent operational extensions remain subject to independently verified sources.

**Phase 11 exit criterion: achieved for the verified monitoring scope.**

## Phase 12 — Drift Detection and Retraining

**Status: COMPLETE / FROZEN — SYNTHETIC VALIDATION SCOPE.**

Phase 12 provides a deterministic CI-tested drift-to-retraining decision path. It uses the existing drift detector and an explicit auditable retraining policy.

The synthetic fixture uses 500 reference observations (seed `42`) and 500 shifted observations (seed `43`) across five numerical and three categorical features. Tests verify both no-drift and intentional-drift scenarios and then pass the resulting drift report into the retraining policy.

The exact verified GitHub Actions commit was:

```text
97899df9c52bec2aa90e38e8a09aa92ee5756886
CI run: 34058671816 → SUCCESS
Deploy Dev run: 34058671804 → SUCCESS
```

CI recorded Python `3.11.16`, Black `26.5.1`, Ruff `0.16.6`, Pytest `9.1.1`, MLflow `3.16.0`, Databricks SDK `0.135.0`, NumPy `1.26.4`, Pandas `3.0.5`, and SciPy `1.11.1`. The exact test run completed with **72 passed, 3 warnings**.

The Deploy Dev job also completed tests, Databricks CLI setup/version recording, bundle validation, and bundle deployment successfully for the same commit.

This phase does **not** claim a live production drift dataset or automatic production retraining trigger. The synthetic fixture is the verified Phase 12 validation artifact. No serving endpoint or model version was changed by this phase.

**Phase 12 exit criterion: achieved for the synthetic validation scope.**

## Phase 13 — Production Model Release Strategy

Phase 13 remains pending. It will use candidate validation, controlled traffic changes, post-release health checks, and rollback to a previously trusted model version. The protected v1 endpoint remains unchanged until a later release is explicitly validated and promoted.

## Complete lifecycle

```text
Data → Validation → Training → MLflow
     → Quality Gate → Unity Catalog Registry
     → Databricks Model Serving
     → Existing System Integration
     → Security / IAM
     → Monitoring
     → Drift Detection
     → Retraining
     → Validation
     → Controlled Release
     → Rollback if required
```

Phases 1–12 are frozen for their validated scopes. Phase 13 is now the next implementation target. Cloud Run and API Gateway remain deliberately excluded from the baseline architecture unless a concrete requirement is introduced.
