"""Supervisor tool — get_queue_health.

Returns queue health metrics: queue size, longest wait, service level %,
and average handle time.  Queries both connect_ctr and connect_agent_events
via Athena, wrapped in a circuit breaker.
"""


from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "24h"

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
    """Convert a human time-range token to hours for the SQL interval."""
    return _TIME_RANGE_MAP.get(time_range, "24")


def _build_query(queue_name: str | None, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"c.initiation_timestamp >= current_timestamp - interval '{hours}' hour",
    ]
    if queue_name:
        where_clauses.append(f"c.queue_name = '{queue_name}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    c.queue_name,
    COUNT(*) AS queue_size,
    MAX(c.queue_duration_seconds) AS longest_wait_seconds,
    ROUND(
        100.0 * SUM(CASE WHEN c.service_level_met = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS service_level_pct,
    ROUND(AVG(c.handle_time_seconds), 2) AS avg_handle_time
FROM connect_ctr c
WHERE {where_sql}
GROUP BY c.queue_name
ORDER BY service_level_pct ASC
"""


def handler(event, context):
    """Lambda entry point for get_queue_health."""
    tool_name = event.get("tool", "get_queue_health")
    params = event.get("parameters", {})

    queue_name = params.get("queue_name")
    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)

    try:
        query = _build_query(queue_name, time_range)
        rows = _cb.call(execute_query, query)

        if not rows:
            return {
                "tool": tool_name,
                "result": {
                    "queue_name": queue_name or "ALL",
                    "queue_size": 0,
                    "longest_wait_seconds": 0,
                    "service_level_pct": 100.0,
                    "avg_handle_time": 0.0,
                },
            }

        # If a specific queue was requested, return the single row
        if queue_name:
            row = rows[0]
            return {
                "tool": tool_name,
                "result": {
                    "queue_name": row.get("queue_name", queue_name),
                    "queue_size": int(row.get("queue_size", 0)),
                    "longest_wait_seconds": int(row.get("longest_wait_seconds", 0)),
                    "service_level_pct": float(row.get("service_level_pct", 0)),
                    "avg_handle_time": float(row.get("avg_handle_time", 0)),
                },
            }

        # Multiple queues — return a list
        results = []
        for row in rows:
            results.append({
                "queue_name": row.get("queue_name", ""),
                "queue_size": int(row.get("queue_size", 0)),
                "longest_wait_seconds": int(row.get("longest_wait_seconds", 0)),
                "service_level_pct": float(row.get("service_level_pct", 0)),
                "avg_handle_time": float(row.get("avg_handle_time", 0)),
            })

        return {"tool": tool_name, "result": results}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
