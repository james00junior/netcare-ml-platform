-- Phase 5: Unity Catalog governance bootstrap
--
-- GCP / Databricks namespace:
--   nectare.bronze
--   nectare.silver
--   nectare.gold
--   nectare.ml
--
-- Run this with a Unity Catalog-enabled Databricks SQL warehouse or
-- Unity Catalog-compatible compute using an identity that has the required
-- catalog/schema privileges. Storage credentials and external locations are
-- intentionally deployment-specific and are not hard-coded here.

CREATE CATALOG IF NOT EXISTS nectare
COMMENT 'Netcare ML platform governed data and machine learning assets';

CREATE SCHEMA IF NOT EXISTS nectare.bronze
COMMENT 'Raw ingested hospital and source-system data';

CREATE SCHEMA IF NOT EXISTS nectare.silver
COMMENT 'Validated and standardised patient encounter data';

CREATE SCHEMA IF NOT EXISTS nectare.gold
COMMENT 'Analytics-ready features and business aggregates';

CREATE SCHEMA IF NOT EXISTS nectare.ml
COMMENT 'Machine learning feature tables and governed model assets';

-- Expected governed assets introduced by subsequent phases:
-- nectare.bronze.hospital_readmissions
-- nectare.silver.patient_encounters
-- nectare.gold.readmission_features
-- nectare.ml.readmission_features
-- nectare.ml.readmission_model

-- NOTE:
-- Production grants are deliberately managed separately from this bootstrap.
-- Do not grant broad privileges to individual users. Use Databricks groups and
-- least-privilege grants appropriate to the deployment environment.
