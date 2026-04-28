"""Input validation for tool parameters — prevents SQL injection."""

import re

# Allowlists
VALID_QUEUES = {"Billing", "Support", "Sales", "Returns", "VIP", "Technical", "General Support"}
VALID_TIME_RANGES = {"1h", "4h", "8h", "12h", "24h", "48h", "7d", "30d"}
AGENT_ID_PATTERN = re.compile(r"^Agent-\d{3}$")


def validate_queue_name(value: str | None) -> str | None:
    """Validate and sanitize queue_name parameter."""
    if value is None:
        return None
    value = value.strip()
    if value not in VALID_QUEUES:
        return None
    return value


def validate_time_range(value: str | None, default: str = "24h") -> str:
    """Validate time_range parameter."""
    if value is None:
        return default
    value = value.strip().lower()
    if value not in VALID_TIME_RANGES:
        return default
    return value


def validate_agent_id(value: str | None) -> str | None:
    """Validate agent_id parameter (Agent-NNN format)."""
    if value is None:
        return None
    value = value.strip()
    if not AGENT_ID_PATTERN.match(value):
        return None
    return value


def safe_sql_string(value: str) -> str:
    """Escape a string for safe SQL interpolation as a last resort."""
    return value.replace("'", "''").replace(";", "").replace("--", "")
