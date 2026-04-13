"""EventBridge PutEvents wrapper for publishing alerts."""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3


_EVENTS = boto3.client("events")

_EVENT_BUS = os.environ.get("EVENT_BUS", "default")
_SOURCE = "connect-analytics"


def publish_alert(alert_type: str, payload: dict) -> str:
    """Publish an alert event to EventBridge.

    Args:
        alert_type: The detail-type for the event
            (e.g. SLA_BREACH, COMPLIANCE_VIOLATION, BURNOUT_RISK).
        payload: Alert-specific data to include in the event detail.

    Returns:
        The generated alert_id (uuid4 string).
    """
    alert_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    severity = payload.get("severity", "MEDIUM")

    detail = {
        "alert_id": alert_id,
        "alert_type": alert_type,
        "timestamp": timestamp,
        "severity": severity,
        "payload": payload,
    }

    _EVENTS.put_events(
        Entries=[
            {
                "Source": _SOURCE,
                "DetailType": alert_type,
                "Detail": json.dumps(detail),
                "EventBusName": _EVENT_BUS,
            }
        ]
    )

    return alert_id
