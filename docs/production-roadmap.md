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
| Phase 11 | Monitoring + Observability | **IN PROGRESS — Step 11.1 VERIFIED** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–9 are closed. Their validated implementation is not modified while Phase 10–13 work proceeds. The protected v1 serving baseline is never touched.

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

## Latest verified repository checkpoint

```text
Commit: cc47b912efd86353f93c2115945e74cb348faa91
Message: Fix monitoring exports lint ordering

CI: PASS
Deploy Dev: PASS
```

This checkpoint passed the repository lint, format, and test stages and the Databricks bundle deployment workflow. The next Phase 11 step can therefore proceed without reopening the completed CI/debugging work.

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

Phase 10 deployment authentication and production bundle deployment have now been validated.

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

Verified production deployment checkpoint:

```text
Commit:
2104e7e849f00b56cdd2593171ac3146c91b7d4a

Environment:
prod

Databricks CLI:
1.15.0

Tests:
41 passed

Bundle validation:
SUCCESS

Bundle deployment:
SUCCESS

Resources created:
- train_readmission_model
- readmission_model_candidate_endpoint
- readmission_model_endpoint

Resources changed:
0

Resources deleted:
0
```

The production bundle is therefore deployed successfully. Runtime production serving inference remains a separate verification checkpoint and is not inferred from deployment success alone.

Current Phase 10 controls include:

- `SecretStr` for runtime API keys and Databricks serving tokens
- GitHub OIDC authentication for Databricks deployment workflows
- `id-token: write` and `contents: read` workflow permissions
- environment-scoped Databricks host and client configuration
- standardised `DATABRICKS_HOST` bundle configuration across dev, staging, and prod
- pinned CI formatter/linter versions based on observed CI
- a committed record of verified build/runtime versions
- a committed `uv.lock` containing the validated 240-package transitive dependency resolution

The dependency-locking follow-up is complete. `pyproject.toml` remains the source of truth for direct dependencies, while `uv.lock` records the resolved transitive dependency graph.

## Phase 11 — Monitoring and Observability

Phase 11 is active. The detailed implementation plan and live evidence are maintained in [`docs/monitoring.md`](monitoring.md). The operational no-guess/change-control rules are maintained in [`docs/verification-record.md`](verification-record.md).

### Step 11.1 — Inspect actual serving telemetry and governed sources

**Status: VERIFIED FOR ENDPOINT TELEMETRY + SERVING SYSTEM-TABLE ACCESS.**

Verified candidate identity:

```text
Endpoint:                 cidev-netcare-readmission-candidate
Served model:             readmission_model-8
Registered model:         netcareaidatabricks.default.readmission_model
Registered version:       8
Served entity ID:         362c5dbb1cf448789afbb4ee6a687712
Endpoint config version:  1
```

Verified candidate serving state:

```text
READY
NOT_UPDATING
DEPLOYMENT_READY
Small / CPU
scale-to-zero enabled
100% traffic within candidate endpoint
```

Verified system-table surfaces:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

The exact v8 `served_entity_id` was resolved from `system.serving.served_entities`. A direct query against `system.serving.endpoint_usage` for that exact ID succeeded but returned zero rows. Consequently, system-table access is verified, but v8 request-record population remains open.

The live v8 telemetry snapshot also exposed CPU, memory, request/error, latency, model-queue-time, and provisioned-concurrency metrics. The request/error counters and histogram observations were zero in the inspected snapshot; this is not evidence that serving is broken because direct v8 inference was separately verified.

**Step 11.1 exit criterion:** met for the inspected telemetry and system-table surfaces; request-record population remains explicitly open.

### Remaining Phase 11 sequence

1. **Step 11.2:** establish governed monitoring data and verify the actual source/schema/access controls.
2. **Step 11.3:** implement health and data-quality checks against verified data.
3. **Step 11.4:** implement prediction and feature-drift monitoring only after the underlying records are observed.
4. **Step 11.5:** implement labelled-outcome evaluation only after the outcome source and join are verified.
5. **Step 11.6:** add alerts and dashboards only after thresholds are evidenced or explicitly approved.

Each step must produce a checkpoint before the next step begins. Empty or missing telemetry is recorded as such; it is never silently converted into populated records or zero-capability assumptions.

## Phase 12 — Drift Detection and Retraining

```text
Production Data
      │
      ▼
Monitoring / Drift Signals
      │
      ├── No actionable drift → Continue
      │
      ▼
Significant drift or scheduled trigger
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

Retraining can be scheduled, triggered by validated drift signals, or triggered by newly labelled outcomes.

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

Phases 1–9 remain frozen. Phase 10 deployment authentication and production bundle deployment are validated. Phase 11 is the active monitoring and observability implementation phase. Cloud Run and API Gateway remain deliberately excluded from the baseline architecture unless a concrete requirement is introduced.
