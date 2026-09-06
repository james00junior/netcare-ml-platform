# Build and Runtime Versions

This file records versions verified from the GitHub Actions CI environment. It is intentionally limited to versions observed in CI; unverified versions are not recorded as facts.

## Verified CI baseline

| Component | Verified version |
|---|---:|
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
| MLflow | 3.16.0 |
| Databricks SDK | 0.135.0 |
| Pydantic | 2.13.5 |
| FastAPI | 0.141.1 |
| httpx | 0.28.1 |
| project | 0.1.0 |

## CI and deployment conventions

- GitHub Actions uses CPython 3.11.16 for the verified CI run.
- Black and Ruff are pinned in `pyproject.toml` to the versions verified by CI.
- Databricks authentication in deployment workflows uses GitHub OIDC with `DATABRICKS_AUTH_TYPE=github-oidc`.
- The Databricks bundle uses the environment-provided `DATABRICKS_HOST` variable for dev, staging, and production targets.
- Databricks CLI is installed by the deployment workflow using `databricks/setup-cli@main`; its resolved version is not recorded here because the current workflow log did not expose a CLI version.

## Dependency locking status

There is currently no `uv.lock` file in the repository. Direct dependencies that require exact reproducibility are pinned in `pyproject.toml`, but transitive dependencies are not fully lock-pinned. The project must not be described as fully dependency-reproducible until a lock file is added and committed.

## Model-serving baseline

- Databricks Model Serving: Serving v2 baseline.
- Unity Catalog registered model: `netcareaidatabricks.default.readmission_model`.
- Validated candidate model version: `8`.
- The serving baseline is frozen while later lifecycle phases are implemented.

## Change-control rule

When CI or deployment dependencies change, update this record from observed CI/deployment output rather than guessing a version. Keep the code, workflow configuration, and this document aligned.
