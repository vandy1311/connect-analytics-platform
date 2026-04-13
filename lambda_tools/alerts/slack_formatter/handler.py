"""Slack webhook formatter Lambda.

Subscribes to all SNS alert topics, formats the alert payload into Slack
Block Kit JSON, and POSTs to the appropriate Slack webhook URL.  Supports
per-alert-type channel routing via the ALERT_CHANNEL_MAP env var.

Retry logic: 3 retries with exponential backoff (1 s, 2 s, 4 s).
Failures are logged to CloudWatch.
"""

import json
import logging
import os
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Alert type metadata — emoji + human-readable label
# ---------------------------------------------------------------------------
_ALERT_META = {
    "SLA_BREACH": {"emoji": "🚨", "label": "SLA Breach"},
    "ABANDONMENT_SPIKE": {"emoji": "📉", "label": "Abandonment Spike"},
    "OCCUPANCY_CRITICAL": {"emoji": "⚠️", "label": "Occupancy Critical"},
    "COMPLIANCE_VIOLATION": {"emoji": "🛑", "label": "Compliance Violation"},
    "BURNOUT_RISK": {"emoji": "🔥", "label": "Burnout Risk"},
}

# Retry config
_MAX_RETRIES = 3
_BASE_DELAY_S = 1  # 1s, 2s, 4s


# ---------------------------------------------------------------------------
# Public helpers (importable for testing)
# ---------------------------------------------------------------------------


def format_slack_message(detail: dict) -> dict:
    """Build a Slack Block Kit message from an alert detail dict.

    Args:
        detail: The EventBridge detail object containing alert_id,
                alert_type, timestamp, severity, and payload.

    Returns:
        A dict with a ``blocks`` list conforming to Slack Block Kit schema.
    """
    alert_type = detail.get("alert_type", "UNKNOWN")
    meta = _ALERT_META.get(alert_type, {"emoji": "❓", "label": alert_type})
    severity = detail.get("severity", "UNKNOWN")
    timestamp = detail.get("timestamp", "N/A")
    payload = detail.get("payload", {})

    header_text = f"{meta['emoji']} {meta['label']}"

    # Build the detail lines common to every alert
    detail_lines = [
        f"*Severity:* {severity}",
        f"*Timestamp:* {timestamp}",
    ]

    # Append type-specific fields
    detail_lines.extend(_type_specific_lines(alert_type, payload))

    section_text = "\n".join(detail_lines)

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": header_text, "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": section_text},
        },
    ]

    return {"blocks": blocks}


def post_to_slack(webhook_url: str, message: dict) -> None:
    """POST *message* to *webhook_url* with retry + exponential backoff.

    Raises after exhausting all retries so the caller can handle the failure.
    """
    payload_bytes = json.dumps(message).encode("utf-8")
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            req = Request(
                webhook_url,
                data=payload_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return
                # Non-200 — treat as failure, retry
                raise URLError(f"Slack returned HTTP {resp.status}")
        except Exception as exc:
            last_exc = exc
            delay = _BASE_DELAY_S * (2 ** attempt)  # 1, 2, 4
            logger.error(
                "Slack delivery attempt %d/%d failed: %s — retrying in %ds",
                attempt + 1,
                _MAX_RETRIES,
                exc,
                delay,
            )
            time.sleep(delay)

    # All retries exhausted
    logger.error("Slack delivery failed after %d retries: %s", _MAX_RETRIES, last_exc)
    raise RuntimeError(
        f"Slack delivery failed after {_MAX_RETRIES} retries"
    ) from last_exc


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------


def handler(event, context):
    """Lambda handler — receives SNS events containing alert details.

    Each SNS record's ``Message`` is a JSON string with the EventBridge
    detail object.
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    channel_map = _load_channel_map()

    for record in event.get("Records", []):
        sns_message = record.get("Sns", {}).get("Message", "{}")
        try:
            detail = json.loads(sns_message)
        except (json.JSONDecodeError, TypeError):
            logger.error("Failed to parse SNS message: %s", sns_message)
            continue

        alert_type = detail.get("alert_type", "UNKNOWN")
        channel = channel_map.get(alert_type)

        message = format_slack_message(detail)

        # If a channel override exists, add it to the payload
        if channel:
            message["channel"] = channel

        try:
            target_url = webhook_url
            post_to_slack(target_url, message)
            logger.info("Alert %s delivered to Slack", detail.get("alert_id"))
        except RuntimeError:
            # Already logged inside post_to_slack; nothing more to do here.
            logger.error(
                "Giving up on alert %s (%s) after retries exhausted",
                detail.get("alert_id"),
                alert_type,
            )

    return {"statusCode": 200, "body": "processed"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_channel_map() -> dict:
    """Load alert-type → Slack-channel mapping from env var."""
    raw = os.environ.get("ALERT_CHANNEL_MAP", "{}")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def _type_specific_lines(alert_type: str, payload: dict) -> list[str]:
    """Return markdown lines for type-specific payload fields."""
    lines: list[str] = []

    if alert_type == "SLA_BREACH":
        if "queue_name" in payload:
            lines.append(f"*Queue:* {payload['queue_name']}")
        if "current_sla_pct" in payload:
            lines.append(f"*Current SLA:* {payload['current_sla_pct']}%")
        if "threshold_pct" in payload:
            lines.append(f"*Threshold:* {payload['threshold_pct']}%")

    elif alert_type == "ABANDONMENT_SPIKE":
        if "queue_name" in payload:
            lines.append(f"*Queue:* {payload['queue_name']}")
        if "abandonment_rate" in payload:
            lines.append(f"*Abandonment Rate:* {payload['abandonment_rate']}%")
        if "spike_threshold" in payload:
            lines.append(f"*Spike Threshold:* {payload['spike_threshold']}%")

    elif alert_type == "OCCUPANCY_CRITICAL":
        if "agent_id" in payload:
            lines.append(f"*Agent:* {payload['agent_id']}")
        if "occupancy_rate" in payload:
            lines.append(f"*Occupancy Rate:* {payload['occupancy_rate']}")
        if "threshold" in payload:
            lines.append(f"*Threshold:* {payload['threshold']}")

    elif alert_type == "COMPLIANCE_VIOLATION":
        if "violation_type" in payload:
            lines.append(f"*Violation Type:* {payload['violation_type']}")
        if "contact_id" in payload:
            lines.append(f"*Contact ID:* {payload['contact_id']}")
        if "agent_id" in payload:
            lines.append(f"*Agent ID:* {payload['agent_id']}")

    elif alert_type == "BURNOUT_RISK":
        if "agent_id" in payload:
            lines.append(f"*Agent ID:* {payload['agent_id']}")
        if "burnout_score" in payload:
            lines.append(f"*Burnout Score:* {payload['burnout_score']}")
        if "occupancy_rate" in payload:
            lines.append(f"*Occupancy Rate:* {payload['occupancy_rate']}")

    return lines
