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

The baseline architecture deliberately avoids an additional API compute layer. Cloud Run and API Gateway are not required for the core ML serving path unless a concrete enterprise requirement justifies them.

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
| Phase 11 | Monitoring + Observability | **IN PROGRESS — Step 11.1 VERIFIED** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–9 are closed. Their validated implementation is not modified while Phase 10–13 work proceeds. The protected v1 serving baseline is never changed as part of candidate development.

## Verification and no-guessing policy

The repository now maintains an explicit verification record at [`docs/verification-record.md`](docs/verification-record.md). It is the operational guardrail for development and debugging.

The rule is simple:

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
Verify deployment for the exact commit when applicable
      ↓
Verify live Databricks state when applicable
      ↓
Update documentation
      ↓
Freeze checkpoint
```

Do not guess model versions, endpoint configuration, tables, permissions, runtime versions, or deployment state. A result from a different commit is not evidence for the current commit. Empty telemetry is recorded as empty, not converted into an assumption that records exist or do not exist.

Documentation distinguishes **implemented**, **queryable**, **observed**, **validated**, and **complete**. These states are not interchangeable.

## Validated serving baseline

The validated candidate serving implementation uses **Databricks Model Serving** directly.

Registered model:

```text
netcareaidatabricks.default.readmission_model
```

Validated candidate:

```text
Serving v2 → Registry Model v8
```

MLflow run:

```text
bf12e7f602084e78acdab4797c40c2b2
```

Verified candidate endpoint:

```text
cidev-netcare-readmission-candidate
```

Verified serving state:

```text
endpoint state:       READY
configuration:        NOT_UPDATING
served model:         readmission_model-8
model version:        8
traffic:              100% within candidate endpoint
deployment:           DEPLOYMENT_READY
workload:             Small / CPU
scale to zero:        enabled
config version:       1
```

The exact 28-field model contract was successfully validated against the isolated v8 candidate endpoint. A live inference request returned:

```text
predicted_label: 0
probability: 0.32462546453278807
risk_tier: medium
model_version: champion
```

The `model_version` response field is recorded exactly as observed. The endpoint configuration independently identifies the served registered model version as `8`.

The protected baseline remains separate:

```text
cidev-netcare-readmission
registered model version: 1
served model:             readmission_model-1
traffic:                  100%
state:                    READY
```

The protected v1 endpoint has not been changed or promoted as part of candidate validation.

## Phase 9 — Existing-System Integration

The production integration boundary is:

```text
Existing Hospital System
          │ HTTPS + JSON
          ▼
Databricks Model Serving
          │
          ▼
Serving v2
          │
          ▼
Registry Model v8
          │
          ▼
Prediction
```

The serving invocation contract is:

```text
POST <Databricks serving endpoint>/invocations
```

with a request body using the Databricks dataframe-records format.

The existing `DatabricksServingClient` validates and normalises the serving response. FastAPI remains available as a local integration adapter and test harness; it is not required as production serving infrastructure.

## Phase 10 — Security + Secrets + IAM

Phase 10 deployment authentication and production bundle deployment have now been validated.

GitHub Actions deployment authentication uses **Databricks GitHub OIDC / workload identity federation**, not a long-lived Databricks personal access token.

```text
GitHub Actions
      │
      │ OIDC
      ▼
Databricks Authentication
      │
      ▼
Databricks Bundles
      │
      ▼
Production Databricks Resources
```

The production federation policy was corrected to the immutable GitHub Actions environment subject and Databricks OIDC token audience. The existing dev federation policy was left unchanged.

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

This confirms successful production bundle deployment. It does **not** by itself claim that production serving inference has been runtime-validated; that remains a separate verification checkpoint.

Deployment workflows use:

```text
DATABRICKS_AUTH_TYPE=github-oidc
DATABRICKS_HOST=${{ vars.DATABRICKS_HOST }}
DATABRICKS_CLIENT_ID=${{ vars.DATABRICKS_CLIENT_ID }}
```

and request only:

```yaml
permissions:
  id-token: write
  contents: read
```

Application credentials use Pydantic `SecretStr` and must never be committed to source, `.env` files, notebooks, or logs.

Detailed controls are documented in [`docs/security.md`](docs/security.md).

## Version and build record

The repository maintains a single version/configuration record at [`docs/build-and-runtime-versions.md`](docs/build-and-runtime-versions.md).

The currently recorded and observed baseline includes:

- Python `3.11.16`
- pip `26.2.1`
- Black `26.5.1`
- Ruff `0.16.6`
- pytest `9.1.1`
- pytest-cov `7.1.0`
- mypy `2.3.1`
- pandas `3.0.5`
- NumPy `1.26.4`
- scikit-learn `1.3.0`
- SciPy `1.11.1`
- XGBoost `3.2.0`
- MLflow `3.16.0`
- Databricks SDK `0.135.0`
- Pydantic `2.13.5`
- FastAPI `0.141.1`
- httpx `0.28.1`
- uvicorn `0.52.4`
- Databricks CLI `1.15.0`
- uv `0.12.7` — dependency lock resolver

The repository includes a committed `uv.lock` containing the validated 240-package transitive dependency resolution. `pyproject.toml` remains the source of truth for direct dependency declarations.

## Phase 11 — Monitoring + Observability

Phase 11 is now active. Step 11.1 is **verified for live endpoint telemetry and governed serving system-table access**. The detailed evidence and implementation sequence are maintained in [`docs/monitoring.md`](docs/monitoring.md).

### Verified live serving telemetry

Observed from `cidev-netcare-readmission-candidate` / `readmission_model-8`:

```text
cpu_usage_percentage                  2.344062231666667
mem_usage_percentage                  6.823611259460449
request_count_total                   0
request_4xx_count_total               0
request_5xx_count_total               0
provisioned_concurrent_requests_total 4
```

The live Prometheus/OpenMetrics surface also exposes request-latency and model-queue-time histograms:

```text
request_latency_ms
model_queue_time_ms
```

The observed snapshot contained zero request observations for those histograms and zero requests/errors for the reported minute. This is a telemetry observation, not evidence that the endpoint cannot serve requests; v8 runtime inference has separately been verified successfully.

### Verified governed serving system tables

The target workspace exposes the following Unity Catalog system tables:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

The observed `system.serving.endpoint_usage` schema contains:

```text
request_time
status_code
requester
databricks_request_id
client_request_id
served_entity_id
```

The observed `system.serving.served_entities` schema contains:

```text
served_entity_id
endpoint_name
served_entity_name
entity_name
entity_version
endpoint_config_version
custom_model_config
change_time
endpoint_delete_time
```

The v8 candidate served entity was queried directly from `system.serving.served_entities` and verified as:

```text
served_entity_id:        362c5dbb1cf448789afbb4ee6a687712
endpoint_name:           cidev-netcare-readmission-candidate
served_entity_name:      readmission_model-8
entity_name:             netcareaidatabricks.default.readmission_model
entity_version:          8
endpoint_config_version: 1
change_time:             2026-09-06T16:00:44.803Z
endpoint_delete_time:    null
```

A direct query of `system.serving.endpoint_usage` for that exact v8 `served_entity_id` succeeded but returned **zero rows**. Therefore the governed usage-table path is confirmed as queryable, but v8 request records have **not yet been observed in that table**. No inference-record population is being assumed from endpoint success alone.

### Current Phase 11 sequence

```text
11.1  Live telemetry + governed source inspection  ← VERIFIED
11.2  Establish governed monitoring data           ← NEXT
11.3  Health + data-quality checks
11.4  Prediction + drift monitoring
11.5  Labelled-outcome evaluation
11.6  Alerts + operational dashboard
```

Each step requires its own evidence checkpoint. We do not advance a step based on documentation alone.

## Phase 12 — Drift + Retraining

The production lifecycle will support drift-triggered or scheduled retraining, followed by model evaluation, registration, and controlled deployment.

Phase 12 will consume the monitoring and drift signals established in Phase 11 rather than introducing an independent monitoring path.

## Phase 13 — Canary + Production Releases

Production releases will use candidate validation, controlled traffic shifts, and rollback to a previously trusted model version.

The protected v1 baseline remains the rollback reference until a later release is explicitly validated and promoted.

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
- **Monitoring:** Databricks-native endpoint telemetry, Unity Catalog monitoring, and GCP monitoring where appropriate

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
     → Monitoring → Drift Detection
     → Retraining → Validation → Controlled Release
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
