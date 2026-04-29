"""Quality tool — get_coaching_recommendations.

Identifies agents with high negative sentiment rates and returns coaching
recommendations with sample excerpts.  Queries connect_contact_lens via
Athena, wrapped in a circuit breaker.
"""

import os

from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "7d"
_NEGATIVE_THRESHOLD_PCT = float(
    os.environ.get("NEGATIVE_SENTIMENT_THRESHOLD", "15")
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


def _build_agent_sentiment_query(agent_id: str | None, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"analysis_timestamp >= current_timestamp - interval '{hours}' hour",
    ]
    if agent_id:
        where_clauses.append(f"agent_id = '{agent_id}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    agent_id,
    COUNT(*) AS total_contacts,
    SUM(CASE WHEN overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) AS negative_count,
    ROUND(
        100.0 * SUM(CASE WHEN overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS negative_sentiment_rate
FROM connect_contact_lens
WHERE {where_sql}
GROUP BY agent_id
HAVING ROUND(
    100.0 * SUM(CASE WHEN overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0),
    2
) >= {_NEGATIVE_THRESHOLD_PCT}
ORDER BY negative_sentiment_rate DESC
"""


def _build_excerpts_query(agent_id: str, time_range: str) -> str:
    hours = _hours_from_range(time_range)

    return f"""
SELECT transcript_excerpt
FROM connect_contact_lens
WHERE agent_id = '{agent_id}'
  AND overall_sentiment = 'NEGATIVE'
  AND analysis_timestamp >= current_timestamp - interval '{hours}' hour
ORDER BY analysis_timestamp DESC
LIMIT 3
"""


def _generate_coaching_suggestions(negative_rate: float) -> list[str]:
    """Generate coaching suggestions based on negative sentiment rate."""
    suggestions = []
    if negative_rate >= 30:
        suggestions.append("Schedule immediate 1:1 coaching session with team lead")
        suggestions.append("Review call recordings for de-escalation opportunities")
    if negative_rate >= 20:
        suggestions.append("Assign empathy and active listening training module")
        suggestions.append("Pair with a high-performing agent for shadowing")
    suggestions.append("Review recent negative interactions for common patterns")
    suggestions.append("Practice positive language framing techniques")
    return suggestions


def handler(event, context):
    """Lambda entry point for get_coaching_recommendations."""
    tool_name = event.get("tool", "get_coaching_recommendations")
    params = event.get("parameters", {})

    agent_id = params.get("agent_id")
    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)

    try:
        query = _build_agent_sentiment_query(agent_id, time_range)
        rows = _cb.call(execute_query, query)

        recommendations = []
        for row in rows:
            aid = row.get("agent_id", "")
            neg_rate = float(row.get("negative_sentiment_rate", 0))

            # Fetch sample excerpts for this agent
            excerpts_query = _build_excerpts_query(aid, time_range)
            try:
                excerpt_rows = _cb.call(execute_query, excerpts_query)
                sample_excerpts = [
                    r.get("transcript_excerpt", "") for r in excerpt_rows
                ]
            except Exception:
                sample_excerpts = []

            recommendations.append({
                "agent_id": aid,
                "negative_sentiment_rate": neg_rate,
                "sample_excerpts": sample_excerpts,
                "coaching_suggestions": _generate_coaching_suggestions(neg_rate),
            })

        return {"tool": tool_name, "result": {"recommendations": recommendations}}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
