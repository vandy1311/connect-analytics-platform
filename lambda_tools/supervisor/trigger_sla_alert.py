"""Supervisor tool — trigger_sla_alert.

Publishes an SLA_BREACH event to EventBridge when the current SLA percentage
falls below the configured threshold.  Threshold config is read from the
SLA_THRESHOLDS env var (JSON), with a per-queue override and a default fallback.
"""

import json
import os

from lambda_tools.shared.alert_publisher import publish_alert
from lambda_tools.shared.error_handler import sanitize_error

_DEFAULT_THRESHOLDS = {
    "default": {"target_pct": 80, "window_seconds": 20},
}


def _load_thresholds() -> dict:
    """Load SLA thresholds from env var, falling back to defaults."""
    raw = os.environ.get("SLA_THRESHOLDS")
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return _DEFAULT_THRESHOLDS


def get_threshold(queue_name: str) -> dict:
    """Return the SLA threshold config for a queue.

    Returns the per-queue config if one exists, otherwise the default.
    Guaranteed to contain 'target_pct' and 'window_seconds' with positive values.
    """
    thresholds = _load_thresholds()
    config = thresholds.get(queue_name, thresholds.get("default", _DEFAULT_THRESHOLDS["default"]))

    # Ensure positive values
    target_pct = config.get("target_pct", 80)
    window_seconds = config.get("window_seconds", 20)
    return {
        "target_pct": max(1, target_pct),
        "window_seconds": max(1, window_seconds),
    }


def handler(event, context):
    """Lambda entry point for trigger_sla_alert."""
    tool_name = event.get("tool", "trigger_sla_alert")
    params = event.get("parameters", {})

    queue_name = params.get("queue_name")
    current_sla_pct = params.get("current_sla_pct")
    threshold_pct = params.get("threshold_pct")
    breach_timestamp = params.get("breach_timestamp")

    # Validate required fields
    if not queue_name or current_sla_pct is None or threshold_pct is None or not breach_timestamp:
        return {
            "tool": tool_name,
            "error": "Missing required parameters: queue_name, current_sla_pct, threshold_pct, breach_timestamp",
        }

    try:
        current_sla_pct = float(current_sla_pct)
        threshold_pct = float(threshold_pct)
    except (ValueError, TypeError) as exc:
        return {"tool": tool_name, **sanitize_error(exc)}

    try:
        # Look up the configured threshold for this queue
        config = get_threshold(queue_name)

        payload = {
            "queue_name": queue_name,
            "current_sla_pct": current_sla_pct,
            "threshold_pct": threshold_pct,
            "breach_timestamp": breach_timestamp,
            "configured_target_pct": config["target_pct"],
            "configured_window_seconds": config["window_seconds"],
            "severity": "HIGH" if current_sla_pct < threshold_pct * 0.75 else "MEDIUM",
        }

        alert_id = publish_alert("SLA_BREACH", payload)

        return {
            "tool": tool_name,
            "result": {
                "alert_id": alert_id,
                "status": "published",
            },
        }

    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
