"""Supervisor tool — get_agent_utilization.

Returns per-agent utilization metrics: occupancy rate, current status,
average handle time, and contacts handled.
Queries connect_agent_events via Athena, wrapped in a circuit breaker.
"""

from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "24h"

_VALID_STATES = {"AVAILABLE", "ON_CALL", "AFTER_CONTACT_WORK", "OFFLINE"}

_TIME_RANGE_MAP = {
    "1h": "1",
    "4h": "4",
    "8h": "8",
    "12h": "12",
    "24h": "24",
    "48h": "48",
    "7d": "168",
    "30d": "720",
}


def _hours_from_range(time_range: str) -> str:
    return _TIME_RANGE_MAP.get(time_range, "24")


def _build_query(agent_id: str | None, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"state_start_timestamp >= current_timestamp - interval '{hours}' hour",
    ]
    if agent_id:
        where_clauses.append(f"agent_id = '{agent_id}'")

    where_sql = " AND ".join(where_clauses)

    # Use a subquery to get the latest state per agent and aggregate metrics.
    return f"""
WITH latest_state AS (
    SELECT
        agent_id,
        current_state,
        ROW_NUMBER() OVER (
            PARTITION BY agent_id
            ORDER BY state_start_timestamp DESC
        ) AS rn
    FROM connect_agent_events
    WHERE {where_sql}
),
agent_metrics AS (
    SELECT
        agent_id,
        ROUND(AVG(occupancy_rate), 4) AS occupancy_rate,
        MAX(contacts_handled_today) AS contacts_handled,
        ROUND(AVG(state_duration_seconds), 2) AS avg_handle_time
    FROM connect_agent_events
    WHERE {where_sql}
    GROUP BY agent_id
)
SELECT
    m.agent_id,
    m.occupancy_rate,
    ls.current_state AS current_status,
    m.avg_handle_time,
    m.contacts_handled
FROM agent_metrics m
JOIN latest_state ls
    ON m.agent_id = ls.agent_id AND ls.rn = 1
ORDER BY m.occupancy_rate DESC
"""


def _clamp_occupancy(value: float) -> float:
    """Ensure occupancy_rate stays within [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def _normalize_status(status: str) -> str:
    """Normalize status to one of the valid states."""
    upper = status.upper().strip()
    return upper if upper in _VALID_STATES else "OFFLINE"


def handler(event, context):
    """Lambda entry point for get_agent_utilization."""
    tool_name = event.get("tool", "get_agent_utilization")
    params = event.get("parameters", {})

    agent_id = params.get("agent_id")
    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)

    try:
        query = _build_query(agent_id, time_range)
        rows = _cb.call(execute_query, query)

        agents = []
        for row in rows:
            agents.append({
                "agent_id": row.get("agent_id", ""),
                "occupancy_rate": _clamp_occupancy(
                    float(row.get("occupancy_rate", 0))
                ),
                "current_status": _normalize_status(
                    row.get("current_status", "OFFLINE")
                ),
                "avg_handle_time": float(row.get("avg_handle_time", 0)),
                "contacts_handled": int(row.get("contacts_handled", 0)),
            })

        return {"tool": tool_name, "result": {"agents": agents}}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
