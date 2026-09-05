# Phase 7 — Serving Debugging Record

## Purpose

This document records the evidence and remediation history for Phase 7 model serving. The existing serving endpoint remains protected while the current candidate is debugged through an isolated endpoint.

## Protected serving baseline

Databricks Model Serving endpoint:

`dev_james_mashiyane_za_dev-netcare-readmission`

Current active configuration:

- model: `netcareaidatabricks.default.readmission_model`
- version: `1`
- deployment state: `DEPLOYMENT_READY`
- traffic: 100%
- scale to zero: enabled

Version 1 is the protected known-good serving baseline. It is not being modified as part of Phase 7 candidate debugging.

## Current candidate

Registered model version:

`8`

Evidence:

- MLflow registration status: `READY`
- run ID: `bf12e7f602084e78acdab4797c40c2b2`
- model source: `models:/m-9fe9fb289f7546f0b0cf4e137422ccdb`
- Unity Catalog alias: `champion -> 8`

The Phase 7 deployment configuration now includes an isolated candidate endpoint whose explicit model version defaults to `8`. The protected endpoint continues to use explicit version `1`.

## Candidate failures observed before version 8

### Version 2 — source package missing

Observed error:

```text
ModuleNotFoundError: No module named 'src'
```

The serving artifact did not contain the application source package required to deserialize `ReadmissionServingModel`.

**Remediation:** package the `src` tree explicitly with the MLflow PyFunc artifact.

### Version 3 — packaging remediation

The source-packaging approach was changed so the MLflow artifact explicitly includes the application package. This moved the failure boundary from missing source code to runtime compatibility.

### Version 4 — scikit-learn deserialization mismatch

Observed error:

```text
AttributeError: Can't get attribute '__pyx_unpickle_CyHalfBinomialLoss' on module sklearn._loss._loss
```

The serving environment was not compatible with the serialized scikit-learn estimator.

### Version 5 — same runtime compatibility problem

The same scikit-learn deserialization failure remained after the first dependency adjustment. The declared serving environment still did not reliably reproduce the training environment.

### Version 6 — candidate still not deployment-ready

The candidate deployment continued to fail during model-server loading. The engineering decision is now to diagnose the current candidate through direct serving deployment rather than create another replacement model version.

## Root-cause categories discovered so far

1. **Artifact packaging:** application source was not initially included in the MLflow model artifact.
2. **Runtime compatibility:** the serving environment did not initially match the environment used to serialize the scikit-learn model.

The current registry implementation derives serialization-sensitive package versions from the actual training environment when the artifact is created.

## Engineering rule

A failed deployment candidate is not discarded merely because a new failure is discovered. The candidate remains the debugging target until the failure boundary is understood and the targeted fix is validated.

A new model version should only be created when the model or training result intentionally changes.

## Version 8 deployment investigation

The next validation is an isolated deployment of registered model version `8`.

```text
Registered v8
    ↓
Isolated candidate serving endpoint
    ↓
Databricks model-server load
    ↓
Capture actual deployment logs
    ↓
Identify exact exception
    ↓
Apply targeted fix
    ↓
Redeploy v8
```

This is deliberately separate from the protected version-1 serving endpoint.

## Validation sequence

```text
Protected v1
    ↓
Freeze
    ↓
Deploy current candidate v8 in isolation
    ↓
Inspect actual model-server failure, if any
    ↓
Targeted fix
    ↓
Redeploy v8
    ↓
DEPLOYMENT_READY
    ↓
Direct inference
    ↓
FastAPI integration
```

## Current status

Phase 7 remains in progress. Training and registration of version 8 have been validated. The next unresolved boundary is the isolated deployment and model-server loading of version 8.
