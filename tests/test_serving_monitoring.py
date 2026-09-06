"""Tests for verified Databricks serving monitoring contracts."""

from src.monitoring.serving import (
    ENDPOINT_USAGE_COLUMNS,
    build_serving_observation,
    normalize_endpoint_metrics,
    normalize_usage_rows,
    resolve_served_entity,
)


def test_usage_rows_use_verified_endpoint_usage_contract() -> None:
    rows = normalize_usage_rows(
        [
            {
                "request_time": "2026-09-06T16:00:00Z",
                "status_code": 200,
                "requester": "test",
                "databricks_request_id": "req-1",
                "client_request_id": "client-1",
                "served_entity_id": "entity-1",
                "unverified_column": "ignored",
            }
        ]
    )

    assert list(rows[0]) == list(ENDPOINT_USAGE_COLUMNS)
    assert rows[0]["status_code"] == 200
    assert "unverified_column" not in rows[0]


def test_zero_usage_rows_are_explicitly_unavailable() -> None:
    observation = build_serving_observation(
        endpoint_name="cidev-netcare-readmission-candidate",
        served_entity_id="entity-1",
        metrics={"request_count_total": 0},
        served_entity_rows=[],
        usage_rows=[],
    )

    assert observation["usage_record_count"] == 0
    assert observation["usage_records_available"] is False
    assert observation["usage_records"] == []


def test_served_entity_is_resolved_by_exact_id() -> None:
    rows = [
        {
            "served_entity_id": "entity-1",
            "endpoint_name": "cidev-netcare-readmission-candidate",
            "served_entity_name": "readmission_model-8",
            "entity_name": "netcareaidatabricks.default.readmission_model",
            "entity_version": 8,
            "endpoint_config_version": 1,
            "custom_model_config": '{"min_concurrency":"0"}',
            "change_time": "2026-09-06T16:00:44.803Z",
            "endpoint_delete_time": None,
        }
    ]

    result = resolve_served_entity(rows, "entity-1")

    assert result is not None
    assert result["entity_version"] == 8
    assert result["served_entity_name"] == "readmission_model-8"


def test_missing_serving_metrics_are_not_silently_zero() -> None:
    metrics = normalize_endpoint_metrics(
        {
            "cpu_usage_percentage": 2.34,
            "mem_usage_percentage": 6.82,
        }
    )

    assert metrics == {
        "cpu_usage_percentage": 2.34,
        "mem_usage_percentage": 6.82,
    }
    assert "request_count_total" not in metrics


def test_serving_observation_preserves_endpoint_and_model_identity() -> None:
    observation = build_serving_observation(
        endpoint_name="cidev-netcare-readmission-candidate",
        served_entity_id="entity-1",
        metrics={
            "cpu_usage_percentage": 2.34,
            "mem_usage_percentage": 6.82,
            "request_count_total": 0,
            "provisioned_concurrent_requests_total": 4,
        },
        served_entity_rows=[
            {
                "served_entity_id": "entity-1",
                "endpoint_name": "cidev-netcare-readmission-candidate",
                "served_entity_name": "readmission_model-8",
                "entity_name": "netcareaidatabricks.default.readmission_model",
                "entity_version": 8,
                "endpoint_config_version": 1,
                "custom_model_config": "{}",
                "change_time": "2026-09-06T16:00:44.803Z",
                "endpoint_delete_time": None,
            }
        ],
        usage_rows=[],
    )

    assert observation["served_entity_found"] is True
    assert observation["served_entity"]["entity_version"] == 8
    assert observation["metrics"]["provisioned_concurrent_requests_total"] == 4
