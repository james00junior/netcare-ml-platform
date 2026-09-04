-- Phase 5: Unity Catalog schema bootstrap
--
-- The Databricks workspace already provides the managed catalog:
--   netcareaidatabricks
--
-- The verified application namespace currently available in this workspace is
-- the auto-created `default` schema. Do not invent or assume additional schemas.
-- Catalog/schema provisioning must be based on the actual target environment.

-- The following application schemas are optional future data-layer namespaces.
-- They are deliberately not required by Phase 6 model registration.
CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.bronze
COMMENT 'Raw ingested hospital and source-system data';

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.silver
COMMENT 'Validated and standardised patient encounter data';

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.gold
COMMENT 'Analytics-ready features and business aggregates';

-- Phase 6 model registry uses the existing managed default schema:
-- netcareaidatabricks.default.readmission_model

-- Expected governed assets introduced by subsequent phases:
-- netcareaidatabricks.bronze.hospital_readmissions
-- netcareaidatabricks.silver.patient_encounters
-- netcareaidatabricks.gold.readmission_features
-- netcareaidatabricks.default.readmission_model

-- NOTE:
-- Production grants are deliberately managed separately from this bootstrap.
-- Do not grant broad privileges to individual users. Use Databricks groups and
-- least-privilege grants appropriate to the deployment environment.
