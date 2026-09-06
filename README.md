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
| Phase 10 | Security + Secrets + IAM | **IN PROGRESS** |
| Phase 11 | Monitoring + Observability | **PENDING** |
| Phase 12 | Drift + Retraining | **PENDING** |
| Phase 13 | Canary + Production Releases | **PENDING** |

**Freeze rule:** Phases 1–9 are closed. Their validated implementation is not modified while Phase 10–13 work proceeds.

## Validated serving baseline

The validated serving implementation uses **Databricks Model Serving** directly.

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

Isolated candidate endpoint:

```text
dev_james_mashiyane_za_dev-netcare-readmission-candidate
```

Verified serving state at validation:

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

The exact 28-field model contract was successfully validated against the isolated v8 candidate endpoint. The serving response included `predicted_label`, `probability`, `risk_tier`, and `model_version`.

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

Phase 10 is the active security-hardening phase.

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
Model Serving
```

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

Monitoring will cover:

- serving latency, errors, availability, throughput, and resource utilisation;
- data quality, schema changes, feature distributions, and drift;
- prediction distributions, confidence, actual outcomes, ROC-AUC, Recall, Precision, and F1.

## Phase 12 — Drift + Retraining

The production lifecycle will support drift-triggered or scheduled retraining, followed by model evaluation, registration, and controlled deployment.

## Phase 13 — Canary + Production Releases

Production releases will use candidate validation, controlled traffic shifts, and rollback to a previously trusted model version.

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
- **Monitoring:** Databricks-native telemetry and GCP monitoring where appropriate

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
- Freeze known-good components before debugging unknown components.
- Make small, targeted changes.
- Repair failed candidates instead of unnecessarily abandoning them.
- Preserve rollback paths.
- Match infrastructure to workload requirements.
- Prefer the minimum architecture that satisfies the requirements.
- Minimize patient data in logs and telemetry.

Detailed engineering investigations belong in `docs/`; [`docs/production-roadmap.md`](docs/production-roadmap.md) is the lifecycle source of truth and this README records the current verified architecture and status.
