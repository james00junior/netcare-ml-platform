"""Normalization helpers for verified Databricks serving telemetry.

This module is intentionally transport-agnostic. Authentication and SQL/API
execution remain outside the monitoring domain logic so the code cannot invent
workspace configuration or silently turn missing telemetry into observations.
"""

from typing import Any, Iterable, Mapping

ENDPOINT_USAGE_COLUMNS = (
    "request_time",
    "status_code",
    "requester",
    "databricks_request_id",
    "client_request_id",
    "served_entity_id",
)

SERVED_ENTITY_COLUMNS = (
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


def endpoint_usage_query(served_entity_id: str, limit: int = 100) -> str:
    """Build the verified endpoint_usage query without adding unverified fields."""
    if not served_entity_id:
        raise ValueError("served_entity_id must not be empty")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    escaped_id = served_entity_id.replace("'", "''")
    columns = ", ".join(ENDPOINT_USAGE_COLUMNS)
    return (
        f"SELECT {columns} FROM system.serving.endpoint_usage "
        f"WHERE served_entity_id = '{escaped_id}' "
        f"ORDER BY request_time DESC LIMIT {int(limit)}"
    )


def served_entities_query(served_entity_id: str) -> str:
    """Build the verified served_entities lookup query."""
    if not served_entity_id:
        raise ValueError("served_entity_id must not be empty")
    escaped_id = served_entity_id.replace("'", "''")
    columns = ", ".join(SERVED_ENTITY_COLUMNS)
    return (
        f"SELECT {columns} FROM system.serving.served_entities "
        f"WHERE served_entity_id = '{escaped_id}'"
    )


def normalize_endpoint_health(
    *,
    endpoint_state: str | None,
    config_update_state: str | None,
    deployment_state: str | None,
) -> dict[str, Any]:
    """Represent only explicitly observed endpoint state values."""
    ready = endpoint_state == "READY" if endpoint_state is not None else None
    updating = config_update_state == "UPDATING" if config_update_state is not None else None
    deployment_ready = (
        deployment_state == "DEPLOYMENT_READY" if deployment_state is not None else None
    )
    healthy = (
        ready and not updating and deployment_ready
        if None not in (ready, updating, deployment_ready)
        else None
    )
    return {
        "endpoint_state": endpoint_state,
        "config_update_state": config_update_state,
        "deployment_state": deployment_state,
        "ready": ready,
        "healthy": healthy,
    }


def normalize_endpoint_metrics(metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize only metrics actually supplied by the serving telemetry source.

    Missing metrics remain absent; they are never converted to zero.
    """
    known = (
        "cpu_usage_percentage",
        "mem_usage_percentage",
        "request_count_total",
        "request_4xx_count_total",
        "request_5xx_count_total",
        "request_latency_ms_count",
        "request_latency_ms_sum",
        "model_queue_time_ms_count",
        "model_queue_time_ms_sum",
        "provisioned_concurrent_requests_total",
    )
    return {name: metrics[name] for name in known if name in metrics}


def normalize_usage_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return request telemetry using the verified endpoint_usage contract."""
    normalized = []
    for row in rows:
        normalized.append({column: row.get(column) for column in ENDPOINT_USAGE_COLUMNS})
    return normalized


def resolve_served_entity(
    rows: Iterable[Mapping[str, Any]],
    served_entity_id: str,
) -> dict[str, Any] | None:
    """Resolve one served entity by its exact Databricks identifier."""
    for row in rows:
        if row.get("served_entity_id") == served_entity_id:
            return {column: row.get(column) for column in SERVED_ENTITY_COLUMNS}
    return None


def build_serving_observation(
    *,
    endpoint_name: str,
    served_entity_id: str,
    metrics: Mapping[str, Any],
    served_entity_rows: Iterable[Mapping[str, Any]],
    usage_rows: Iterable[Mapping[str, Any]],
    endpoint_state: str | None = None,
    config_update_state: str | None = None,
    deployment_state: str | None = None,
) -> dict[str, Any]:
    """Build a monitoring observation from already-observed source data.

    ``usage_records_available`` is based only on the supplied rows. An empty
    usage result is therefore represented explicitly rather than inferred as a
    successful request count.
    """
    usage = normalize_usage_rows(usage_rows)
    entity = resolve_served_entity(served_entity_rows, served_entity_id)

    return {
        "endpoint_name": endpoint_name,
        "served_entity_id": served_entity_id,
        "served_entity_found": entity is not None,
        "served_entity": entity,
        "health": normalize_endpoint_health(
            endpoint_state=endpoint_state,
            config_update_state=config_update_state,
            deployment_state=deployment_state,
        ),
        "metrics": normalize_endpoint_metrics(metrics),
        "usage_record_count": len(usage),
        "usage_records_available": bool(usage),
        "usage_records": usage,
    }
