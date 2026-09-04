# Netcare ML Platform

Production-oriented ML platform for **30-day hospital readmission prediction**, designed exclusively for **Google Cloud Platform (GCP)** with **Databricks on GCP**.

> **Platform constraint:** Azure is not part of this architecture or implementation. All cloud, data, ML lifecycle, serving and CI/CD decisions in this repository target GCP + Databricks on GCP.

## 1. Platform objective

The platform turns hospital encounter data into a governed machine-learning service that can:

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
| Data lake | **Google Cloud Storage** | Durable raw and curated data storage |
| Data engineering | **Databricks on GCP** | Processing and orchestration |
| Storage format | **Delta Lake** | Reliable analytical tables |
| Architecture | **Bronze / Silver / Gold** | Data quality and transformation boundaries |
| Governance | **Unity Catalog** | Data/model governance, permissions and lineage |
| Experiment tracking | **MLflow** | Parameters, metrics, artifacts and runs |
| Model registry | **Unity Catalog + MLflow** | Governed model versions and aliases |
| Training | **scikit-learn / HistGradientBoosting** | Readmission classification |
| Serving | **Databricks Model Serving** | Managed inference |
| Integration | **FastAPI / Cloud Run** | External API integration |
| API gateway | **GCP API Gateway** | External API entry point |
| Secrets | **GCP Secret Manager** | Secret management |
| CI/CD | **GitHub Actions** | Automated quality and deployment gates |
| Observability | **Cloud Monitoring / Cloud Logging** | Infrastructure and application monitoring |

The current ML workload is **CPU-only**. No GPU is required for the baseline readmission models because the workload is small tabular classification rather than GPU-oriented deep learning. Compute is therefore optimized around CPU capacity, memory, storage, reliability and cost rather than accelerator capacity.

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
├── docs/                    # Architecture and governance docs
├── .github/workflows/       # CI/CD pipelines
└── run_pipeline.py          # Local end-to-end pipeline
```

## 5. Data architecture

### Bronze

Raw landing layer. Source data is retained close to its original representation and is not used directly for model training.

### Silver

Validated and standardized encounter data. Processing includes schema validation, missing-value handling, categorical normalization and duplicate handling as appropriate.

### Gold

Analytics- and ML-ready datasets containing approved features for downstream training and serving.

### Unity Catalog

The current Databricks governance design uses the verified catalog:

```text
netcareaidatabricks
├── bronze
├── silver
├── gold
└── ml
```

Planned ML assets include:

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
- no unacceptable regression against the production model when a production comparison is available.

Registration and promotion remain separate governance operations. The implementation uses Unity Catalog aliases rather than legacy MLflow model stages.

### Quality-gate failure and remediation

The first Databricks candidate execution reached the quality gate and reported:

```text
Candidate rejected by Phase 6 quality gate: ('recall failed',)
```

Investigation showed that this was **not a model-quality failure**. Both training helpers were returning accuracy and ROC-AUC but had omitted recall from the metric dictionary. The strict quality gate correctly treated the missing metric as unacceptable.

The engineering response was to fix the training/evaluation implementation rather than weaken the gate. Both Logistic Regression and HistGradientBoosting now explicitly calculate recall from test predictions and return it with candidate metrics.

After that remediation, the Databricks training path completed successfully and the quality gate was reached with the required recall metric available.

This produced an important engineering lesson:

> **A failed quality gate should first trigger investigation of the evaluation implementation and evidence, not relaxation of the acceptance threshold.**

## 7. Current model baseline

The leakage-safe local pipeline currently evaluates:

| Model | Accuracy | ROC-AUC | Recall | F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.653 | 0.710 | 0.692 | 0.509 |
| HistGradientBoosting | 0.713 | 0.711 | 0.628 | 0.533 |

These are development/assessment results on the supplied dataset and **must not be interpreted as production clinical performance claims**.

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

Environment-specific configuration belongs in deployment configuration and secret management. Credentials must never be committed to the repository.

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

The final serving contract will be aligned with the actual Databricks serving input schema before production deployment.

## 10. Databricks on GCP

Databricks resources are managed as code through the Declarative Automation Bundle under `databricks/`.

The environment model is:

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

The training notebook accepts environment-specific catalog, experiment, registered-model and GCS data-path parameters from the Bundle.

### Compute decision: CPU, not GPU

The baseline workload is tabular classification using Logistic Regression and HistGradientBoosting. The dataset is small and the models are CPU-efficient. GPU infrastructure would add cost and operational complexity without providing a justified benefit for this workload.

The engineering decision is therefore:

```text
Small tabular ML workload
          ↓
CPU compute
          ↓
Small / cost-controlled cluster
          ↓
Scale only when workload requirements justify it
```

This does **not** mean production must always use a single-node cluster. Production compute should be selected according to dataset size, concurrency, latency, reliability and cost requirements.

### Databricks runtime versus model-training time

A successful DEV run took approximately eight minutes wall-clock time. That duration should not be interpreted as model-training time.

The observed runtime includes infrastructure and environment lifecycle overhead such as:

1. cluster provisioning;
2. Databricks runtime startup;
3. Spark initialization;
4. project wheel installation;
5. notebook/task initialization;
6. cloud authentication and data-access setup.

The actual baseline model training and candidate evaluation are lightweight relative to cluster startup.

```text
Databricks Job Runtime
        │
        ├── Cluster provisioning / startup
        ├── Runtime initialization
        ├── Dependency / wheel installation
        ├── Notebook initialization
        └── ML execution                 ← lightweight
```

The current single-node configuration is therefore a **DEV validation configuration**, not a production performance benchmark.

## 11. Infrastructure engineering decisions and lessons learned

This section records the infrastructure decisions made during implementation and the improvements that resulted from real target-environment validation.

### 11.1 Initial decision: small single-node CPU compute

The first implementation deliberately used a small single-node CPU cluster because:

- the dataset is small;
- the baseline models are CPU-oriented;
- distributed Spark execution is not required for the current training workload;
- minimizing DEV cost and startup complexity is reasonable during assessment development.

This remains a valid **DEV workload decision**.

The mistake was not choosing CPU or single-node compute. The initial configuration did not sufficiently account for **cloud-capacity resilience**.

### 11.2 What failed

A Databricks training attempt failed during cluster provisioning with:

```text
GCP_INSUFFICIENT_CAPACITY
ZONE_RESOURCE_POOL_EXHAUSTED
```

The job failed before notebook execution. Therefore the failure was infrastructure capacity, not:

- Python code;
- package imports;
- GCS permissions;
- data validation;
- preprocessing;
- model training;
- MLflow;
- quality-gate logic;
- Unity Catalog.

Databricks documents `GCP_INSUFFICIENT_CAPACITY` as a GCP capacity/stockout condition and identifies changing instance type or availability-zone strategy and using flexible node types as resilience measures. [D1]

### 11.3 Why `AUTO` alone was insufficient

The first response was to replace a fixed zone with:

```yaml
gcp_attributes:
  zone_id: AUTO
```

This was useful because it removed a hard dependency on one specific zone. However, `AUTO` does **not** guarantee capacity. It can select a zone that is still capacity-constrained for the requested VM type. [D2]

That happened in practice: the subsequent attempt was placed in `us-central1-c` and again failed with GCP capacity exhaustion.

The lesson is:

> **Zone flexibility and instance-type flexibility solve different parts of the capacity problem.**

### 11.4 Improved decision: flexible CPU node types

The job now uses a preferred CPU instance type plus compatible alternatives through Databricks flexible node-type configuration:

```yaml
node_type_id: "c4-standard-4"
driver_node_type_id: "c4-standard-4"
driver_node_type_flexibility:
  alternate_node_type_ids:
    - "c3-standard-4"
    - "c3d-standard-4"
    - "n4-standard-4"
    - "c4d-standard-4"
```

The purpose is not to make the cluster larger. The purpose is to increase the probability that a **small CPU workload can obtain compatible compute capacity** without requiring a specific VM shape.

Databricks supports flexible node types for GCP compute and exposes driver node flexibility in Declarative Automation Bundles. [D3] [D4]

### 11.5 Region versus zone decision

The architecture uses the **`us-central1` GCP region**. The exact availability zone does not need to be identical across every component. The important architectural decision is to keep latency-sensitive data and compute in an appropriate common region while allowing compute placement to vary between zones when that improves availability.

For this platform:

```text
GCP region: us-central1

GCS: regional / region-aligned storage strategy
Databricks compute: us-central1
Compute zone: capacity-aware selection
```

A zone mismatch is therefore not itself an architectural failure. A rigid dependency on a capacity-constrained zone is the problem. Databricks documents both automatic zone placement and high-availability zone placement as supported GCP strategies. [D2]

### 11.6 Why we did not solve capacity by adding GPUs

The capacity failures did **not** indicate insufficient compute performance. They indicated that GCP could not provision the requested CPU VM.

Adding GPUs would therefore solve the wrong problem and increase cost and operational complexity.

The correct response was:

```text
Capacity failure
      ↓
Diagnose provisioning layer
      ↓
Keep workload CPU-only
      ↓
Increase compatible CPU placement options
      ↓
Re-run target environment validation
```

### 11.7 Why we did not automatically increase cluster size

A larger cluster is not inherently more resilient to stockouts. It can require more VM capacity and can therefore make provisioning harder.

For the current small tabular workload, the engineering preference is:

> **Use the minimum compute required by the workload, but remove unnecessary infrastructure rigidity.**

Scaling out should happen when workload requirements justify it, not simply because a provisioning failure occurred.

### 11.8 Engineering maturity lesson

The most important improvement was methodological:

```text
Initial design assumption
        ↓
Target-environment execution
        ↓
Observed failure
        ↓
Layer-specific diagnosis
        ↓
Architecture decision update
        ↓
Targeted remediation
        ↓
Repeat validation
```

This is preferable to hiding infrastructure failures or repeatedly changing configuration without evidence.

## 12. Repeated target-environment validation

The implemented training path has been executed successfully multiple times after the evaluation defect was fixed.

Recorded successful DEV runs include:

| Run | Start | End | Wall-clock duration | Result |
|---|---|---|---:|---|
| First corrected run | 15:26:16 | 15:34:42 | 8m 26s | `TERMINATED SUCCESS` |
| Second corrected run | 15:41:52 | 15:52:10 | 10m 18s | `TERMINATED SUCCESS` |

These executions demonstrate that the implemented data/training path can:

- provision Databricks compute;
- install the packaged project wheel;
- import `src` correctly in the Databricks runtime;
- access the GCS dataset;
- validate and preprocess the data;
- train candidate models;
- calculate recall;
- apply the strict quality gate;
- complete successfully.

A later capacity failure occurred during cluster provisioning. That failure is an infrastructure acceptance issue and is documented separately rather than being incorrectly classified as an ML pipeline failure.

## 13. Current acceptance status

The current engineering state must distinguish **implemented and successfully executing stages** from the remaining integration acceptance criterion.

```text
Data ingestion / access       → RUNNING SUCCESSFULLY
Preprocessing                 → RUNNING SUCCESSFULLY
Model training                → RUNNING SUCCESSFULLY
Evaluation                    → RUNNING SUCCESSFULLY
Quality gate                  → RUNNING SUCCESSFULLY
Databricks Bundle deployment  → RUNNING SUCCESSFULLY
GCP compute access            → CONFIGURED
GCS dataset access            → CONFIGURED

Unity Catalog registration   → REMAINING ACCEPTANCE ITEM
Unity Catalog champion alias → REMAINING ACCEPTANCE ITEM
```

**Phase 6 is not blocked by the ML pipeline.** The remaining acceptance item is to prove the full governed registry operation in the target Databricks Unity Catalog environment: create/register the model version successfully and assign the `champion` alias.

No phase should be marked fully complete until its acceptance criteria have been demonstrated in the relevant target environment.

## 14. Security

Production security design:

- GCP IAM and service accounts for workload identity;
- GCP Secret Manager for application and integration secrets;
- Databricks permissions and Unity Catalog grants for data/model access;
- no credentials or tokens committed to GitHub;
- least-privilege access to Bronze, Silver, Gold and ML assets;
- inference telemetry should avoid logging raw patient input values.

## 15. Monitoring

### Infrastructure

- API latency
- request/error rates
- service availability
- throughput
- Cloud Monitoring
- Cloud Logging

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

## 16. Retraining strategy

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

## 17. Release and rollback strategy

The production model uses Unity Catalog aliases so that deployment targets a governed model reference rather than a hard-coded version.

Example staged rollout:

```text
Model v1 → 100% production

Model v2 → candidate

Model v2 → controlled rollout
Model v1 → remaining traffic

Model v2 → expanded rollout

Model v2 → 100% traffic
```

If the new model fails production checks, traffic can be returned to the previous approved model version.

## 18. CI/CD

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

CI should reject defects rather than automatically weakening tests or quality thresholds.

## 19. Implementation roadmap

### Phase 1 — Production Data Science Pipeline

**Status: COMPLETE**

- leakage-safe preprocessing
- train/test split
- Logistic Regression baseline
- HistGradientBoosting baseline
- evaluation
- persisted model artifacts
- persisted fitted preprocessing
- production inference consistency
- automated tests

### Phase 2 — MLflow Tracking and Registry

**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

- experiment tracking foundations
- model logging
- registry integration foundations
- Unity Catalog registry configuration

Remaining registry acceptance is tracked under Phase 6.

### Phase 3 — GCP Data Lake + Databricks Medallion

**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

- GCS architecture
- Bronze/Silver/Gold design
- Databricks processing architecture
- GCS dataset access from Databricks compute

Further production-scale data engineering remains a hardening concern rather than a current training-path blocker.

### Phase 4 — Databricks Workflows

**Status: IMPLEMENTED / EXECUTION PATH VALIDATED**

- Databricks Bundle foundation
- environment targets
- training job resource
- packaged Python wheel deployment
- successful DEV notebook execution
- GCS access configuration

Further production workflow hardening remains pending.

### Phase 5 — Unity Catalog

**Status: FOUNDATION COMPLETE**

- verified `netcareaidatabricks` catalog
- Bronze/Silver/Gold/ML schema design
- governance SQL
- least-privilege grant templates
- governance documentation

### Phase 6 — Model Registry and Promotion

**Status: IN PROGRESS — CURRENT PHASE**

Completed/validated:

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
- correction of missing recall calculation
- successful DEV training execution after the recall fix
- repeated successful DEV training executions
- capacity-aware compute remediation after GCP stockout validation

**Remaining acceptance criterion:** successfully register a model version in `netcareaidatabricks.ml` and assign the governed `champion` alias during a successful target-environment run.

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

## 20. Engineering decision log

| Decision / observation | Evidence | Engineering response |
|---|---|---|
| Baseline workload does not need GPUs | Small tabular classification workload | Use CPU-first infrastructure |
| Single-node is sufficient for current DEV training workload | Lightweight models and small dataset | Keep small compute for DEV; do not confuse with production scaling strategy |
| Databricks package import failed initially | `ModuleNotFoundError: No module named 'src'` | Package `src` as a wheel and install it through the Bundle |
| Quality gate reported missing recall | Training metrics omitted recall | Fix evaluation metrics; keep strict quality gate unchanged |
| GCS access failed from Databricks compute | Target environment required explicit object access | Grant the required service-account object-viewer permission |
| Fixed zone caused stockout | `GCP_INSUFFICIENT_CAPACITY` / `ZONE_RESOURCE_POOL_EXHAUSTED` | Remove unnecessary fixed-zone dependency |
| `AUTO` changed the selected zone but did not guarantee capacity | Subsequent stockout in another zone | Add flexible compatible CPU node types |
| Adding GPUs would not address the failure | Failure occurred during CPU VM provisioning | Keep infrastructure CPU-only |
| Increasing node count is not automatically a resilience solution | Larger clusters can require more capacity | Prefer minimal compute with greater placement flexibility |
| Successful repeated executions matter | Two corrected DEV runs completed successfully | Use repeated target-environment validation as evidence |
| Unity Catalog registration remains unproven | Training and quality gate succeed before registry acceptance | Focus next work on UC registration/version/alias validation |

## 21. Verification-first engineering approach

This project deliberately follows a verification-first engineering process rather than treating implementation as completion.

### Why this matters

1. **Prevents false completion** — code can exist while its target environment still fails.
2. **Makes integration failures visible** — GCS permissions, Databricks packaging, compute capacity and registry access are tested in context.
3. **Preserves traceability** — implementation, test evidence and deployment evidence remain distinguishable.
4. **Encourages reproducibility** — repeated executions strengthen confidence in the workflow.
5. **Protects model quality** — quality thresholds remain strict when implementation defects are found.
6. **Separates infrastructure from application failures** — a cluster stockout is not reported as an ML failure.
7. **Supports controlled progression** — each phase has explicit acceptance criteria.
8. **Improves architecture through evidence** — real failures become inputs to better engineering decisions.

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
Observe failures and evidence
   ↓
Diagnose the correct layer
   ↓
Make the smallest justified change
   ↓
Repeat validation
   ↓
Document the decision
   ↓
Only then mark the acceptance criterion complete
```

> **“DONE” means verified, not merely implemented.**

## 22. Source of truth and engineering workflow

GitHub `main` is the source of truth for the project.

The development workflow is:

```text
Inspect GitHub
      ↓
Identify the exact problem
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
Document evidence and decision
      ↓
Continue to the next acceptance criterion
```

The local working tree and GitHub repository should remain synchronized throughout development.

## 23. References and evidence

The references below use ordinary Markdown links so that they render correctly on GitHub. External references support architectural and platform claims; project-specific references record implementation and remediation evidence.

### Official platform references

- [D1 — Databricks: GCP cluster error codes](https://docs.databricks.com/gcp/en/compute/troubleshooting/cluster-error-codes) — capacity/stockout diagnosis and remediation guidance.
- [D2 — Databricks: Configure compute on GCP](https://docs.databricks.com/gcp/en/compute/configure) — GCP availability-zone and compute configuration behaviour.
- [D3 — Databricks: Flexible node types on GCP](https://docs.databricks.com/gcp/en/compute/instance-families) — flexible-node capacity resilience and compatible compute concepts.
- [D4 — Databricks: Declarative Automation Bundles resource reference](https://docs.databricks.com/aws/en/dev-tools/bundles/resources) — Bundle resource configuration, including compute settings.
- [G1 — Google Cloud Storage locations](https://cloud.google.com/storage/docs/locations) — regional storage and location considerations.
- [M1 — MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/) — model registration and lifecycle concepts.
- [U1 — Databricks Unity Catalog](https://docs.databricks.com/gcp/en/data-governance/unity-catalog/) — governance and catalog concepts.

### Project implementation evidence

- [E1 — Recall metric remediation commit](https://github.com/james00junior/netcare-ml-platform/commit/da20185f52ff29f27d3dba021c8b75ca3ca94c53) — adds explicit recall calculation to the baseline training path.
- [E2 — HistGradientBoosting recall remediation commit](https://github.com/james00junior/netcare-ml-platform/commit/5cbde8f79b32a32a2b2dcc541d9994f91c19a53) — adds explicit recall calculation to the GBDT path.
- [E3 — Databricks training notebook alignment](https://github.com/james00junior/netcare-ml-platform/commit/4d127e3db11be12f74a60ba22eb83e37a204296f) — aligns the Databricks training notebook with the governed promotion workflow.
- [E4 — Databricks Bundle artifact-path fix](https://github.com/james00junior/netcare-ml-platform/commit/a84c00b05cf387966de989bcabdfcc270c8508d1) — fixes wheel build/source path handling.
- [E5 — Unity Catalog catalog configuration](https://github.com/james00junior/netcare-ml-platform/commit/51bdaa1f4270c8aa0e643f554263433a10d35557) — aligns Bundle configuration with the verified `netcareaidatabricks` catalog.
- [E6 — GCP flexible CPU fallback configuration](https://github.com/james00junior/netcare-ml-platform/commit/cdce69b0dea0a7ecb5871ca9032bfac75df86b2a) — adds preferred and alternate CPU node types for capacity resilience.

### Verification evidence

The current repository records successful target-environment executions and the infrastructure capacity incidents that informed the compute redesign. Databricks run URLs and timestamps are intentionally recorded in the engineering notes above so that the implementation history remains auditable without confusing infrastructure incidents with ML pipeline failures.

## 24. Final engineering position

The project has moved from a locally validated ML pipeline to a target-environment Databricks execution path with explicit governance, packaging, GCS access, quality gates and infrastructure-resilience decisions.

The key lessons from implementation are not that the first configuration was perfect. The key lessons are that:

- compute should match the workload;
- GPU infrastructure is unnecessary for this baseline;
- small DEV compute is appropriate when the workload is small;
- infrastructure capacity must be designed separately from model performance;
- `AUTO` zone selection is useful but not sufficient by itself;
- compatible CPU flexibility is a better response to this capacity problem than adding unnecessary compute;
- strict quality gates should be fixed at the evaluation layer when metrics are missing;
- repeated target-environment execution is stronger evidence than local assumptions;
- Unity Catalog registration and promotion must be demonstrated before Phase 6 is marked complete.

The engineering objective is therefore not to pretend that every first decision was optimal. It is to make each decision **evidence-driven, testable, explainable and progressively more resilient**.
