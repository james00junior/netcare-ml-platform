# Serving Baseline — v1 and v8

This document records the live Databricks serving state verified on 2026-09-06. It is an evidence checkpoint, not a change to serving configuration.

## Protected baseline

Endpoint: `cidev-netcare-readmission`

- Registered model: `netcareaidatabricks.default.readmission_model`
- Model version: `1`
- Served model: `readmission_model-1`
- Traffic: `100%`
- Endpoint state: `READY`
- Config update: `NOT_UPDATING`
- Deployment state: `DEPLOYMENT_READY`
- Workload: `Small`, `CPU`
- Scale-to-zero: enabled
- Config version: `1`

This remains the protected v1 serving baseline and rollback reference.

## Candidate inference deployment

Endpoint: `cidev-netcare-readmission-candidate`

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

This confirms that model version 8 is deployed as the isolated candidate inference endpoint. It has not been promoted to the protected v1 endpoint.

## Development endpoints

The live endpoint inventory also showed:

- `dev-netcare-readmission` serving model version `1`, `READY`.
- `dev-netcare-readmission-candidate` serving model version `8`, `READY`.

## Interpretation

Model version numbers must not be interpreted as training versus inference versions. Both v1 and v8 are registered model versions; the distinction here is deployment role:

- v1 is the protected serving baseline.
- v8 is the isolated candidate serving deployment.

No telemetry configuration, traffic promotion, model replacement, or endpoint configuration change is implied by this document.

## Next verification

Before Phase 11 monitoring configuration is changed, the live Databricks telemetry/metrics surface and available inference records must be inspected. Monitoring implementation must use observed workspace capabilities and schemas rather than invented table names or fields.
