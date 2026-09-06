# Verification and Change-Control Record

This document is the operational guardrail for the Netcare ML Platform. It exists to prevent repeated debugging loops, stale assumptions, and configuration drift.

## Source-of-truth hierarchy

When evidence conflicts, use this order:

1. **Live Databricks state** for deployed resources, serving state, model versions, telemetry, and system-table contents.
2. **GitHub `main`** for application code, bundle configuration, workflows, documentation, and committed version records.
3. **GitHub Actions results for the exact commit SHA** for CI/deployment verification.
4. Local command output supplied from the current checkout.
5. Memory, previous output, or assumptions are **not** verification evidence.

A value is only called **verified** when the source and exact version/commit are identified.

## Protected baseline

The following serving resources are frozen unless an explicit change is required and independently validated:

```text
Protected endpoint: cidev-netcare-readmission
Protected served model: readmission_model-1
Protected registered model version: 1

Candidate endpoint: cidev-netcare-readmission-candidate
Candidate served model: readmission_model-8
Candidate registered model version: 8
MLflow run: bf12e7f602084e78acdab4797c40c2b2
```

Phases 1–11 are frozen for their validated scopes. Candidate development must not modify the protected v1 endpoint or silently change the serving/version configuration.

## Phase 11 completion checkpoint — 2026-09-06

Live Databricks evidence supplied for this checkpoint:

```text
Protected endpoint: cidev-netcare-readmission
  served model: readmission_model-1
  registered version: 1
  state: READY
  config update: NOT_UPDATING
  deployment: DEPLOYMENT_READY
  traffic: 100%
  usage tracking: enabled

Candidate endpoint: cidev-netcare-readmission-candidate
  served model: readmission_model-8
  registered version: 8
  served entity ID: 362c5dbb1cf448789afbb4ee6a687712
  state: READY
  config update: NOT_UPDATING
  deployment: DEPLOYMENT_READY
  traffic: 100% within candidate endpoint
  usage tracking: enabled
```

The governed query against `system.serving.endpoint_usage` succeeded with schema:

```text
request_time
status_code
requester
databricks_request_id
client_request_id
served_entity_id
```

For the exact v8 served entity ID `362c5dbb1cf448789afbb4ee6a687712`, the query returned:

```text
status: SUCCEEDED
total_row_count: 0
total_chunk_count: 0
truncated: false
```

Therefore:

- serving telemetry is verified;
- serving system-table access is verified;
- the v8 served-entity identity is verified;
- v8 request-record population is **not** observed;
- prediction/probability fields are not inferred from the usage table;
- labelled outcomes are not inferred from serving telemetry.

The repository monitoring contracts are implemented and tested for the evidence boundary, including serving health, governed serving queries, missing-metric preservation, data quality, drift, and labelled-performance calculations.

**Phase 11 status: COMPLETE / FROZEN FOR VERIFIED MONITORING SCOPE.**

This completion does not claim a live prediction-record pipeline, labelled-outcome source, production alert configuration, or production dashboard deployment where those were not evidenced.

## Latest repository quality checkpoint before Phase 11 documentation close

```text
Commit: 2f8caa30f59d5c3e9036baf20b37b6a5c16ed5fc
Message: Fix governed monitoring source table qualification

GitHub Actions CI: PASS
GitHub Actions Deploy Dev: PASS
```

The exact commit passed the repository lint, format, test, and deployment workflow stages. Phase 11 documentation changes are documentation-only checkpoint updates following that verified implementation checkpoint.

## Change procedure

For every non-trivial implementation or configuration change:

1. **Inspect current state.** Fetch the exact file/configuration and identify the current commit SHA.
2. **State the evidence.** Record the exact observed value, endpoint, model version, or workflow run before changing anything.
3. **Make one targeted change.** Do not mix unrelated refactors, dependency upgrades, infrastructure changes, and monitoring work.
4. **Run repository quality checks.** At minimum, run the same lint, format, and test commands used by CI.
5. **Push/commit the change.** Record the resulting commit SHA.
6. **Verify CI for that exact SHA.** Do not infer success from an earlier or later run.
7. **Verify deployment for that exact SHA** when the change affects deployable resources.
8. **Inspect live Databricks state** when the change affects serving, bundles, jobs, permissions, telemetry, or system tables.
9. **Update this record and the relevant documentation** with only observed evidence.
10. **Freeze the verified checkpoint** before moving to the next step.

## Failure handling

If CI fails:

- inspect the failing job and exact failed step;
- fix only the demonstrated failure;
- rerun/verify the exact affected commit;
- do not change Databricks serving resources unless the failure is proven to be a deployment/configuration problem.

If deployment fails:

- inspect the exact deployment job and failure message;
- compare the repository configuration with the live Databricks state;
- do not modify the protected serving baseline unless the evidence requires it.

If live telemetry is empty:

- record it as **empty/unobserved**, not zero-capability;
- do not fabricate request records, inference tables, or metrics;
- use another source only after that source is independently verified.

## No-guessing rule

The following statements are prohibited unless directly evidenced:

- a model version not observed in registry/serving state;
- an endpoint configuration not returned by Databricks;
- an inference table that has not been queried and identified;
- populated usage records when the verified query returns zero rows;
- permissions that have not been inspected;
- a successful deployment attributed to a different commit;
- a runtime/dependency version not observed in CI or declared configuration.

## Documentation rule

After each verified milestone, update:

- `README.md` — concise current status and architecture;
- `docs/production-roadmap.md` — lifecycle milestone and exit criteria;
- the relevant phase document — detailed evidence and implementation state;
- `docs/build-and-runtime-versions.md` — only when versions/configuration change;
- this file — exact checkpoint, evidence, and change-control notes.

Documentation must distinguish **implemented**, **queryable**, **observed**, **validated**, and **complete**. These terms are not interchangeable.

## Next lifecycle phase

Phase 11 is frozen for the verified monitoring scope. The next active work is Phase 12:

```text
Phase 12 — Drift + Retraining
```

Phase 12 must first inspect the actual Databricks training/retraining job and verified data source before adding orchestration. It must consume validated monitoring signals rather than inventing a new monitoring path.
