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

Phase 1–9 implementations are frozen. Candidate development must not modify the protected v1 endpoint or silently change the serving/version configuration.

## Latest repository quality checkpoint

The latest monitoring-code checkpoint is:

```text
Commit: cc47b912efd86353f93c2115945e74cb348faa91
Message: Fix monitoring exports lint ordering
```

For this exact commit:

```text
GitHub Actions CI: PASS
GitHub Actions Deploy Dev: PASS
```

The successful CI run completed lint, format checking, tests, and Codecov steps. The successful Deploy Dev run completed tests, Databricks CLI setup, bundle validation, and bundle deployment.

**Rule:** never use the status of a different commit to declare the current commit green.

## Monitoring evidence checkpoint — 2026-09-06

Verified live candidate identity:

```text
Endpoint:                 cidev-netcare-readmission-candidate
Served entity:            readmission_model-8
Registry model:           netcareaidatabricks.default.readmission_model
Registry version:         8
Served entity ID:         362c5dbb1cf448789afbb4ee6a687712
Endpoint config version:  1
Endpoint state:            READY
Config update state:       NOT_UPDATING
Deployment state:          DEPLOYMENT_READY
Workload:                  Small / CPU
Scale to zero:             enabled
```

Verified serving system-table surfaces:

```text
system.serving.endpoint_usage
system.serving.served_entities
```

The exact v8 `served_entity_id` query against `system.serving.endpoint_usage` succeeded but returned zero rows. Therefore:

- system-table access is verified;
- the exact v8 served entity is verified;
- v8 request-record population is **not** verified;
- no inference-record source or schema is assumed beyond the observed system-table schema.

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

## Next approved Phase 11 sequence

The next work is not another CI/debugging loop. The repository is green at the latest verified commit. Continue Phase 11 in this order:

```text
11.2  Establish governed monitoring data
11.3  Implement health and data-quality checks
11.4  Implement prediction and drift monitoring
11.5  Implement labelled-outcome evaluation
11.6  Add alerts and operational dashboard
```

Each step requires evidence and a checkpoint before the next step begins.
