# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

## Architecture

```text
Hospital / Clinical Sources
          ↓
          GCP
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
FastAPI / Cloud Run
          ↓
GCP API Gateway
```

## Phase status

| Phase | Status |
|---|---|
| Phase 1 — Production Data Science Pipeline | **COMPLETE** |
| Phase 2 — MLflow Tracking / Registry | **IMPLEMENTED / VALIDATED** |
| Phase 3 — GCP Data Lake + Databricks Medallion | **IMPLEMENTED / VALIDATED** |
| Phase 4 — Databricks Workflows | **IMPLEMENTED / VALIDATED** |
| Phase 5 — Unity Catalog | **FOUNDATION COMPLETE** |
| Phase 6 — Model Registry & Promotion | **COMPLETE** |
| Phase 7 — Production Model Serving & Inference | **IN PROGRESS** |
| Phase 8–13 | **PENDING** |

## Technology stack

- **Cloud:** GCP
- **Storage:** Google Cloud Storage
- **Data / orchestration:** Databricks on GCP
- **Storage format:** Delta Lake
- **Governance:** Unity Catalog
- **Experiment tracking:** MLflow
- **Models:** scikit-learn Logistic Regression and HistGradientBoosting
- **Serving:** Databricks Model Serving
- **API:** FastAPI, Cloud Run, GCP API Gateway
- **Secrets:** GCP Secret Manager
- **CI/CD:** GitHub Actions
- **Observability:** Cloud Monitoring / Cloud Logging

The baseline workload is CPU-based tabular classification.

## Repository structure

```text
netcare-ml-platform/
├── src/
├── api/
├── notebooks/
├── databricks/
├── infrastructure/
├── tests/
├── docs/
├── .github/workflows/
└── run_pipeline.py
```

## Data architecture

**Bronze** — raw landing data.

**Silver** — validated and standardized encounter data.

**Gold** — approved analytics and ML features.

### Unity Catalog

Verified registered model:

```text
netcareaidatabricks.default.readmission_model
```

The registered model uses the verified `default` schema.

## ML lifecycle

```text
Data → Validation → Leakage-safe preprocessing
     → Train/Test → Evaluation → MLflow candidate
     → Quality Gate → Register → Promote champion
     → Explicit serving deployment
```

Quality gates require ROC-AUC ≥ 0.70, Recall ≥ 0.60, data validation, model tests, and no unacceptable regression when a production comparison is available.

## Phase 6 — Model Registry & Promotion

Phase 6 is complete. Models are evaluated before registration and promotion. Unity Catalog provides governed model versions and the `champion` alias.

The deployment process resolves the approved alias to an explicit model version before serving deployment.

## Phase 7 — Production Model Serving & Inference

Phase 7 is validating the model artifact and serving boundary.

### Serving contract

Raw patient feature records are transformed using the fitted preprocessing pipeline before inference. The response contains:

```text
predicted_label
probability
risk_tier
model_version
```

External API contract:

```text
POST /v1/predictions/readmission
```

### Known-good serving baseline

DEV endpoint:

```text
dev_james_mashiyane_za_dev-netcare-readmission
```

The active configuration serves model version **1** at 100% traffic and is `DEPLOYMENT_READY`.

**Version 1 is the protected known-good baseline and must remain untouched while candidate serving is debugged.**

### Current blocker

Candidate serving has exposed two artifact-boundary problems:

1. the serving artifact initially did not package the `src` application code;
2. subsequent artifacts exposed scikit-learn/runtime deserialization incompatibility.

The current registry implementation derives serialization-sensitive dependency versions from the training environment.

Detailed evidence is maintained in `docs/phase-7-serving-debugging.md`.

### Acceptance criteria

- [ ] self-contained serving artifact validated
- [ ] candidate deployment reaches `DEPLOYMENT_READY`
- [ ] direct serving inference succeeds
- [ ] response contract validated
- [ ] FastAPI integration succeeds
- [ ] serving/integration tests pass
- [ ] architecture documentation reflects the verified implementation

## Development and deployment

GitHub is the source of truth for application code and deployment configuration.

```text
GitHub → CI → Bundle validation → DEV → STAGING → PRODUCTION
```

Credentials and tokens must never be committed.

## Engineering principles

- Evidence before claims.
- Freeze known-good components before debugging unknown components.
- Make small, targeted changes.
- Repair failed candidates instead of unnecessarily abandoning them.
- Preserve rollback paths.
- Match infrastructure to workload requirements.
- Minimize patient data in logs and telemetry.

Detailed engineering investigations belong in `docs/`; the README records the current verified architecture and status.
