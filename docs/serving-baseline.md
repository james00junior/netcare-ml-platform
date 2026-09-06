# Serving Baseline — v1 and v8

This document records the live Databricks serving state verified on 2026-09-06. It is an evidence checkpoint, not a change to serving configuration.

## Protected baseline

Endpoint: `cidev-netcare-readmission`

- Endpoint ID: `044cf254e6f3475d948e511d7945905f`
- Registered model: `netcareaidatabricks.default.readmission_model`
- Model version: `1`
- Served model: `readmission_model-1`
- Traffic: `100%`
- Endpoint state: `READY`
- Config update: `NOT_UPDATING`
- Deployment state: `DEPLOYMENT_READY`
- Deployment state message: `Scaled to zero`
- Workload: `Small`, `CPU`
- Scale-to-zero: enabled
- Config version: `1`
- Route optimized: `false`
- Permission level: `CAN_MANAGE`
- Creation timestamp: `1788710444000`
- Last updated timestamp: `1788710444000`

This remains the protected v1 serving baseline and rollback reference.

## Candidate inference deployment

Endpoint: `cidev-netcare-readmission-candidate`

- Endpoint ID: `d8e17cedddda498c9bad212619250597`
- Registered model: `netcareaidatabricks.default.readmission_model`
- Model version: `8`
- Served model: `readmission_model-8`
- Traffic: `100%` within the candidate endpoint
- Endpoint state: `READY`
- Config update: `NOT_UPDATING`
- Deployment state: `DEPLOYMENT_READY`
- Workload: `Small`, `CPU`
- Scale-to-zero: enabled
- Config version: `1`
- Route optimized: `false`
- Permission level: `CAN_MANAGE`
- Creation timestamp: `1788710444000`
- Last updated timestamp: `1788710444000`

This confirms that model version 8 is deployed as the isolated candidate inference endpoint. It has not been promoted to the protected v1 endpoint.

## Direct v8 inference evidence

A live invocation of `cidev-netcare-readmission-candidate` was verified using the endpoint's observed OpenAPI request contract. The observed response was:

```json
{
  "predictions": [
    {
      "model_version": "champion",
      "predicted_label": 0,
      "probability": 0.32462546453278807,
      "risk_tier": "medium"
    }
  ]
}
```

The endpoint configuration identifies registered model version `8` / served model `readmission_model-8`. The response field `model_version` was observed as `champion` and is recorded exactly as returned; no interpretation is added here.

## Development endpoints

The live endpoint inventory also showed:

- `dev-netcare-readmission` serving model version `1`, `READY`.
- `dev-netcare-readmission-candidate` serving model version `8`, `READY`.

## Interpretation

Model version numbers must not be interpreted as training versus inference versions. Both v1 and v8 are registered model versions; the distinction here is deployment role:

- v1 is the protected serving baseline.
- v8 is the isolated candidate serving deployment.

No telemetry configuration, traffic promotion, model replacement, or endpoint configuration change is implied by this document.

## Monitoring evidence checkpoint

Candidate v8 serving telemetry was inspected separately through the Databricks metrics surface. The observed metrics included CPU usage, memory usage, request count, 4xx/5xx counts, provisioned concurrent requests, request latency, and model queue time. That evidence is recorded in `docs/monitoring.md`.

The protected v1 endpoint configuration above does not include telemetry or inference-table configuration in the returned `config` object. This does not establish that no other monitoring or inference-record capability exists in the workspace.

## Next verification

The next Databricks inspection is to obtain the same live metrics surface for the protected v1 endpoint and compare it with the already observed v8 candidate metrics. After that, the available inference-record/monitoring data source and its actual schema and permissions must be identified before any monitoring configuration is changed.
