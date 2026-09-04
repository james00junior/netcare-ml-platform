# Netcare ML Platform

Production ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

> **Platform constraint:** Azure is not part of this architecture or implementation. All cloud, data, ML lifecycle, serving and CI/CD decisions in this repository target GCP + Databricks on GCP.

## 1. Platform objective

The platform turns hospital encounter data into a governed, production-ready machine-learning service that can:

- ingest and validate hospital data;
- build leakage-safe ML features;
- train and evaluate readmission models;
- track experiments and artifacts with MLflow;
- register and govern models in Unity Catalog;
- promote only quality-approved models to the `champion` alias;
- serve approved models through Databricks Model Serving;
- expose a stable external API through FastAPI and GCP API Gateway;
- monitor data, model performance and infrastructure;
- detect drift and trigger controlled retraining;
- support staged model releases and rollback.

## 2. Target production architecture

```text
Hospital / Clinical Source Systems
              │
              ▼
      GCP API / Data Ingestion
              │
              ▼
   Google Cloud Storage (GCS)
              │
              ▼
   ┌──────────────────────────┐
   │ Databricks on GCP        │
   │ Delta / Medallion        │
   │                          │
   │ Bronze → Silver → Gold   │
   └────────────┬─────────────┘
                │
                ▼
         Unity Catalog
      ┌─────────┴─────────┐
      │                   │
   Data assets       ML assets
                          │
                          ▼
                    MLflow Tracking
                          │
                          ▼
                    Quality Gate
                          │
                          ▼
                 UC Model Registry
                          │
                 champion alias
                          │
                          ▼
              Databricks Model Serving
                          │
                          ▼
                    Cloud Run
                     FastAPI
                          │
                          ▼
                  GCP API Gateway
                          │
                          ▼
                  Hospital Systems

Monitoring / Logging / Security span all layers.
```

## 3. Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Cloud | **GCP** | Primary cloud platform |
| Data lake | **Google Cloud Storage** | Raw and curated data storage |
| Data engineering | **Databricks on GCP** | Distributed processing and orchestration |
| Storage format | **Delta Lake** | Reliable analytical tables |
| Architecture | **Bronze / Silver / Gold** | Data quality and transformation boundaries |
| Governance | **Unity Catalog** | Catalogs, schemas, permissions, lineage and ML assets |
| Experiment tracking | **MLflow** | Parameters, metrics, artifacts and runs |
| Model registry | **Unity Catalog + MLflow** | Governed model versions and aliases |
| Training | **scikit-learn / HistGradientBoosting** | Readmission classification |
| Serving | **Databricks Model Serving** | Managed production inference |
| Integration | **FastAPI / Cloud Run** | Stable external API contract |
| API gateway | **GCP API Gateway** | External API entry point and controls |
| Secrets | **GCP Secret Manager** | Credential and secret management |
| CI/CD | **GitHub Actions** | Quality gates and deployment automation |
| Observability | **Cloud Monitoring / Cloud Logging** | Infrastructure and application monitoring |

## 4. Repository structure

```text
netcare-ml-platform/
├── src/
│   ├── config/              # Runtime and model configuration
│   ├── data/                # Ingestion, validation, preprocessing
│   ├── features/            # Feature construction
│   ├── models/              # Training, evaluation, registry, promotion
│   ├── serving/             # Production predictor and schemas
│   └── monitoring/          # Drift and performance monitoring
├── api/                     # FastAPI application
├── notebooks/               # Exploration and Databricks notebooks
├── databricks/
│   ├── databricks.yml       # Declarative Automation Bundle
│   ├── resources/           # Databricks jobs/resources
│   └── sql/                 # Unity Catalog bootstrap/governance SQL
├── infrastructure/          # Cloud infrastructure definitions
├── tests/                   # Automated tests
├── docs/                    # Architecture, governance and API docs
├── .github/workflows/       # CI/CD pipelines
└── run_pipeline.py          # Local end-to-end pipeline
```

## 5. Data architecture

### Bronze

Raw landing layer. Data is retained close to source format and is not used directly for model training.

### Silver

Validated and standardized clinical/encounter data. Typical processing includes schema checks, missing-value handling, categorical normalization and duplicate detection.

### Gold

Analytics- and ML-ready datasets containing approved features for downstream training and serving.

### Unity Catalog

The current governance design uses the `netcareaidatabricks` catalog:

```text
netcareaidatabricks
├── bronze
├── silver
├── gold
└── ml
```

The ML assets include:

```text
netcareaidatabricks.ml.readmission_features
netcareaidatabricks.ml.readmission_model
```

## 6. ML lifecycle and Phase 6 governance

```text
Raw Data
   ↓
Validation
   ↓
Train/Test Split
   ↓
Leakage-safe Preprocessing
   ↓
Model Training
   ↓
MLflow Experiment
   ↓
Candidate Evaluation
   ↓
Quality Gate
   ↓
Register Candidate
   ↓
Compare with Champion
   ↓
Promote `champion` Alias
   ↓
Model Serving
```

A model is **not promoted merely because training succeeded**.

The Phase 6 quality gate requires:

- ROC-AUC ≥ 0.70;
- Recall ≥ 0.60;
- data validation passed;
- model tests passed;
- candidate performance must not regress against the production model when production comparison is required.

Registration and promotion are separate operations. A registered model version receives the `champion` Unity Catalog alias only after the promotion gate passes. Unity Catalog aliases are used instead of legacy MLflow model stages.

### Recall threshold and current remediation

Recall is a deliberate quality constraint because the readmission use case must avoid allowing a candidate model with inadequate detection of positive readmission cases into the governed promotion path.

During the first Databricks Phase 6 execution, the quality gate reported:

```text
Candidate rejected by Phase 6 quality gate: ('recall failed',)
```

The initial failure was caused by an implementation defect: the training helpers logged accuracy and ROC-AUC but did not calculate the `recall` metric. The quality gate therefore treated the missing recall value as `0.0` and correctly rejected the candidate.

This has now been fixed in both training paths. Logistic Regression and HistGradientBoosting evaluation now explicitly calculate recall using the test predictions and return it with the candidate metrics. The quality gate itself has **not** been weakened.

The corrected Databricks execution subsequently completed successfully, confirming that the candidate now reaches and passes the Phase 6 quality gate with recall available to the evaluation logic.

The previously measured local development results remain above the threshold:

- Logistic Regression recall: **0.692**
- HistGradientBoosting recall: **0.628**

These are development/assessment results and must not be interpreted as production clinical performance claims.

## 7. Current model baseline

The leakage-safe local pipeline currently evaluates:

| Model | Accuracy | ROC-AUC | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.653 | 0.710 | 0.692 | 0.509 |
| HistGradientBoosting | 0.713 | 0.711 | 0.628 | 0.533 |

These are development/assessment results on the supplied dataset, **not production clinical performance claims**.

## 8. Development, staging and production

The intended promotion path is:

```text
GitHub
   ↓
CI quality gates
   ↓
Databricks Bundle validation
   ↓
DEV
   ↓
STAGING
   ↓
PRODUCTION
```

Environment-specific configuration must be supplied through deployment configuration and secret management. Credentials must never be committed to the repository.

## 9. Production inference architecture

The local FastAPI predictor uses the **same fitted preprocessing artifact produced during training**. This prevents production inference from independently refitting or reconstructing preprocessing logic.

The intended managed production path is:

```text
Client
  ↓
GCP API Gateway
  ↓
Cloud Run / FastAPI integration
  ↓
Databricks Model Serving
  ↓
Champion model
```

External API contract:

```text
POST /v1/predictions/readmission
```

The final production contract will be aligned with the actual Databricks serving input schema before deployment.

## 10. Databricks on GCP

Databricks resources are managed as code through the Declarative Automation Bundle under `databricks/`.

The current environment model is:

```text
                 databricks.yml
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
         DEV       STAGING       PROD
          │           │           │
          └────── Databricks ─────┘
                      │
                Unity Catalog
                      │
              Training / Serving
```

The Databricks training notebook is aligned to the GCP-only architecture and the current leakage-safe training pipeline. It accepts environment-specific catalog, experiment and registered-model parameters from the Databricks Bundle.

The DEV training job currently uses a small single-node cluster for cost-effective Phase 6 validation. This is a validation configuration, not a claim that production workloads should always use a single node.

### Databricks runtime versus model-training time

The observed DEV job runtime must be interpreted carefully. A successful Phase 6 Databricks run took approximately **8 minutes overall**, but this does **not** mean the simple readmission models required eight minutes to train.

The majority of the runtime is infrastructure and environment startup overhead, including:

1. Databricks cluster provisioning;
2. Databricks runtime startup;
3. Spark initialization;
4. installation of the project Python wheel and dependencies;
5. notebook/task initialization;
6. cloud authentication and data-access setup.

The actual model training and candidate evaluation are lightweight and complete in a small fraction of the total job duration. The current dataset is also small, with the GCS CSV being approximately 154 KB.

This distinction is important when evaluating platform performance:

```text
Databricks Job Runtime
        │
        ├── Cluster provisioning / startup  ← dominant DEV overhead
        ├── Runtime initialization
        ├── Dependency / wheel installation
        ├── Notebook initialization
        └── ML execution                     ← lightweight; seconds-scale
```

The current single-node cluster is therefore a **validation configuration** rather than a performance benchmark. For production, compute strategy should be selected according to workload size, concurrency, latency requirements and cost. Appropriate approaches may include managed job compute, scheduled workloads, reuse of appropriately configured compute, or other Databricks compute strategies that avoid unnecessary startup overhead for latency-sensitive workloads.

The key engineering conclusion is that the observed eight-minute wall-clock runtime is primarily **platform startup overhead**, not evidence that the model-training algorithm is computationally expensive.

### GCP infrastructure resilience and capacity-aware compute placement

Cloud infrastructure failures must be distinguished from application and model failures. During Phase 6 validation, a Databricks job reached cluster provisioning but failed before notebook execution because Google Cloud could not allocate the requested VM in the selected zone:

```text
GCP_INSUFFICIENT_CAPACITY
ZONE_RESOURCE_POOL_EXHAUSTED
The zone us-central1-f does not have enough resources available
```

This is a **cloud-capacity failure**, not a Python, data, MLflow, model-quality or Unity Catalog failure. Databricks documents `GCP_INSUFFICIENT_CAPACITY` as a stockout condition and recommends changing the availability zone or instance type and enabling flexible node types where supported. citeturn0search0turn0search1

The training job therefore avoids unnecessarily pinning the validation compute to a single GCP zone:

```yaml
new_cluster:
  node_type_id: "n2-standard-4"
  gcp_attributes:
    zone_id: AUTO
```

Using `AUTO` allows Databricks to select an available zone rather than permanently constraining the job to `us-central1-f`. Databricks also documents high-availability zone placement as a way to reduce the probability of single-zone capacity issues. citeturn0search4

Flexible node types provide an additional resilience mechanism by allowing compatible alternative instance types when the preferred type is unavailable. Databricks recommends keeping flexible node types enabled unless a workload has a strict requirement for a specific instance type. citeturn0search0

For this project, the resilience strategy is therefore:

```text
Databricks Job
     ↓
Capacity-aware zone placement
     ↓
AUTO availability zone
     ↓
Flexible node types where supported
     ↓
Cluster provisioning
     ↓
Training workload
```

This is particularly important for production workloads because a correct application cannot run if its compute infrastructure cannot be provisioned. Infrastructure resilience is therefore treated as a separate acceptance dimension from ML correctness.

### Repeated DEV validation runs

Repeated successful runs strengthen the conclusion that the platform path is stable rather than the result of a one-off successful execution.

Recorded successful Phase 6 DEV runs include:

| Run | Start | End | Wall-clock duration | Result |
|---|---|---|---:|---|
| First corrected run | 15:26:16 | 15:34:42 | 8m 26s | `TERMINATED SUCCESS` |
| Second corrected run | 15:41:52 | 15:52:10 | 10m 18s | `TERMINATED SUCCESS` |

A later validation attempt exposed a separate infrastructure capacity issue in `us-central1-f`. That failure is documented above and resulted in a capacity-aware placement change rather than a change to the ML pipeline.

The variation in total duration demonstrates that wall-clock time is dominated by Databricks environment and cluster lifecycle overhead rather than deterministic model-training complexity. Successful executions reaching the training path provide a reliability signal, while capacity failures provide evidence about infrastructure resilience requirements.

This is an important engineering distinction: **application correctness, model quality, execution reliability and infrastructure availability are separate acceptance dimensions.**

Actual workspace deployment remains environment-dependent. The repository contains the deployment definitions, but a real deployment requires the target GCP/Databricks workspace and authenticated deployment configuration.

## 11. Security

Production security design:

- GCP IAM and service accounts for workload identity;
- GCP Secret Manager for application and integration secrets;
- Databricks permissions and Unity Catalog grants for data/model access;
- no credentials or tokens committed to GitHub;
- least-privilege access to Bronze, Silver, Gold and ML assets;
- MLflow logging excludes raw patient input values from inference telemetry.

## 12. Monitoring

### Infrastructure

- API latency
- request/error rates
- service availability
- throughput
- Cloud Monitoring and Cloud Logging

### Data

- missing values
- schema changes
- distribution changes
- data drift

### Model

- prediction distribution
- confidence distribution
- ROC-AUC
- Recall
- Precision
- F1
- production degradation

### Outcome feedback

```text
Prediction
    ↓
Prediction log
    ↓
Actual outcome arrives later
    ↓
Join prediction + outcome
    ↓
Calculate production performance
```

## 13. Retraining strategy

```text
Production Data
      ↓
Drift / New Labels
      ↓
Retraining Workflow
      ↓
Candidate Evaluation
      ↓
Quality Gate
      ├── Fail → Reject
      ↓
Register Model Version
      ↓
Compare with Champion
      ├── Worse → Reject
      ↓
Promote Champion
      ↓
Deploy
```

Retraining may be scheduled, triggered by significant drift, or triggered by availability of new outcome labels.

## 14. Release and rollback strategy

The production model uses Unity Catalog aliases so that deployment targets a governed model reference rather than a hard-coded version.

Example staged rollout:

```text
Model v1 → 100% production

Model v2 → candidate

Model v2 → 10% traffic
Model v1 → 90% traffic

Model v2 → 50% traffic
Model v1 → 50% traffic

Model v2 → 100% traffic
```

If the new model fails production checks, traffic can be returned to the previous approved model version.

## 15. CI/CD

GitHub Actions is the source-controlled automation layer.

The normal CI quality gate is intentionally **immutable**:

```text
Push / Pull Request
       ↓
Install dependencies
       ↓
Ruff
       ↓
Black --check
       ↓
Pytest
       ↓
Coverage reporting
```

Automated format-and-commit workflows are not part of the permanent CI design.

## 16. Implementation roadmap

### Phase 1 — Production Data Science Pipeline

**Status: COMPLETE**

- leakage-safe preprocessing
- train/test split
- baseline model
- HistGradientBoosting model
- evaluation
- persisted model artifacts
- persisted fitted preprocessing
- production inference consistency
- automated tests

### Phase 2 — MLflow Tracking and Registry

**Status: PARTIAL**

- experiment tracking foundations
- model logging
- registry integration foundations
- Unity Catalog registry configuration

Remaining work is integrated governed lifecycle validation.

### Phase 3 — GCP Data Lake + Databricks Medallion

**Status: PARTIAL**

- GCS architecture
- Bronze/Silver/Gold design
- Databricks processing architecture

Actual cloud deployment and validation remain environment-dependent.

### Phase 4 — Databricks Workflows

**Status: PARTIAL**

- Databricks Bundle foundation
- environment targets
- training job resource
- successful DEV cluster provisioning and notebook execution
- GCS access configured through the Databricks compute service account

Actual production-grade workflow hardening remains pending.

### Phase 5 — Unity Catalog

**Status: FOUNDATION COMPLETE**

- `netcareaidatabricks` catalog design
- Bronze/Silver/Gold/ML schemas
- governance SQL
- least-privilege grant templates
- governance documentation

### Phase 6 — Model Registry and Promotion

**Status: IN PROGRESS — CURRENT PHASE**

Completed/validated foundations:

- quality gate implementation
- candidate-vs-production comparison
- Unity Catalog alias helpers
- governed promotion workflow
- promotion tests
- CI quality cleanup
- production preprocessing consistency fix
- GCP-only Databricks training notebook alignment
- Databricks Bundle deployment
- GCP IAM permission required for Databricks compute to read the training dataset
- Databricks execution reaching candidate evaluation
- correction of missing recall calculation in model evaluation
- successful DEV Databricks training execution after the recall fix
- repeated successful DEV Databricks executions confirming training-path stability
- capacity-aware GCP zone placement change after `GCP_INSUFFICIENT_CAPACITY` validation failure

Current validation:

- corrected training code is deployed through the Databricks Bundle;
- the DEV training path has successfully reached training, evaluation and quality-gate completion;
- GCS access is configured for the Databricks compute service account;
- the job cluster is Unity Catalog compatible through `USER_ISOLATION`;
- the training job now uses `AUTO` GCP zone placement to reduce single-zone capacity failures;
- the remaining Phase 6 acceptance criterion is successful end-to-end Unity Catalog model registration and `champion` alias promotion on a successfully provisioned run.

### Phase 7 — Databricks Model Serving

**Status: NEXT**

- production endpoint
- serving input/output contract
- authentication
- health checks
- latency testing
- rollback

### Phase 8 — FastAPI + Cloud Run

**Status: PENDING**

- API service
- containerization
- Cloud Run deployment
- model-serving integration

### Phase 9 — GCP API Gateway

**Status: PENDING**

- API gateway
- authentication
- routing
- rate limiting

### Phase 10 — Monitoring and Drift

**Status: PENDING**

- data drift
- prediction drift
- model performance
- alerting
- Cloud Monitoring integration

### Phase 11 — Automated Retraining

**Status: PENDING**

- scheduled retraining
- trigger-based retraining
- model comparison
- automatic candidate rejection

### Phase 12 — Production CI/CD

**Status: PENDING**

- GitHub Actions
- staging deployment
- production promotion
- infrastructure deployment
- automated rollback

### Phase 13 — Production Hardening

**Status: PENDING**

- load testing
- security testing
- failure recovery
- disaster recovery
- cost optimization
- operational documentation

## 17. Current engineering state

The project is intentionally being built **phase-by-phase with explicit acceptance criteria**.

The repository should not claim production readiness merely because code has been implemented.

A phase is marked **COMPLETE** only when its acceptance criteria have been implemented and validated in the relevant target environment.

The current position is:

```text
Phase 1  → COMPLETE
Phase 2  → PARTIAL
Phase 3  → PARTIAL
Phase 4  → PARTIAL
Phase 5  → FOUNDATION COMPLETE
Phase 6  → IN PROGRESS  ← CURRENT
Phase 7  → NEXT
Phase 8  → PENDING
Phase 9  → PENDING
Phase 10 → PENDING
Phase 11 → PENDING
Phase 12 → PENDING
Phase 13 → PENDING
```

This is deliberate engineering discipline, not a deficiency in the implementation. It keeps the project honest about what has been built, what has been integrated, and what has actually been verified.

## 18. Source of truth

GitHub `main` is the source of truth for the project.

The development workflow is:

```text
Inspect GitHub
      ↓
Make the smallest clean change
      ↓
Commit to GitHub
      ↓
Pull locally
      ↓
Run tests / validation
      ↓
Validate target environment
      ↓
Document evidence
      ↓
Continue to next acceptance criterion
```

The local working tree and GitHub repository should remain synchronized throughout development.

## 19. Production ML engineering approach

This project deliberately follows a verification-first engineering process rather than treating implementation as completion.

### Why this matters

1. **Prevents false completion** — a feature can exist in code while still failing in its target environment.
2. **Makes integration failures visible early** — GCS permissions, Databricks compute configuration, Unity Catalog access and MLflow integration are validated before production claims are made.
3. **Preserves engineering traceability** — implementation, test evidence, integration evidence and deployment evidence remain distinguishable.
4. **Encourages reproducibility** — repeated execution is used to verify that a workflow is not succeeding only by chance.
5. **Protects model quality** — quality gates remain strict even when an earlier failure is caused by an implementation defect.
6. **Separates implementation from validation** — code can be technically correct while the surrounding infrastructure is still incomplete.
7. **Supports controlled progression** — each phase has explicit acceptance criteria before the next phase becomes the primary focus.
8. **Improves operational readiness** — failures such as cloud capacity exhaustion are treated as engineering signals that should influence infrastructure design, not as reasons to hide or bypass validation.

### Acceptance principle

```text
Implement
   ↓
Test
   ↓
Integrate
   ↓
Run in the target environment
   ↓
Collect evidence
   ↓
Document the result
   ↓
Only then mark the phase complete
```

> **“DONE” means verified, not merely implemented.**

This approach is particularly important for ML systems because correctness spans more than model code. Data access, preprocessing consistency, model quality, registry governance, compute availability, serving infrastructure, security, monitoring and deployment all contribute to whether the system is actually production-ready.
