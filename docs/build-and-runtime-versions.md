# Build and Runtime Versions

This file is the repository's version/configuration record for the production ML platform. Versions listed below are recorded from observed GitHub Actions output or directly from repository-declared configuration. They are not estimates.

## CI runtime — observed

| Component | Version |
|---|---:|
| Runner OS | Ubuntu 24.04.4 LTS |
| Runner image | ubuntu-24.04 / 20260831.293.1 |
| Python | 3.11.16 |
| pip | 26.2.1 |
| Black | 26.5.1 |
| Ruff | 0.16.6 |
| pytest | 9.1.1 |
| pytest-cov | 7.1.0 |
| mypy | 2.3.1 |
| pandas | 3.0.5 |
| NumPy | 1.26.4 |
| scikit-learn | 1.3.0 |
| SciPy | 1.11.1 |
| XGBoost | 3.2.0 |
| MLflow | 3.16.0 |
| Databricks SDK | 0.135.0 |
| Pydantic | 2.13.5 |
| pydantic-settings | 2.15.0 |
| FastAPI | 0.141.1 |
| httpx | 0.28.1 |
| uvicorn | 0.52.4 |
| python-multipart | 0.0.32 |
| python-dotenv | 1.2.3 |
| PyYAML | 6.0.3 |
| joblib | 1.6.0 |
| matplotlib | 3.11.1 |
| cloudpickle | 3.1.2 |

## Repository-declared direct dependencies

The direct dependencies in `pyproject.toml` are pinned to the versions observed in the Phase 10 CI environment. Monitoring dependencies remain range-constrained because their current CI versions have not been observed.

## GitHub Actions configuration

The CI workflow explicitly uses Python `3.11.16` and records Python, pip, Black, Ruff, and pytest versions during execution.

Deployment workflows use the same Python `3.11.16` runtime and the same pinned package set from `pyproject.toml`.

GitHub Actions deployment authentication is configured as:

```text
DATABRICKS_AUTH_TYPE=github-oidc
DATABRICKS_HOST=${{ vars.DATABRICKS_HOST }}
DATABRICKS_CLIENT_ID=${{ vars.DATABRICKS_CLIENT_ID }}
```

The workflows request:

```yaml
permissions:
  id-token: write
  contents: read
```

The Databricks CLI setup action's current `VERSION` file was inspected directly and contains `1.15.0`. Deployment workflows therefore pass `version: "1.15.0"` explicitly and record the installed CLI version during deployment.

## Databricks Bundle configuration

All three bundle targets — `dev`, `staging`, and `prod` — use the same environment variable name:

```text
DATABRICKS_HOST
```

The configured catalog is:

```text
netcareaidatabricks
```

The registered model is:

```text
netcareaidatabricks.default.readmission_model
```

The protected serving model version is configured as `1` and the isolated candidate version as `8`.

## Model-serving baseline

The validated Phase 8/9 serving baseline is:

- Databricks Model Serving: Serving v2
- Unity Catalog model: `netcareaidatabricks.default.readmission_model`
- validated candidate model version: `8`
- MLflow run: `bf12e7f602084e78acdab4797c40c2b2`

Phase 8 and Phase 9 remain frozen while Phase 10 security hardening proceeds.

## Dependency locking status

There is currently **no `uv.lock` file** in the repository. The direct dependencies are version-pinned, but the complete transitive dependency graph is not lock-pinned. This repository must therefore be described as **direct-dependency version-pinned, not fully lockfile-reproducible**.

A future dependency-locking change must add and commit the lock file only after it has been generated and validated in the project environment.

## Change-control rule

When changing a runtime, dependency, GitHub Action, Databricks CLI, or deployment configuration:

1. verify the version/configuration from the actual CI or deployment environment;
2. update this record;
3. update the corresponding source configuration;
4. run CI;
5. do not describe an unobserved value as verified.
