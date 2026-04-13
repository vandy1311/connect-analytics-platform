"""WFM tool — get_staffing_forecast.

Analyzes historical CTR volume patterns and projects contact volume with
confidence intervals.  Generates a matplotlib area chart with confidence
bands, encoded as base64 PNG.
"""

import base64
import io
import json
import math
from collections import defaultdict

from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_HORIZON = 7


def _build_query(queue_name: str | None) -> str:
    """Query historical volume patterns by hour and day-of-week."""
    where_clauses = [
        "initiation_timestamp >= current_timestamp - interval '30' day",
    ]
    if queue_name:
        where_clauses.append(f"queue_name = '{queue_name}'")

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    EXTRACT(DOW FROM initiation_timestamp) AS day_of_week,
    EXTRACT(HOUR FROM initiation_timestamp) AS hour_of_day,
    COUNT(*) AS contact_count,
    CAST(initiation_timestamp AS DATE) AS contact_date
FROM connect_ctr
WHERE {where_sql}
GROUP BY
    EXTRACT(DOW FROM initiation_timestamp),
    EXTRACT(HOUR FROM initiation_timestamp),
    CAST(initiation_timestamp AS DATE)
ORDER BY day_of_week, hour_of_day
"""


def _compute_forecast(rows: list[dict], horizon_days: int) -> list[dict]:
    """Compute projected volume with confidence intervals.

    Groups historical data by (day_of_week, hour_of_day), calculates
    mean and stddev, then projects forward for the requested horizon.
    Confidence interval: mean ± 1.5 * stddev.
    """
    # Group volumes by (dow, hour)
    volume_map: dict[tuple[int, int], list[int]] = defaultdict(list)
    for row in rows:
        dow = int(row.get("day_of_week", 0))
        hour = int(row.get("hour_of_day", 0))
        count = int(row.get("contact_count", 0))
        volume_map[(dow, hour)].append(count)

    forecast = []
    for day_offset in range(horizon_days):
        # Cycle through days of week (0=Sunday in Athena DOW)
        # We start from day_offset=0 as "today"
        dow = day_offset % 7

        for hour in range(24):
            volumes = volume_map.get((dow, hour), [])
            if volumes:
                mean_vol = sum(volumes) / len(volumes)
                if len(volumes) > 1:
                    variance = sum((v - mean_vol) ** 2 for v in volumes) / (len(volumes) - 1)
                    stddev = math.sqrt(variance)
                else:
                    stddev = mean_vol * 0.2  # Default 20% uncertainty for single data point
            else:
                mean_vol = 0.0
                stddev = 0.0

            predicted = max(0, round(mean_vol))
            margin = 1.5 * stddev
            lower = max(0, round(mean_vol - margin))
            upper = max(0, round(mean_vol + margin))

            # Estimate staffing: ~15 contacts per agent per hour
            recommended_staff = max(1, math.ceil(upper / 15))
            current_staff = max(1, math.ceil(predicted / 15))

            forecast.append({
                "date": f"day+{day_offset}",
                "hour": hour,
                "predicted_volume": predicted,
                "current_staff": current_staff,
                "recommended_staff": recommended_staff,
                "confidence_lower": lower,
                "confidence_upper": upper,
            })

    return forecast


def _generate_chart(forecast: list[dict]) -> str:
    """Generate a matplotlib area chart with confidence bands, return base64 PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x_labels = [f"D{e['date'].replace('day+', '')}H{e['hour']}" for e in forecast]
    x = list(range(len(forecast)))
    predicted = [e["predicted_volume"] for e in forecast]
    lower = [e["confidence_lower"] for e in forecast]
    upper = [e["confidence_upper"] for e in forecast]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(x, predicted, label="Predicted Volume", color="#3498db", linewidth=1.5)
    ax.fill_between(x, lower, upper, alpha=0.25, color="#3498db", label="Confidence Band")
    ax.set_xlabel("Time Slot")
    ax.set_ylabel("Contact Volume")
    ax.set_title("Staffing Forecast with Confidence Intervals")
    ax.legend()

    # Show sparse x-tick labels to avoid clutter
    step = max(1, len(x) // 20)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(x_labels[::step], rotation=45, fontsize=7)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def handler(event, context):
    """Lambda entry point for get_staffing_forecast."""
    tool_name = event.get("tool", "get_staffing_forecast")
    params = event.get("parameters", {})

    horizon_days = int(params.get("forecast_horizon_days", _DEFAULT_HORIZON))
    queue_name = params.get("queue_name")

    try:
        query = _build_query(queue_name)
        rows = _cb.call(execute_query, query)

        forecast = _compute_forecast(rows, horizon_days)

        chart = None
        if forecast:
            try:
                chart = _generate_chart(forecast)
            except Exception:
                pass  # Chart generation failure — return text-only

        result = {"forecast": forecast}
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
