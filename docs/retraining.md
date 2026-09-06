# Phase 12 — Drift + Retraining

## Purpose

Phase 12 demonstrates the drift-to-retraining control loop for this project using deterministic synthetic data. No production claim is made: the live Phase 11 serving usage table was verified with zero request rows, so there is no real prediction stream available for drift evaluation.

## Synthetic validation design

The repository creates two reproducible populations:

- `make_reference_dataset()` — 500 reference observations using the project readmission feature types.
- `make_shifted_dataset()` — 500 observations with deliberate shifts in numeric distributions and categorical proportions.

The test suite runs the existing `detect_data_drift()` implementation against both populations and verifies that the unchanged population is not flagged while the shifted population is flagged.

## Retraining decision

`RetrainingPolicy` requires an explicit minimum observation count and at least one retraining signal. `should_retrain()` consumes the drift/performance reports produced by the monitoring layer and returns both the decision and auditable reasons.

The Phase 12 tests therefore demonstrate:

```text
synthetic reference data
        |
        v
synthetic current data with controlled shift
        |
        v
existing drift detector
        |
        +---- no drift ----> do not retrain
        |
        +---- drift --------> retraining requested
                              (after minimum observations)
```

## What this phase does not claim

This project does not claim an automated production retraining trigger. The existing Databricks bundle contains the validated training workflow, but no production drift-data source or scheduled retraining trigger has been evidenced. Phase 12 therefore validates the decision and test path with synthetic data rather than fabricating live telemetry or a production schedule.

The existing training notebook remains the retraining execution path: it loads the governed raw dataset, validates it, trains the baseline/GBDT candidates, applies the existing quality gate, and registers/promotes the approved candidate. fileciteturn222file0

## Frozen boundary

The Phase 12 synthetic test does not modify:

- protected endpoint `cidev-netcare-readmission`;
- protected model version `1`;
- candidate endpoint `cidev-netcare-readmission-candidate`;
- candidate model version `8`.

Those serving resources remain frozen from Phase 11.
