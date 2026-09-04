-- Phase 5: Unity Catalog schema bootstrap
--
-- The Databricks workspace already provides the managed catalog:
--   netcareaidatabricks
--
-- This script deliberately does NOT create the catalog. Catalog provisioning
-- is an environment-level administration concern. The script creates the
-- application schemas required by the platform inside the verified catalog.

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.bronze
COMMENT 'Raw ingested hospital and source-system data';

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.silver
COMMENT 'Validated and standardised patient encounter data';

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.gold
COMMENT 'Analytics-ready features and business aggregates';

CREATE SCHEMA IF NOT EXISTS netcareaidatabricks.ml
COMMENT 'Machine learning feature tables and governed model assets';

-- Expected governed assets introduced by subsequent phases:
-- netcareaidatabricks.bronze.hospital_readmissions
-- netcareaidatabricks.silver.patient_encounters
-- netcareaidatabricks.gold.readmission_features
-- netcareaidatabricks.ml.readmission_features
-- netcareaidatabricks.ml.readmission_model

-- NOTE:
-- Production grants are deliberately managed separately from this bootstrap.
-- Do not grant broad privileges to individual users. Use Databricks groups and
-- least-privilege grants appropriate to the deployment environment.
