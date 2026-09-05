# Phase 7 — Serving Debugging Record

## Purpose

This document records the evidence and remediation history for Phase 7 model serving. The production baseline remains protected while candidate serving is debugged.

## Known-good baseline

Databricks Model Serving endpoint:

`dev_james_mashiyane_za_dev-netcare-readmission`

Active configuration:

- model: `netcareaidatabricks.default.readmission_model`
- version: `1`
- deployment state: `DEPLOYMENT_READY`
- traffic: 100%
- scale to zero: enabled

Version 1 is the known-good serving baseline and must remain untouched while candidate deployment is investigated.

## Candidate failures

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

The candidate deployment continued to fail during model-server loading. At this point the correct engineering action is to diagnose the artifact/runtime boundary rather than create another replacement candidate.

## Root-cause categories

The failures discovered so far fall into two categories:

1. **Artifact packaging:** application source was not included in the MLflow model artifact.
2. **Runtime compatibility:** the serving environment did not match the environment used to serialize the scikit-learn model.

The current registry implementation addresses runtime reproducibility by deriving serialization-sensitive package versions from the actual training environment when the artifact is created.

## Engineering rule

A failed candidate is not discarded merely because a new failure is discovered. The candidate remains the debugging target until the failure boundary is understood and the targeted fix is validated.

Only create a new model version when the model or training result intentionally changes.

## Validation sequence

```text
Known-good v1
    ↓
Freeze
    ↓
Diagnose candidate artifact
    ↓
Targeted fix
    ↓
Rebuild / redeploy candidate
    ↓
DEPLOYMENT_READY
    ↓
Direct inference
    ↓
FastAPI integration
```

## Current status

Phase 7 remains in progress. Training and model registration have been repeatedly validated. Version 1 serving remains healthy. Candidate serving is the active unresolved boundary.
