# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed as a **Databricks-centric production ML system on GCP**.

## Project scope

This project implements and validates the production ML lifecycle from governed data ingestion through model training, evaluation, registry, serving, integration, security, monitoring, drift detection, retraining decisioning, and controlled release.

The verified baseline deliberately avoids infrastructure that is not required by the workload. Databricks Model Serving is the production serving boundary; a separate Cloud Run/API Gateway layer is not part of the baseline.

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
          ↓
Monitoring → Drift Detection
          ↓
Retraining Decision → Validation
          ↓
Controlled Release / Rollback
```

GitHub is the source of truth for application code and deployment configuration. GCS provides cloud data storage. Databricks provides the ML lifecycle, governance, orchestration, registry, and serving platform.

## Complete production lifecycle

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

**Production lifecycle baseline: COMPLETE / FROZEN.** Future work is treated as a new, independently scoped change under the verification and change-control procedure.

## Verification and no-guessing policy

The repository maintains an explicit verification record at [`docs/verification-record.md`](docs/verification-record.md). The rule is:

```text
Inspect actual state → Record exact evidence → Make one targeted change
→ Run lint / format / tests → Verify exact CI/deployment commit
→ Verify live Databricks state → Update documentation → Freeze checkpoint
```

Do not guess model versions, endpoint configuration, tables, permissions, runtime versions, or deployment state. Documentation distinguishes **implemented**, **queryable**, **observed**, **validated**, and **complete**.

## Current production release — Model v8

The latest independently verified production release is:

```text
Endpoint: dev-netcare-readmission
Registered model: netcareaidatabricks.default.readmission_model
Registered version: 8
Served model: readmission_model-8
Configuration version: 2

Endpoint state: READY
Configuration update: NOT_UPDATING
Served entities: 1
Traffic: 100% → readmission_model-8
Deployment: DEPLOYMENT_READY
Workload: Small / CPU
Scale to zero: enabled
Usage tracking: enabled
```

The production release was executed through the manual GitHub Actions `Release Production` workflow with model version `8`. The workflow retains an explicit rollback choice of model version `1`.

No canary traffic percentage is claimed: the verified candidate and protected baseline are separate serving endpoints. The release mechanism provides controlled promotion and explicit rollback without inventing a traffic split.

## Validated serving baseline

Registered model:

```text
netcareaidatabricks.default.readmission_model
```

Validated candidate:

```text
Serving v2 → Registry Model v8
MLflow run: bf12e7f602084e78acdab4797c40c2b2
Endpoint: cidev-netcare-readmission-candidate
```

Candidate state:

```text
READY
NOT_UPDATING
DEPLOYMENT_READY
100% traffic within candidate endpoint
Small / CPU
scale-to-zero enabled
config version 1
```

The protected rollback baseline remains:

```text
Endpoint: cidev-netcare-readmission
Served model: readmission_model-1
Registered version: 1
Traffic: 100%
State: READY
```

## Phase 9 — Existing-System Integration

The production integration boundary is direct Databricks Model Serving:

```text
Existing Hospital System
          │ HTTPS + JSON
          ▼
Databricks Model Serving
          │
          ▼
Serving v2 / Model v8
          │
          ▼
Prediction
```

The existing `DatabricksServingClient` remains a local integration adapter and test harness; FastAPI is not required as production serving infrastructure.

## Phase 10 — Security + Secrets + IAM

GitHub Actions deployment authentication uses Databricks GitHub OIDC / workload identity federation rather than a long-lived Databricks personal access token. Application secrets use `SecretStr` and are not committed to source, `.env` files, notebooks, or logs.

Verified production bundle deployment has already been established separately from runtime serving validation.

## Phase 11 — Monitoring + Observability

**Status: COMPLETE / FROZEN FOR THE VERIFIED MONITORING SCOPE.**

Detailed evidence is maintained in [`docs/monitoring.md`](docs/monitoring.md).

The verified candidate and protected endpoints retain usage tracking and the repository monitoring contracts preserve observed values and unknowns without fabricating telemetry.

The verified `system.serving.endpoint_usage` query for served entity `362c5dbb1cf448789afbb4ee6a687712` returned zero rows; no prediction/probability or labelled-outcome source is inferred from that table.

## Phase 12 — Drift + Retraining

**Status: COMPLETE / FROZEN — SYNTHETIC VALIDATION SCOPE.**

Phase 12 adds deterministic synthetic reference/current populations, exercises the existing drift detector, and evaluates an explicit auditable retraining policy. The end-to-end synthetic drift → retraining decision path is covered by CI tests.

Verified exact implementation checkpoint:

```text
Commit: 97899df9c52bec2aa90e38e8a09aa92ee5756886
CI run: 34058671816 → SUCCESS
Deploy Dev run: 34058671804 → SUCCESS
Tests: 72 passed, 3 warnings
```

Phase 12 does not claim a live production drift dataset or an automatic production retraining trigger. The synthetic fixture is the verified validation artifact. Future production retraining must independently verify its source, trigger, permissions, job configuration, training result, quality gate, registry action, and promotion path.

Detailed evidence is maintained in [`docs/retraining.md`](docs/retraining.md).

## Phase 13 — Canary + Production Releases

**Status: COMPLETE / FROZEN — MODEL v8 PRODUCTION RELEASE VALIDATED.**

Phase 13 adds a manual GitHub Actions production release workflow around the existing candidate/protected model versions. It accepts only the verified release choices: model `8` for controlled promotion and model `1` for explicit rollback.

The workflow uses the existing production OIDC authentication, Python `3.11.16`, Databricks CLI `1.15.0`, bundle validation, deployment-plan preview, bundle deployment, and post-deployment serving verification. It does not invent a traffic split or modify the isolated candidate endpoint.

The model `8` production release is independently verified by the live Databricks endpoint state recorded above.

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
- **Monitoring:** Databricks-native endpoint telemetry and Unity Catalog monitoring surfaces

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

## ML lifecycle

```text
Data → Validation → Leakage-safe preprocessing
     → Train/Test → Evaluation → MLflow candidate
     → Quality Gate → Register → Promote champion
     → Databricks Model Serving
     → Existing System Integration
     → Security / IAM
     → Monitoring → Drift Detection
     → Retraining Decision → Validation
     → Controlled Release → Rollback if required
```

Quality gates require ROC-AUC ≥ 0.70, Recall ≥ 0.60, data validation, model tests, and no unacceptable regression when a production comparison is available.

## Engineering principles

- Evidence before claims.
- Inspect actual state before proposing changes.
- Freeze known-good components before debugging unknown components.
- Make small, targeted changes.
- Verify CI/deployment against the exact commit being discussed.
- Repair failed candidates instead of unnecessarily abandoning them.
- Preserve rollback paths.
- Match infrastructure to workload requirements.
- Prefer the minimum architecture that satisfies the requirements.
- Minimize patient data in logs and telemetry.

Detailed engineering investigations belong in `docs/`; [`docs/production-roadmap.md`](docs/production-roadmap.md) is the lifecycle source of truth, [`docs/monitoring.md`](docs/monitoring.md) is the Phase 11 source of truth, [`docs/retraining.md`](docs/retraining.md) is the Phase 12 source of truth, and [`docs/verification-record.md`](docs/verification-record.md) is the operational change-control and evidence record.
