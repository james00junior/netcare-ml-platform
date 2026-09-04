# Unity Catalog Governance

## Phase 5

The Netcare ML platform uses Databricks Unity Catalog as the governance layer for data, features and machine-learning assets.

## Namespace

```text
nectare
├── bronze
├── silver
├── gold
└── ml
```

Canonical assets:

```text
nectare.bronze.hospital_readmissions
nectare.silver.patient_encounters
nectare.gold.readmission_features
nectare.ml.readmission_features
nectare.ml.readmission_model
```

## Responsibilities

### Bronze
Raw source data. Access is restricted to ingestion/data-engineering identities.

### Silver
Validated, standardised and quality-checked encounter data. Downstream consumers should not need direct access to Bronze.

### Gold
Analytics-ready datasets and model-ready feature inputs.

### ML
Governed machine-learning feature tables and model assets. Model lifecycle controls are implemented in the MLflow/model-registry layer.

## Governance principles

- Use Unity Catalog three-part names for governed assets.
- Use Databricks groups rather than individual-user grants.
- Apply least privilege by environment and role.
- Keep production data access separate from development access.
- Do not hard-code GCP credentials, Databricks tokens or storage credentials.
- External GCS storage locations are deployment configuration and are not embedded in repository SQL.
- Keep lineage enabled through Unity Catalog-managed tables and model workflows.
- Avoid logging patient-identifying or raw clinical input data in MLflow.

## Feature tables

Feature engineering in later phases should publish stable, versioned feature tables under `nectare.ml`. Gold remains the analytics layer; ML contains machine-learning-specific feature assets and training/serving contracts.

## Model governance

Models are governed through the MLflow lifecycle described in Phase 6. The Unity Catalog `ml` schema is the target namespace for governed model assets where the Databricks deployment supports Unity Catalog model registration.

## Deployment

`databricks/sql/00_unity_catalog.sql` creates the catalog and schemas. `databricks/sql/01_unity_catalog_grants.sql` contains a least-privilege grant template whose group names must be mapped to the real Databricks groups at deployment time.
