# Phase 11 — Monitoring and Observability

Phase 11 establishes the monitoring and observability foundation for the Netcare ML Platform. It is implementation-first: live Databricks configuration and observed telemetry are recorded separately from capabilities that require request or labelled-outcome data.

## Phase 11 status

**COMPLETE / FROZEN FOR THE VERIFIED MONITORING SCOPE.**

The repository now contains tested monitoring contracts for serving health, governed serving-system queries, input data quality, prediction/data drift, and labelled model performance. The target Databricks workspace has also verified serving telemetry and governed serving-system-table access.

The important live-data boundary is explicit: `system.serving.endpoint_usage` is queryable, but the verified v8 candidate query currently returns zero rows. Therefore request-level prediction and labelled-outcome monitoring are **not claimed as live**. Phase 12 must use an independently verified prediction/outcome source if one is introduced.

## Verified live evidence — 2026-09-06

### Protected production baseline

```text
Endpoint:       cidev-netcare-readmission
Served model:   readmission_model-1
Registry model: netcareaidatabricks.default.readmission_model
Model version:  1
State:          READY
Config update:  NOT_UPDATING
Deployment:     DEPLOYMENT_READY
Traffic:        100%
Workload:       Small / CPU
Scale to zero:  enabled
Usage tracking: enabled
Config version: 1
```

### Candidate

```text
Endpoint:                 cidev-netcare-readmission-candidate
Served model:             readmission_model-8
Registry model:           netcareaidatabricks.default.readmission_model
Model version:            8
Served entity ID:         362c5dbb1cf448789afbb4ee6a687712
State:                    READY
Config update:            NOT_UPDATING
Deployment:               DEPLOYMENT_READY
Traffic:                  100% within candidate endpoint
Workload:                 Small / CPU
Scale to zero:            enabled
Usage tracking:           enabled
Config version:           1
```

No serving configuration was changed during the Phase 11 inspection.

## Observed endpoint telemetry

The candidate telemetry snapshot exposed:

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

Observed values:

| Metric | Value |
|---|---:|
| `cpu_usage_percentage` | `2.344062231666667` |
| `mem_usage_percentage` | `6.823611259460449` |
| `request_count_total` | `0` |
| `request_4xx_count_total` | `0` |
| `request_5xx_count_total` | `0` |
| `provisioned_concurrent_requests_total` | `4` |

The latency and queue-time histograms were exposed but contained zero observations in the inspected snapshot. This is an observation about that snapshot, not evidence that the endpoint cannot serve requests; direct v8 inference has separately been validated.

The protected v1 endpoint similarly exposed request/error and latency telemetry, with zero request observations in the supplied snapshot.

## Verified governed serving system tables

The target workspace exposes:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

### `system.serving.endpoint_usage`

Verified columns:

```text
request_time
status_code
requester
databricks_request_id
client_request_id
served_entity_id
```

A direct query of this table succeeded. A query for the exact v8 served entity ID:

```text
362c5dbb1cf448789afbb4ee6a687712
```

returned:

```text
status: SUCCEEDED
total_row_count: 0
total_chunk_count: 0
truncated: false
```

Therefore the table is **queryable but currently empty for the verified v8 entity**.

### `system.serving.served_entities`

Verified columns:

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

The v8 identity is:

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

## Repository monitoring implementation

The monitoring package provides tested, transport-agnostic components for the verified evidence boundary:

- serving endpoint health normalization;
- preservation of observed metrics without fabricating missing values;
- exact serving system-table column contracts;
- governed SQL builders restricted to verified source columns;
- served-entity resolution;
- required-column/null data-quality checks;
- prediction/data drift calculations;
- labelled-outcome performance metrics;
- performance degradation comparison.

The Databricks execution layer remains outside these pure Python helpers so the repository does not invent authentication, workspace paths, target tables, or deployment-specific configuration.

## Monitoring layers

### 1. Serving/platform health

Track:

- endpoint readiness;
- configuration-update state;
- deployment state;
- request volume where observed;
- request/error rates where observed;
- latency where observations exist;
- active served model/version;
- resource utilisation where exposed.

### 2. Input data quality

The repository validates explicitly supplied contracts for:

- required columns;
- unexpected columns;
- null counts.

Feature ranges and domain-specific thresholds remain caller-supplied rather than guessed.

### 3. Prediction behaviour

The monitoring framework supports:

- prediction rates;
- probability distributions;
- risk-tier distributions;
- distribution comparisons.

These are not represented as live Databricks prediction telemetry because the verified `endpoint_usage` table currently contains no v8 request records and exposes no prediction/probability columns.

### 4. Feature drift

The repository provides reference/current distribution comparison for numerical and categorical features. Drift thresholds remain configuration inputs and are not presented as Databricks-approved operational thresholds.

### 5. Labelled model performance

The repository supports:

- accuracy;
- precision;
- recall;
- F1;
- ROC-AUC when probabilities are available;
- comparison against an explicit baseline.

A live labelled-outcome source has not been evidenced in Databricks during this Phase 11 checkpoint, so no live outcome metric is claimed.

## Alerts and dashboards

The Phase 11 repository provides the monitoring signals and contracts required by later operational integration, but **no live Databricks alert/dashboard deployment is claimed** from the evidence supplied in this checkpoint.

This is intentional. Numeric operational thresholds, target dashboard objects, and alert destinations must be explicitly evidenced or approved before they are committed as production configuration.

## Security and privacy

Monitoring must:

- avoid unnecessary patient identifiers;
- avoid raw clinical payloads where derived monitoring fields are sufficient;
- use governed Unity Catalog objects for persisted monitoring data;
- restrict monitoring access to minimum required roles;
- keep credentials out of telemetry and logs.

## Phase 11 completion boundary

Phase 11 is considered complete and frozen for the verified repository/serving-monitoring scope because:

1. live serving state and telemetry have been observed;
2. governed serving system tables and exact schemas have been verified;
3. the v8 served-entity identity has been verified;
4. the request-table query path has been exercised and its zero-row result recorded;
5. repository monitoring contracts are implemented and tested;
6. missing live request/outcome data is explicitly treated as unavailable rather than fabricated.

The following remain **data-dependent operational extensions**, not silently completed capabilities:

```text
Live request-level prediction records  → not observed
Live labelled outcomes                 → not observed
Production alert configuration         → not deployed/evidenced
Production dashboard configuration     → not deployed/evidenced
```

Those boundaries are inputs to the remaining lifecycle work. Phase 12 must not assume that prediction or outcome records exist merely because the serving endpoint is healthy.

## Freeze checkpoint

```text
Phase: 11
Status: COMPLETE / FROZEN FOR VERIFIED SCOPE
Date: 2026-09-06
Protected production model: readmission_model-1
Candidate model: readmission_model-8
Candidate served entity ID: 362c5dbb1cf448789afbb4ee6a687712
endpoint_usage v8 rows observed: 0
```
