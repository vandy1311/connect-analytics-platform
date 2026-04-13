"""Error sanitization — strips SQL, table names, stack traces, ARNs, and account IDs."""

import re
import uuid


# SQL keywords to strip (case-insensitive)
_SQL_KEYWORDS = re.compile(
    r"\b(SELECT|FROM|WHERE|JOIN|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|"
    r"GROUP\s+BY|ORDER\s+BY|HAVING|UNION|INNER|OUTER|LEFT|RIGHT|CROSS|"
    r"ON|INTO|VALUES|SET|TABLE|INDEX|VIEW|LIMIT|OFFSET|DISTINCT|AS|AND|OR|"
    r"NOT|IN|EXISTS|BETWEEN|LIKE|IS\s+NULL|IS\s+NOT\s+NULL|CASE|WHEN|THEN|"
    r"ELSE|END|COUNT|SUM|AVG|MIN|MAX|CAST|COALESCE)\b",
    re.IGNORECASE,
)

# Known table names from the Connect Analytics data catalog
_TABLE_NAMES = re.compile(
    r"\b(connect_ctr|connect_agent_events|connect_contact_lens)\b",
    re.IGNORECASE,
)

# Python stack trace patterns
_PYTHON_TRACEBACK = re.compile(
    r"(Traceback \(most recent call last\).*?)(?=\n\n|\Z)",
    re.DOTALL,
)
_PYTHON_EXCEPTION_CLASS = re.compile(
    r"\b\w*(Error|Exception|Warning)\b:\s*.*",
)

# Java stack trace patterns
_JAVA_STACKTRACE = re.compile(r"\bat\s+[\w.$]+\([\w.]+:\d+\)")

# AWS ARN pattern
_ARN_PATTERN = re.compile(r"arn:aws[\w-]*:[\w-]+:[^:\s]*:\d{12}:[^\s]+")

# AWS account ID (12-digit standalone numbers)
_ACCOUNT_ID = re.compile(r"\b\d{12}\b")


def sanitize_error(error: Exception) -> dict:
    """Sanitize an error for safe user-facing display.

    Strips SQL keywords, table names, Python/Java stack traces, ARNs,
    and AWS account IDs. Adds a correlation ID for log tracing.

    Args:
        error: The exception to sanitize.

    Returns:
        Dict with 'error' (user-friendly message) and 'correlation_id' (uuid).
    """
    correlation_id = str(uuid.uuid4())
    raw = str(error)

    sanitized = _sanitize_message(raw)

    # If sanitization removed everything meaningful, use a generic message
    cleaned = sanitized.strip()
    if not cleaned or len(cleaned) < 3:
        sanitized = "An internal error occurred. Please try again."

    return {
        "error": sanitized,
        "correlation_id": correlation_id,
    }


def _sanitize_message(message: str) -> str:
    """Apply all sanitization rules to a raw error message."""
    text = message

    # Remove Python tracebacks first (multi-line)
    text = _PYTHON_TRACEBACK.sub("[internal error]", text)

    # Remove Java stack trace lines
    text = _JAVA_STACKTRACE.sub("[internal error]", text)

    # Remove Python exception class names with messages
    text = _PYTHON_EXCEPTION_CLASS.sub("[error details removed]", text)

    # Remove ARNs
    text = _ARN_PATTERN.sub("[resource]", text)

    # Remove AWS account IDs
    text = _ACCOUNT_ID.sub("[account]", text)

    # Remove known table names
    text = _TABLE_NAMES.sub("[table]", text)

    # Remove SQL keywords
    text = _SQL_KEYWORDS.sub("", text)

    # Collapse multiple spaces / whitespace runs
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()
