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

## Verified live evidence — 2026-09-06

The Phase 11 telemetry inspection has now been performed against both the protected baseline and isolated candidate endpoint:

```text
Protected baseline
Endpoint:       cidev-netcare-readmission
Served model:   readmission_model-1
Registry model: netcareaidatabricks.default.readmission_model
Model version:  1

Candidate
Endpoint:       cidev-netcare-readmission-candidate
Served model:   readmission_model-8
Registry model: netcareaidatabricks.default.readmission_model
Model version:  8
```

### Observed endpoint metrics — v1 protected baseline

The live Prometheus/OpenMetrics export for `cidev-netcare-readmission` exposed:

```text
request_count_total
request_4xx_count_total
request_5xx_count_total
request_latency_ms
```

Observed values in the supplied telemetry snapshot, timestamped `1788718020000`:

| Metric | Observed value |
|---|---:|
| `request_count_total` | `0.0` |
| `request_4xx_count_total` | `0.0` |
| `request_5xx_count_total` | `0.0` |
| `request_latency_ms_count` | `0.0` |
| `request_latency_ms_sum` | `0.0` |

All reported request-latency histogram buckets from `5` ms through `600000` ms and `+Inf` were `0.0` in this snapshot.

This is a telemetry snapshot with no recorded requests in the reported minute. It is not evidence that the endpoint cannot serve requests.

### Observed endpoint metrics — v8 candidate

The live Prometheus/OpenMetrics export for `cidev-netcare-readmission-candidate` exposed:

```text
cpu_usage_percentage
mem_usage_percentage
request_count_total
request_4xx_count_total
request_5xx_count_total
request_latency_ms
model_queue_time_ms
provisioned_concurrent_requests_total
```

Observed values in the supplied telemetry snapshot:

| Metric | Observed value |
|---|---:|
| `cpu_usage_percentage` | `2.344062231666667` |
| `mem_usage_percentage` | `6.823611259460449` |
| `request_count_total` | `0.0` |
| `request_4xx_count_total` | `0.0` |
| `request_5xx_count_total` | `0.0` |
| `provisioned_concurrent_requests_total` | `4.0` |

The request-latency and model-queue-time histograms were also exposed. Their reported snapshot contained zero observations (`count=0`, `sum=0`). A separate live v8 inference request has already been verified successfully.

### v1 versus v8 telemetry comparison

The two live exports confirm that both endpoints expose request/error and latency telemetry, while the v8 candidate export additionally exposed CPU, memory, provisioned-concurrency, and model-queue-time metrics in the observed snapshot.

This comparison is limited to the exact metrics returned by the two supplied exports. It does not establish that metrics absent from one snapshot are unavailable from the workspace generally.

### Verified governed serving system tables

The target workspace exposes these Databricks serving system tables:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

`system.serving.endpoint_usage` was verified with 114,721,404 rows and a request-time range from `2026-05-17 00:00:00.374000` through `2026-09-06 18:11:59.375000`. Its observed schema contains per-request fields including `request_time`, `status_code`, `requester`, `databricks_request_id`, `client_request_id`, and `served_entity_id`.

`system.serving.served_entities` was verified with 9,645 rows. Its observed schema contains endpoint/model identity fields including `served_entity_id`, `endpoint_name`, `served_entity_name`, `entity_name`, `entity_version`, `endpoint_config_version`, `custom_model_config`, `change_time`, and `endpoint_delete_time`.

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

### Observed endpoint configuration

The live endpoint GET responses previously verified:

```text
v1 endpoint: cidev-netcare-readmission
  config_version:       1
  endpoint state:       READY
  config update:        NOT_UPDATING
  deployment:           DEPLOYMENT_READY
  served model:         readmission_model-1
  registered model:     netcareaidatabricks.default.readmission_model
  registered version:   1
  traffic:              100%
  workload:             Small / CPU
  scale to zero:        enabled
  route optimized:      false
  permission:           CAN_MANAGE

v8 candidate endpoint: cidev-netcare-readmission-candidate
  config_version:       1
  endpoint state:       READY
  config update:        NOT_UPDATING
  deployment:           DEPLOYMENT_READY
  served model:         readmission_model-8
  registered model:     netcareaidatabricks.default.readmission_model
  registered version:   8
  traffic:              100% within candidate endpoint
  workload:             Small / CPU
  scale to zero:        enabled
  route optimized:      false
  permission:           CAN_MANAGE
```

No serving configuration was changed during this monitoring inspection.

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

The verified serving telemetry path currently consists of Databricks endpoint metrics plus the governed serving system tables. The system-table usage path is queryable, but the exact v8 candidate entity currently has zero matching `endpoint_usage` rows. Therefore prediction-level and labelled-outcome monitoring must not be represented as implemented from that table until records are actually observed or another approved source is verified.

Conceptually:

```text
Databricks Model Serving
        │
        ├── Endpoint / request telemetry  ← verified
        │
        └── Serving system tables
              ├── served_entities          ← verified
              └── endpoint_usage           ← queryable; v8 rows not yet observed
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

No inference-record population or telemetry configuration is assumed beyond the observed evidence.

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

**Current status:** **VERIFIED FOR ENDPOINT TELEMETRY + SERVING SYSTEM-TABLE ACCESS.** Live endpoint metrics for both the protected v1 baseline and isolated v8 candidate have been observed. `system.serving.endpoint_usage` and `system.serving.served_entities` are queryable, and the exact v8 served entity has been verified. The v8-specific `endpoint_usage` query returned zero rows, so request-record population remains unverified.

**Exit criterion:** observed source/schema documented with evidence. **Met for the inspected endpoint telemetry and system-table surfaces; request-record population remains open.**

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
