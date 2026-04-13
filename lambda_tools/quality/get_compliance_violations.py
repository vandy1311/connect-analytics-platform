"""Quality tool — get_compliance_violations.

Scans connect_contact_lens for records with non-empty compliance_flags.
Returns violation details and publishes COMPLIANCE_VIOLATION events to
EventBridge for high-severity violations.
"""

import json

from lambda_tools.shared.alert_publisher import publish_alert
from lambda_tools.shared.athena_client import execute_query
from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
from lambda_tools.shared.error_handler import sanitize_error

_cb = CircuitBreaker()

_DEFAULT_TIME_RANGE = "7d"

_HIGH_SEVERITY_TYPES = {"PCI_VIOLATION", "DATA_BREACH", "HIPAA_VIOLATION"}

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


def _build_query(time_range: str, violation_type: str | None) -> str:
    hours = _hours_from_range(time_range)

    where_clauses = [
        f"analysis_timestamp >= current_timestamp - interval '{hours}' hour",
        "compliance_flags IS NOT NULL",
        "compliance_flags <> '[]'",
    ]
    if violation_type:
        where_clauses.append(
            f"CONTAINS(compliance_flags, '{violation_type}')"
        )

    where_sql = " AND ".join(where_clauses)

    return f"""
SELECT
    contact_id,
    agent_id,
    compliance_flags,
    analysis_timestamp,
    transcript_excerpt
FROM connect_contact_lens
WHERE {where_sql}
ORDER BY analysis_timestamp DESC
"""


def _parse_flags(raw_flags) -> list[str]:
    """Parse compliance_flags from Athena result (may be JSON string or list)."""
    if isinstance(raw_flags, list):
        return raw_flags
    if isinstance(raw_flags, str):
        try:
            parsed = json.loads(raw_flags)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        # Fallback: comma-separated or single value
        return [f.strip() for f in raw_flags.split(",") if f.strip()]
    return []


def _is_high_severity(violation_type: str, event_payload: dict) -> bool:
    """Determine if a violation warrants a HIGH severity alert."""
    severity = event_payload.get("severity", "").upper()
    if severity == "HIGH":
        return True
    return violation_type.upper() in _HIGH_SEVERITY_TYPES


def handler(event, context):
    """Lambda entry point for get_compliance_violations."""
    tool_name = event.get("tool", "get_compliance_violations")
    params = event.get("parameters", {})

    time_range = params.get("time_range", _DEFAULT_TIME_RANGE)
    violation_type = params.get("violation_type")

    try:
        query = _build_query(time_range, violation_type)
        rows = _cb.call(execute_query, query)

        violations = []
        for row in rows:
            flags = _parse_flags(row.get("compliance_flags", ""))
            contact_id = row.get("contact_id", "")
            agent_id = row.get("agent_id", "")
            timestamp = row.get("analysis_timestamp", "")
            excerpt = row.get("transcript_excerpt", "")

            for flag in flags:
                if violation_type and flag.upper() != violation_type.upper():
                    continue

                violation = {
                    "violation_type": flag,
                    "contact_id": contact_id,
                    "agent_id": agent_id,
                    "timestamp": timestamp,
                    "transcript_excerpt": excerpt,
                }
                violations.append(violation)

                # Publish alert for high-severity violations
                if _is_high_severity(flag, params):
                    try:
                        publish_alert("COMPLIANCE_VIOLATION", {
                            "violation_type": flag,
                            "contact_id": contact_id,
                            "agent_id": agent_id,
                            "transcript_excerpt": excerpt,
                            "severity": "HIGH",
                        })
                    except Exception:
                        pass  # Alert publish failure — don't break the response

        return {"tool": tool_name, "result": {"violations": violations}}

    except CircuitOpenError as exc:
        return {
            "tool": tool_name,
            "error": f"Service temporarily unavailable. Retry after {exc.retry_after:.0f}s.",
        }
    except Exception as exc:
        return {"tool": tool_name, **sanitize_error(exc)}
