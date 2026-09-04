# Unity Catalog Governance

## Phase 5

The Netcare ML platform uses Databricks Unity Catalog as the governance layer for data, features and machine-learning assets.

## Verified namespace

The target Databricks workspace currently exposes the managed catalog `netcareaidatabricks` with these verified schemas:

```text
netcareaidatabricks
├── default              # verified; auto-created by the workspace
└── information_schema   # verified; system-managed
```

Phase 6 model registration therefore uses the existing application schema:

```text
netcareaidatabricks.default.readmission_model
```

**Important:** `ml` is not a schema in the current target workspace and must not be referenced by the platform configuration, bootstrap SQL, tests, or documentation.

## Responsibilities

### default

Current application namespace used for the Phase 6 registered model. Model registration must target the schema that actually exists in the deployment environment rather than assuming a conventional `ml` schema.

### information_schema

System-managed metadata schema. It is not an application namespace and must not be used for model registration.

### bronze / silver / gold

These are planned data-layer namespaces created by the platform bootstrap when required by later data-engineering phases. They are separate from the currently verified Phase 6 model-registration namespace.

## Governance principles

- Use Unity Catalog three-part names for governed assets.
- Verify catalog and schema existence in the target environment before referencing them in application code.
- Use Databricks groups rather than individual-user grants.
- Apply least privilege by environment and role.
- Keep production data access separate from development access.
- Do not hard-code GCP credentials, Databricks tokens or storage credentials.
- External GCS storage locations are deployment configuration and are not embedded in repository SQL.
- Keep lineage enabled through Unity Catalog-managed tables and model workflows.
- Avoid logging patient-identifying or raw clinical input data in MLflow.

## Model governance

Models are governed through the MLflow lifecycle described in Phase 6. The current target namespace is:

```text
netcareaidatabricks.default.readmission_model
```

The `champion` alias is assigned only after the quality gate passes.

## Deployment

`databricks/sql/00_unity_catalog.sql` creates only the application data schemas required by the platform and does not create or assume an `ml` schema. Phase 6 registration uses the verified `default` schema. `databricks/sql/01_unity_catalog_grants.sql` contains a least-privilege grant template aligned with that verified namespace.
