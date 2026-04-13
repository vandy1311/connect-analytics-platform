"""Supervisor tool — get_abandonment_analysis.

Returns abandonment metrics: abandonment rate, peak abandonment hour,
average wait time before abandonment, and total abandoned contacts.
Queries connect_ctr via Athena, wrapped in a circuit breaker.
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
    return _TIME_RANGE_MAP.get(time_range, "24")


def _build_abandonment_query(queue_name: str | None, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"initiation_timestamp >= current_timestamp - interval '{hours}' hour",
    ]
    if queue_name:
        where_clauses.append(f"queue_name = '{queue_name}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    COUNT(*) AS total_contacts,
    SUM(CASE WHEN outcome = 'ABANDONED' THEN 1 ELSE 0 END) AS total_abandoned,
    ROUND(
        100.0 * SUM(CASE WHEN outcome = 'ABANDONED' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS abandonment_rate,
    ROUND(
        AVG(
            CASE WHEN outcome = 'ABANDONED'
                 THEN queue_duration_seconds
                 ELSE NULL
            END
        ),
        2
    ) AS avg_wait_before_abandon
FROM connect_ctr
WHERE {where_sql}
"""


def _build_peak_hour_query(queue_name: str | None, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"initiation_timestamp >= current_timestamp - interval '{hours}' hour",
        "outcome = 'ABANDONED'",
    ]
    if queue_name:
        where_clauses.append(f"queue_name = '{queue_name}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    EXTRACT(HOUR FROM initiation_timestamp) AS abandon_hour,
    COUNT(*) AS abandon_count
FROM connect_ctr
WHERE {where_sql}
GROUP BY EXTRACT(HOUR FROM initiation_timestamp)
ORDER BY abandon_count DESC
LIMIT 1
"""


def handler(event, context):
    """Lambda entry point for get_abandonment_analysis."""
    tool_name = event.get("tool", "get_abandonment_analysis")
    params = event.get("parameters", {})

    queue_name = params.get("queue_name")
    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)

    try:
        # Run both queries through the circuit breaker
        agg_query = _build_abandonment_query(queue_name, time_range)
        agg_rows = _cb.call(execute_query, agg_query)

        peak_query = _build_peak_hour_query(queue_name, time_range)
        peak_rows = _cb.call(execute_query, peak_query)

        agg = agg_rows[0] if agg_rows else {}
        peak_hour = int(peak_rows[0]["abandon_hour"]) if peak_rows else None

        return {
            "tool": tool_name,
            "result": {
                "abandonment_rate": float(agg.get("abandonment_rate", 0)),
                "peak_abandonment_hour": peak_hour,
                "avg_wait_before_abandon": float(agg.get("avg_wait_before_abandon", 0)),
                "total_abandoned": int(agg.get("total_abandoned", 0)),
            },
        }

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
