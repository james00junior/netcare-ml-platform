"""Governed serving-monitoring data contracts and SQL builders.

The SQL in this module uses only serving system-table columns verified in the
workspace. Execution is intentionally left to the Databricks notebook/job so
this package remains transport-agnostic and testable locally.
"""

from __future__ import annotations

from collections.abc import Iterable

ENDPOINT_USAGE_TABLE = "system.serving.endpoint_usage"
SERVED_ENTITIES_TABLE = "system.serving.served_entities"

MONITORING_USAGE_COLUMNS = (
    "request_time",
    "status_code",
    "requester",
    "databricks_request_id",
    "client_request_id",
    "served_entity_id",
)

MONITORING_ENTITY_COLUMNS = (
    "served_entity_id",
    "endpoint_name",
    "served_entity_name",
    "entity_name",
    "entity_version",
    "endpoint_config_version",
    "custom_model_config",
    "change_time",
    "endpoint_delete_time",
)


def _quote_identifier(value: str) -> str:
    """Quote a SQL identifier after rejecting unsafe qualified names."""
    if not value or any(part == "" for part in value.split(".")):
        raise ValueError("SQL identifier must be non-empty and dot-qualified")
    if any(not part.replace("_", "").isalnum() for part in value.split(".")):
        raise ValueError("SQL identifier contains unsupported characters")
    return ".".join(f"`{part}`" for part in value.split("."))


def _quote_string(value: str) -> str:
    if not value:
        raise ValueError("Value must be non-empty")
    return "'" + value.replace("'", "''") + "'"


def monitoring_usage_query(
    *,
    served_entity_id: str,
    target_table: str,
    limit: int = 10000,
) -> str:
    """Build the governed usage extraction query from verified source columns."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    target = _quote_identifier(target_table)
    source = ENDPOINT_USAGE_TABLE
    entity = _quote_string(served_entity_id)
    columns = ",\n    ".join(f"`{column}`" for column in MONITORING_USAGE_COLUMNS)
    return (
        f"INSERT INTO {target} ({columns})\n"
        f"SELECT {columns}\n"
        f"FROM {source}\n"
        f"WHERE `served_entity_id` = {entity}\n"
        f"ORDER BY `request_time` DESC\n"
        f"LIMIT {limit}"
    )


def monitoring_entity_query(*, served_entity_id: str, target_table: str) -> str:
    """Build the governed served-entity metadata extraction query."""
    target = _quote_identifier(target_table)
    source = SERVED_ENTITIES_TABLE
    entity = _quote_string(served_entity_id)
    columns = ",\n    ".join(f"`{column}`" for column in MONITORING_ENTITY_COLUMNS)
    return (
        f"INSERT INTO {target} ({columns})\n"
        f"SELECT {columns}\n"
        f"FROM {source}\n"
        f"WHERE `served_entity_id` = {entity}"
    )


def monitoring_table_schema(table_name: str, columns: Iterable[str]) -> str:
    """Build a deterministic Delta table DDL for explicitly approved columns."""
    table = _quote_identifier(table_name)
    column_types = {
        "request_time": "TIMESTAMP",
        "status_code": "INT",
        "requester": "STRING",
        "databricks_request_id": "STRING",
        "client_request_id": "STRING",
        "served_entity_id": "STRING",
        "endpoint_name": "STRING",
        "served_entity_name": "STRING",
        "entity_name": "STRING",
        "entity_version": "INT",
        "endpoint_config_version": "INT",
        "custom_model_config": "STRING",
        "change_time": "TIMESTAMP",
        "endpoint_delete_time": "TIMESTAMP",
    }
    selected = tuple(columns)
    if not selected:
        raise ValueError("At least one column is required")
    unknown = tuple(column for column in selected if column not in column_types)
    if unknown:
        raise ValueError(f"Unsupported monitoring columns: {unknown}")
    definitions = ",\n    ".join(f"`{column}` {column_types[column]}" for column in selected)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    {definitions}\n) USING DELTA"
