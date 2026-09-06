# Phase 11 — Monitoring and Observability

This document defines the monitoring contract for the Netcare ML Platform. It is intentionally implementation-first: a capability is not considered complete merely because it is described here. Live Databricks configuration and observed telemetry must be verified before a milestone is marked complete.

## Objectives

Phase 11 provides operational visibility across:

1. serving infrastructure;
2. request and inference behaviour;
3. input-data quality and drift;
4. model prediction behaviour;
5. labelled-outcome performance; and
6. deployment/model-version state.

The monitoring architecture remains Databricks-centric and does not introduce Cloud Run or API Gateway.

## Monitoring layers

### 1. Serving / platform health

Track at minimum:

- endpoint availability and readiness;
- request volume and throughput;
- request and inference latency, including P50 and P99 where available;
- HTTP/error rates;
- request failures and timeouts;
- deployment/update state;
- active served model and model version;
- serving resource utilisation where exposed by the platform.

Operational alerts should distinguish transient serving events from sustained service degradation.

### 2. Input-data quality

Track:

- required-field completeness;
- null and missing-value rates;
- schema compatibility;
- feature range violations;
- categorical-value changes;
- unexpected feature distributions;
- input freshness where timestamps are available.

The monitoring path must avoid storing unnecessary patient identifiers or raw clinical payloads.

### 3. Prediction behaviour

Track:

- prediction counts;
- positive/negative prediction rates;
- probability/confidence distributions;
- risk-tier distributions;
- prediction rates by model version;
- sudden distribution changes relative to an approved baseline.

These signals are useful before delayed clinical outcomes become available.

### 4. Model performance

When labelled outcomes become available, calculate:

- ROC-AUC;
- Recall;
- Precision;
- F1;
- confusion-matrix counts;
- calibration/confidence behaviour where appropriate;
- performance by relevant evaluation cohorts where governance permits.

The existing quality gates remain the reference thresholds unless a later, explicitly approved change is documented.

## Data and telemetry design

The preferred design is to use Databricks-native serving telemetry and governed monitoring data. Where inference logging is required, records should contain only the fields necessary for monitoring and model-performance analysis.

Conceptually:

```text
Databricks Model Serving
        │
        ├── Endpoint / request telemetry
        │
        ├── Inference records
        │
        ▼
Governed monitoring data
        │
        ├── Platform dashboards
        ├── Data-quality checks
        ├── Drift calculations
        └── Model-performance calculations
                 │
                 ▼
              Alerts
```

The exact Databricks telemetry source and schema must be inspected in the target workspace before implementation. Do not hard-code a table name or schema that has not been observed in the deployed environment.

## Baselines

Monitoring requires explicit baselines rather than arbitrary alert thresholds.

### Serving baseline

Use the validated endpoint behaviour and observed request characteristics as the initial operational reference. Thresholds should be based on observed behaviour and service requirements.

### Data baseline

Use the approved training/validation feature distributions as the initial reference where the same feature contract is available.

### Model baseline

Use the frozen validated model evaluation as the performance reference. Candidate or replacement models must be compared against this baseline before controlled release.

## Alerts

Initial alert classes:

| Alert | Condition | Action |
|---|---|---|
| Endpoint unavailable | Serving endpoint is not ready/available | Investigate immediately |
| Elevated errors | Error rate exceeds approved operational threshold | Investigate serving/client failure |
| Latency degradation | Sustained latency exceeds approved threshold | Investigate capacity/request behaviour |
| Schema violation | Required input contract changes or fails validation | Reject/quarantine affected input |
| Data-quality degradation | Completeness/range checks exceed threshold | Investigate upstream data |
| Prediction shift | Prediction distribution materially changes | Investigate data/model behaviour |
| Feature drift | Feature distribution exceeds approved drift threshold | Feed Phase 12 review |
| Performance regression | Labelled model metrics regress beyond approved tolerance | Stop promotion/review model |

Threshold values should be committed only after they are measured or explicitly approved. This document deliberately does not invent numeric operational thresholds.

## Dashboard requirements

The initial monitoring dashboard should expose:

- endpoint status;
- request volume;
- error rate;
- P50/P99 latency where available;
- active model/version;
- prediction distribution;
- probability distribution;
- data-quality checks;
- drift status;
- latest labelled-outcome metrics;
- recent deployment/model-version events.

## Security and privacy

Monitoring must follow the same security principles as the serving system:

- do not log unnecessary patient identifiers;
- do not store raw clinical payloads when derived monitoring fields are sufficient;
- use governed Unity Catalog objects for persisted monitoring data;
- restrict monitoring access to the minimum required roles;
- keep secrets and authentication material out of telemetry;
- retain data according to the applicable organisational policy.

## Implementation sequence

### Step 11.1 — Inspect live serving telemetry

Identify the actual telemetry, endpoint metrics, inference records, system tables, and permissions available in the deployed Databricks environment.

**Exit criterion:** observed source/schema documented with evidence.

### Step 11.2 — Establish governed monitoring data

Create or configure the minimum governed monitoring datasets required for serving, data-quality, prediction, and performance monitoring.

**Exit criterion:** monitoring data is queryable and access-controlled.

### Step 11.3 — Implement health and quality checks

Implement endpoint, request, schema, completeness, and range checks.

**Exit criterion:** checks execute successfully against representative data.

### Step 11.4 — Implement prediction and drift monitoring

Calculate prediction-distribution and feature-drift signals using explicit baselines.

**Exit criterion:** drift calculations reproduce known baseline behaviour and identify controlled distribution changes.

### Step 11.5 — Implement labelled-outcome evaluation

Join predictions to subsequently available outcomes and calculate the agreed model metrics.

**Exit criterion:** metrics are reproducible and comparable with the frozen validation baseline.

### Step 11.6 — Add alerts and operational dashboard

Expose actionable alerts and the monitoring dashboard after thresholds have been evidenced or approved.

**Exit criterion:** a controlled test produces the expected alert and dashboard signal.

## Phase 11 completion rule

Phase 11 is complete only when the live monitoring path is implemented, tested, access-controlled, and evidenced in the target Databricks environment.

Documentation alone does not complete Phase 11.

## Relationship to later phases

Phase 12 consumes the drift and performance signals established here to drive retraining decisions.

Phase 13 consumes the monitoring signals to support candidate promotion, controlled traffic changes, and rollback.

The protected v1 baseline remains the rollback reference until a later model release is explicitly validated and promoted.
