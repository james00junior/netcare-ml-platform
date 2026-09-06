"""Tests for the verified Phase 11 governed monitoring contract."""

import pytest

from src.monitoring.governed import (
    ENDPOINT_USAGE_TABLE,
    MONITORING_ENTITY_COLUMNS,
    MONITORING_USAGE_COLUMNS,
    monitoring_entity_query,
    monitoring_table_schema,
    monitoring_usage_query,
)


def test_usage_query_uses_only_verified_endpoint_usage_columns() -> None:
    query = monitoring_usage_query(
        served_entity_id="362c5dbb1cf448789afbb4ee6a687712",
        target_table="netcareaidatabricks.default.serving_usage",
    )

    assert ENDPOINT_USAGE_TABLE in query
    assert "`request_time`" in query
    assert "`status_code`" in query
    assert "`served_entity_id`" in query
    assert "probability" not in query
    assert "prediction" not in query


def test_usage_query_escapes_served_entity_id() -> None:
    query = monitoring_usage_query(
        served_entity_id="abc'def",
        target_table="netcareaidatabricks.default.serving_usage",
    )

    assert "'abc''def'" in query


def test_entity_query_uses_verified_entity_columns() -> None:
    query = monitoring_entity_query(
        served_entity_id="362c5dbb1cf448789afbb4ee6a687712",
        target_table="netcareaidatabricks.default.served_entities",
    )

    for column in MONITORING_ENTITY_COLUMNS:
        assert f"`{column}`" in query


def test_schema_is_deterministic_and_explicit() -> None:
    ddl = monitoring_table_schema(
        "netcareaidatabricks.default.serving_usage",
        MONITORING_USAGE_COLUMNS,
    )

    assert ddl.startswith("CREATE TABLE IF NOT EXISTS")
    assert "USING DELTA" in ddl
    assert "`status_code` INT" in ddl


def test_schema_rejects_unverified_columns() -> None:
    with pytest.raises(ValueError, match="Unsupported monitoring columns"):
        monitoring_table_schema(
            "netcareaidatabricks.default.serving_usage",
            (*MONITORING_USAGE_COLUMNS, "prediction_probability"),
        )


def test_monitoring_queries_reject_invalid_limits_and_identifiers() -> None:
    with pytest.raises(ValueError, match="positive"):
        monitoring_usage_query(
            served_entity_id="362c5dbb1cf448789afbb4ee6a687712",
            target_table="netcareaidatabricks.default.serving_usage",
            limit=0,
        )

    with pytest.raises(ValueError, match="unsupported characters"):
        monitoring_usage_query(
            served_entity_id="362c5dbb1cf448789afbb4ee6a687712",
            target_table="netcareaidabricks.default.bad-name",
        )
