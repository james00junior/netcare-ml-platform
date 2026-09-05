# Phase 7 — Serving Debugging Record

## Purpose

This document records the evidence and remediation history for Phase 7 model serving. The existing production baseline remains protected while the current candidate is validated through an isolated endpoint.

## Protected serving baseline

The existing production baseline is frozen and is not modified as part of the Phase 7 investigation.

## Current candidate: version 8

Registered model:

`netcareaidatabricks.default.readmission_model`

Version: `8`

Evidence:

- MLflow registration status: `READY`
- run ID: `bf12e7f602084e78acdab4797c40c2b2`
- model source: `models:/m-9fe9fb289f7546f0b0cf4e137422ccdb`
- Unity Catalog alias: `champion -> 8`

### Candidate serving endpoint

`dev_james_mashiyane_za_dev-netcare-readmission-candidate`

Verified endpoint configuration:

- model: `netcareaidatabricks.default.readmission_model`
- model version: `8`
- served entity: `readmission_model-8`
- traffic: 100%
- workload: Small / CPU
- scale to zero: enabled
- endpoint state: `READY`
- deployment state: `DEPLOYMENT_READY`
- deployment state message: `Scaled to zero`

`Scaled to zero` is an idle-state message, not a deployment failure. The important deployment result is `DEPLOYMENT_READY`.

## v8 model signature

The registered v8 model metadata was inspected without deserializing the sklearn estimator. The exact input contract is:

### Required inputs

```text
age: integer
sex: string
admission_type: string
admission_source: string
discharge_disposition: string
length_of_stay_days: integer
icu_hours: integer
num_prior_admissions_12m: integer
num_ed_visits_12m: integer
primary_diagnosis_group: string
secondary_diagnosis_count: integer
elixhauser_score: integer
wbc: double
has_diabetes: integer
has_hypertension: integer
has_ckd: integer
has_copd: integer
has_heart_failure: integer
num_medications: integer
had_surgery: integer
had_icu_stay: integer
discharge_to_home: integer
followup_booked: integer
payer_type: string
```

### Optional inputs

```text
creatinine: double
hemoglobin: double
sodium: double
potassium: double
```

### Outputs

```text
predicted_label: long
probability: double
risk_tier: string
model_version: string
```

No model parameters are declared in the signature.

## Local deserialization diagnostic

An attempt to load v8 locally on the Mac produced a dependency mismatch warning and then failed during scikit-learn object deserialization.

The v8 artifact declares:

```text
mlflow==3.16.0
pandas==3.0.5
numpy==1.26.4
scikit-learn==1.3.0
scipy==1.11.1
```

The local environment at the time of inspection had different versions, including scikit-learn `1.9.0`. The observed exception was:

```text
AttributeError: Can't get attribute '__pyx_unpickle_CyHalfBinomialLoss'
```

This local failure does not establish a serving failure. The authoritative serving endpoint for v8 is independently reporting `DEPLOYMENT_READY`.

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

The candidate deployment continued to fail during model-server loading. The engineering decision is now to diagnose candidates through the serving boundary rather than create replacement model versions for infrastructure failures.

## Root-cause categories discovered so far

1. **Artifact packaging:** application source was not initially included in the MLflow model artifact.
2. **Runtime compatibility:** the serving environment did not initially match the environment used to serialize the scikit-learn model.
3. **Local-versus-serving distinction:** a local `mlflow.pyfunc.load_model()` failure caused by environment mismatch must not be treated as evidence that the Databricks serving endpoint has failed.

The current registry implementation derives serialization-sensitive package versions from the actual training environment when the artifact is created.

## Engineering rule

A failed deployment candidate is not discarded merely because a new failure is discovered. The candidate remains the debugging target until the failure boundary is understood and the targeted fix is validated.

A new model version should only be created when the model or training result intentionally changes.

## Current Phase 7 position

The v8 serving boundary has now passed deployment validation:

```text
Registered v8
    ↓
Isolated candidate serving endpoint
    ↓
Model-server load
    ↓
DEPLOYMENT_READY
```

The next unresolved boundary is **direct inference against the v8 candidate endpoint**.

The next validation should use the exact model signature above and confirm the returned prediction contract:

```text
predicted_label
probability
risk_tier
model_version
```

## Validation sequence

```text
Freeze existing production baseline
    ↓
Validate registered v8
    ↓
Validate isolated v8 deployment
    ↓
DEPLOYMENT_READY
    ↓
Direct v8 inference
    ↓
Validate response contract
    ↓
FastAPI integration
    ↓
Serving/integration tests
```

## Current status

Phase 7 remains in progress.

**Validated:**

- v8 training
- v8 registration
- v8 model signature
- isolated v8 serving endpoint
- v8 deployment state: `DEPLOYMENT_READY`

**Next:**

- direct inference against the isolated v8 endpoint
- response-contract validation
- FastAPI integration
