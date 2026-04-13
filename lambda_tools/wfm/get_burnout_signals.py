"""WFM tool — get_burnout_signals.

Analyzes agent event data for burnout patterns: sustained high occupancy,
extended ACW durations, and increasing handle times.  Calculates a burnout
score (0.0–1.0) per agent and publishes BURNOUT_RISK events for agents
exceeding the critical threshold.
"""

import os

from lambda_tools.shared.alert_publisher import publish_alert
from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "7d"
_BURNOUT_CRITICAL_THRESHOLD = float(
    os.environ.get("BURNOUT_CRITICAL_THRESHOLD", "0.85")
)

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
    return _TIME_RANGE_MAP.get(time_range, "168")


def _build_query(time_range: str) -> str:
    hours = _hours_from_range(time_range)

    return f"""
SELECT
    agent_id,
    ROUND(AVG(occupancy_rate), 4) AS avg_occupancy,
    ROUND(AVG(
        CASE WHEN current_state = 'AFTER_CONTACT_WORK'
             THEN state_duration_seconds
             ELSE NULL
        END
    ), 2) AS avg_acw_duration,
    ROUND(AVG(state_duration_seconds), 2) AS avg_state_duration,
    COUNT(*) AS event_count
FROM connect_agent_events
WHERE state_start_timestamp >= current_timestamp - interval '{hours}' hour
GROUP BY agent_id
HAVING COUNT(*) >= 5
ORDER BY AVG(occupancy_rate) DESC
"""


def _build_trend_query(agent_id: str, time_range: str) -> str:
    """Query to detect increasing handle times over time for a specific agent."""
    hours = _hours_from_range(time_range)

    return f"""
SELECT
    CAST(state_start_timestamp AS DATE) AS event_date,
    ROUND(AVG(state_duration_seconds), 2) AS avg_duration
FROM connect_agent_events
WHERE agent_id = '{agent_id}'
  AND current_state = 'ON_CALL'
  AND state_start_timestamp >= current_timestamp - interval '{hours}' hour
GROUP BY CAST(state_start_timestamp AS DATE)
ORDER BY event_date ASC
"""


def _calculate_handle_time_trend(trend_rows: list[dict]) -> float:
    """Calculate handle time trend as a normalized slope.

    Returns a value in [0.0, 1.0] where higher means increasing handle times.
    """
    if len(trend_rows) < 2:
        return 0.0

    durations = [float(r.get("avg_duration", 0)) for r in trend_rows]
    n = len(durations)
    x_mean = (n - 1) / 2.0
    y_mean = sum(durations) / n

    numerator = sum((i - x_mean) * (d - y_mean) for i, d in enumerate(durations))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0

    slope = numerator / denominator
    # Normalize: positive slope → higher score, cap at 1.0
    normalized = min(1.0, max(0.0, slope / max(abs(y_mean), 1.0)))
    return round(normalized, 4)


def _calculate_burnout_score(
    occupancy_rate: float,
    handle_time_trend: float,
    avg_acw_duration: float,
) -> float:
    """Calculate burnout score (0.0–1.0).

    Formula: 0.4 * occupancy_factor + 0.3 * handle_time_trend + 0.3 * acw_factor

    - occupancy_factor: occupancy_rate clamped to [0, 1]
    - handle_time_trend: already in [0, 1]
    - acw_factor: normalized ACW duration (higher ACW → higher burnout signal)
      Normalized against a 300s baseline (5 min avg ACW is considered high).
    """
    occupancy_factor = max(0.0, min(1.0, occupancy_rate))
    acw_factor = min(1.0, max(0.0, avg_acw_duration / 300.0))

    score = (
        0.4 * occupancy_factor
        + 0.3 * handle_time_trend
        + 0.3 * acw_factor
    )
    return round(max(0.0, min(1.0, score)), 4)


def _recommend_action(burnout_score: float) -> str:
    """Generate a recommended action based on burnout score."""
    if burnout_score >= 0.9:
        return "Immediate schedule relief required — reassign to low-volume queue within 24 hours"
    if burnout_score >= 0.85:
        return "Schedule relief shift within 48 hours"
    if burnout_score >= 0.7:
        return "Monitor closely — consider reducing shift length next week"
    if burnout_score >= 0.5:
        return "Schedule optional wellness check-in"
    return "No immediate action required"


def handler(event, context):
    """Lambda entry point for get_burnout_signals."""
    tool_name = event.get("tool", "get_burnout_signals")
    params = event.get("parameters", {})

    threshold = float(params.get("threshold", _BURNOUT_CRITICAL_THRESHOLD))
    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)

    try:
        query = _build_query(time_range)
        rows = _cb.call(execute_query, query)

        at_risk_agents = []
        for row in rows:
            agent_id = row.get("agent_id", "")
            avg_occupancy = float(row.get("avg_occupancy", 0))
            avg_acw = float(row.get("avg_acw_duration", 0) or 0)

            # Get handle time trend for this agent
            try:
                trend_query = _build_trend_query(agent_id, time_range)
                trend_rows = _cb.call(execute_query, trend_query)
                handle_time_trend = _calculate_handle_time_trend(trend_rows)
            except Exception:
                handle_time_trend = 0.0

            burnout_score = _calculate_burnout_score(
                avg_occupancy, handle_time_trend, avg_acw
            )

            at_risk_agents.append({
                "agent_id": agent_id,
                "burnout_score": burnout_score,
                "occupancy_rate": round(avg_occupancy, 4),
                "avg_acw_duration": avg_acw,
                "handle_time_trend": handle_time_trend,
                "recommended_action": _recommend_action(burnout_score),
            })

        # Sort by burnout_score descending
        at_risk_agents.sort(key=lambda a: a["burnout_score"], reverse=True)

        # Publish BURNOUT_RISK events for agents above critical threshold
        for agent in at_risk_agents:
            if agent["burnout_score"] > threshold:
                try:
                    publish_alert("BURNOUT_RISK", {
                        "agent_id": agent["agent_id"],
                        "burnout_score": agent["burnout_score"],
                        "occupancy_rate": agent["occupancy_rate"],
                        "recommended_action": agent["recommended_action"],
                        "severity": "HIGH",
                    })
                except Exception:
                    pass  # Alert publish failure — don't break the response

        return {"tool": tool_name, "result": {"at_risk_agents": at_risk_agents}}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
