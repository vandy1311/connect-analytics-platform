"""Quality tool — get_sentiment_trends.

Returns sentiment aggregation by period (day) with a matplotlib line chart
encoded as base64 PNG.  Queries connect_contact_lens via Athena, wrapped
in a circuit breaker.
"""

import base64
import io
import json

from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "7d"

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


def _build_query(time_range: str, agent_id: str | None) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"analysis_timestamp >= current_timestamp - interval '{hours}' hour",
    ]
    if agent_id:
        where_clauses.append(f"agent_id = '{agent_id}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    CAST(analysis_timestamp AS DATE) AS period,
    COUNT(*) AS total,
    SUM(CASE WHEN overall_sentiment = 'POSITIVE' THEN 1 ELSE 0 END) AS positive_count,
    SUM(CASE WHEN overall_sentiment = 'NEGATIVE' THEN 1 ELSE 0 END) AS negative_count,
    SUM(CASE WHEN overall_sentiment = 'NEUTRAL' THEN 1 ELSE 0 END) AS neutral_count,
    SUM(CASE WHEN overall_sentiment = 'MIXED' THEN 1 ELSE 0 END) AS mixed_count
FROM connect_contact_lens
WHERE {where_sql}
GROUP BY CAST(analysis_timestamp AS DATE)
ORDER BY period ASC
"""


def _aggregate_periods(rows: list[dict]) -> list[dict]:
    """Convert raw Athena rows into sentiment percentage periods."""
    periods = []
    for row in rows:
        total = int(row.get("total", 0))
        if total == 0:
            continue
        periods.append({
            "date": row.get("period", ""),
            "positive_pct": round(100.0 * int(row.get("positive_count", 0)) / total, 2),
            "negative_pct": round(100.0 * int(row.get("negative_count", 0)) / total, 2),
            "neutral_pct": round(100.0 * int(row.get("neutral_count", 0)) / total, 2),
            "mixed_pct": round(100.0 * int(row.get("mixed_count", 0)) / total, 2),
        })
    return periods


def _generate_chart(periods: list[dict]) -> str:
    """Generate a matplotlib line chart of sentiment over time, return base64 PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dates = [p["date"] for p in periods]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, [p["positive_pct"] for p in periods], label="Positive", color="#2ecc71", marker="o")
    ax.plot(dates, [p["negative_pct"] for p in periods], label="Negative", color="#e74c3c", marker="o")
    ax.plot(dates, [p["neutral_pct"] for p in periods], label="Neutral", color="#95a5a6", marker="o")
    ax.plot(dates, [p["mixed_pct"] for p in periods], label="Mixed", color="#f39c12", marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Percentage (%)")
    ax.set_title("Sentiment Trends Over Time")
    ax.legend()
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def handler(event, context):
    """Lambda entry point for get_sentiment_trends."""
    tool_name = event.get("tool", "get_sentiment_trends")
    params = event.get("parameters", {})

    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)
    agent_id = params.get("agent_id")

    try:
        query = _build_query(time_range, agent_id)
        rows = _cb.call(execute_query, query)

        periods = _aggregate_periods(rows)

        chart = None
        if periods:
            try:
                chart = _generate_chart(periods)
            except Exception:
                pass  # Chart generation failure — return text-only

        result = {"periods": periods}
        if chart:
            result["chart"] = chart

        return {"tool": tool_name, "result": result}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
