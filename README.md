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
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–11 are closed for their validated scopes. The protected v1 serving baseline remains frozen while later lifecycle work proceeds.

## Verification and no-guessing policy

The repository maintains an explicit verification record at [`docs/verification-record.md`](docs/verification-record.md). The rule is:

```text
Inspect actual state → Record exact evidence → Make one targeted change
→ Run lint / format / tests → Verify exact CI/deployment commit
→ Verify live Databricks state → Update documentation → Freeze checkpoint
```

Do not guess model versions, endpoint configuration, tables, permissions, runtime versions, or deployment state. Documentation distinguishes **implemented**, **queryable**, **observed**, **validated**, and **complete**.

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

The protected baseline remains:

```text
Endpoint: cidev-netcare-readmission
Served model: readmission_model-1
Registered version: 1
Traffic: 100%
State: READY
```

The protected v1 endpoint has not been changed as part of candidate validation or Phase 11.

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

### Live Databricks evidence

Protected production endpoint:

```text
cidev-netcare-readmission
model version: 1
state: READY
config update: NOT_UPDATING
deployment: DEPLOYMENT_READY
usage tracking: enabled
```

Candidate endpoint:

```text
cidev-netcare-readmission-candidate
model version: 8
served entity ID: 362c5dbb1cf448789afbb4ee6a687712
state: READY
config update: NOT_UPDATING
deployment: DEPLOYMENT_READY
100% traffic within candidate endpoint
usage tracking: enabled
```

Verified governed system-table surfaces:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

The verified `endpoint_usage` schema contains request metadata only:

```text
request_time
status_code
requester
databricks_request_id
client_request_id
served_entity_id
```

A direct query of `system.serving.endpoint_usage` for the exact v8 served entity succeeded and returned **zero rows**. This means the table is queryable but v8 request-record population was not observed. No prediction/probability or labelled-outcome source is inferred from that table.

The repository monitoring implementation provides tested contracts for:

- endpoint health;
- observed serving metrics;
- governed serving-system queries;
- served-entity identity;
- input schema/null checks;
- feature/prediction drift calculations;
- labelled-outcome performance metrics;
- performance degradation comparison.

Missing telemetry remains unknown rather than being fabricated as zero. No live alert/dashboard deployment is claimed without evidence.

### Phase 11 exit boundary

Phase 11 is frozen for the verified monitoring scope: live serving telemetry and governed system-table access are evidenced, the monitoring contracts are implemented/tested, and the empty v8 usage result is explicitly recorded. Live request-level prediction records, labelled outcomes, and production alert/dashboard deployment remain data/configuration-dependent extensions for later evidence.

## Phase 12 — Drift + Retraining

**Next active phase.** Phase 12 will connect validated drift/performance signals to the existing training, MLflow, quality-gate, registration, and promotion components. The actual Databricks retraining trigger/job configuration will be verified before orchestration changes are made.

## Phase 13 — Canary + Production Releases

Pending Phase 12. Production release work will use candidate validation, controlled traffic changes, post-release monitoring, and rollback to a previously trusted version. The protected v1 baseline remains the rollback reference until a later release is explicitly validated and promoted.

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
     → Retraining → Validation → Controlled Release
     → Rollback if required
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

Detailed engineering investigations belong in `docs/`; [`docs/production-roadmap.md`](docs/production-roadmap.md) is the lifecycle source of truth, [`docs/monitoring.md`](docs/monitoring.md) is the Phase 11 source of truth, and [`docs/verification-record.md`](docs/verification-record.md) is the operational change-control and evidence record.
