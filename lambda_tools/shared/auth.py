"""Authentication and RBAC middleware for Connect Analytics Platform.

Provides:
- ``authenticate``: Validates bearer tokens; rejects with 401 if missing/invalid.
- ``authorize``: Enforces role-to-agent mapping; rejects with 403 if denied.
- ``auth_gate``: Combined authenticate + authorize in one call.

Role-to-agent mapping (hackathon scope — simple token-based auth):
    supervisor   → Supervisor_Agent
    qa_analyst   → Quality_Agent
    wfm_planner  → WFM_Agent

Unauthorized access attempts are logged with user_id, attempted_agent, and
timestamp for audit purposes.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role → Agent mapping
# ---------------------------------------------------------------------------
ROLE_AGENT_MAP: dict[str, str] = {
    "supervisor": "Supervisor_Agent",
    "qa_analyst": "Quality_Agent",
    "wfm_planner": "WFM_Agent",
}

# ---------------------------------------------------------------------------
# Token store — loaded from env var or defaults for hackathon
# ---------------------------------------------------------------------------
_TOKEN_STORE: dict[str, dict[str, str]] | None = None


def _load_token_store() -> dict[str, dict[str, str]]:
    """Load the token→user mapping.

    In hackathon mode the mapping lives in the ``AUTH_TOKENS`` env var as
    JSON: ``{"<token>": {"user_id": "...", "role": "..."}, ...}``.

    Falls back to a small built-in set so the demo works out of the box.
    """
    global _TOKEN_STORE
    if _TOKEN_STORE is not None:
        return _TOKEN_STORE

    raw = os.environ.get("AUTH_TOKENS")
    if raw:
        try:
            _TOKEN_STORE = json.loads(raw)
            return _TOKEN_STORE
        except json.JSONDecodeError:
            logger.error("AUTH_TOKENS env var is not valid JSON — using defaults")

    # Built-in demo tokens
    _TOKEN_STORE = {
        "demo-supervisor-token": {"user_id": "supervisor-001", "role": "supervisor"},
        "demo-qa-token": {"user_id": "qa-analyst-001", "role": "qa_analyst"},
        "demo-wfm-token": {"user_id": "wfm-planner-001", "role": "wfm_planner"},
    }
    return _TOKEN_STORE


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def authenticate(token: Optional[str]) -> dict[str, Any]:
    """Validate a bearer token and return the associated user info.

    Parameters
    ----------
    token:
        The bearer token extracted from the request.  ``None`` or empty
        string means no token was provided.

    Returns
    -------
    dict
        On success: ``{"authenticated": True, "user_id": ..., "role": ...}``
        On failure: ``{"authenticated": False, "status_code": 401,
                       "error": "Authentication required"}``
    """
    if not token:
        logger.warning("Authentication failed: no token provided")
        return {
            "authenticated": False,
            "status_code": 401,
            "error": "Authentication required",
        }

    store = _load_token_store()
    user_info = store.get(token)

    if user_info is None:
        logger.warning("Authentication failed: invalid token")
        return {
            "authenticated": False,
            "status_code": 401,
            "error": "Authentication required",
        }

    return {
        "authenticated": True,
        "user_id": user_info["user_id"],
        "role": user_info["role"],
    }


# ---------------------------------------------------------------------------
# Authorization (RBAC)
# ---------------------------------------------------------------------------


def authorize(role: str, target_agent: str) -> dict[str, Any]:
    """Check whether *role* is permitted to access *target_agent*.

    Parameters
    ----------
    role:
        The authenticated user's role (e.g. ``"supervisor"``).
    target_agent:
        The agent the user is trying to reach (e.g. ``"Supervisor_Agent"``).

    Returns
    -------
    dict
        On success: ``{"authorized": True}``
        On failure: ``{"authorized": False, "status_code": 403,
                       "error": "Access denied"}``
    """
    allowed_agent = ROLE_AGENT_MAP.get(role)

    if allowed_agent is None or allowed_agent != target_agent:
        _log_unauthorized_access(
            user_id=role,  # best-effort; caller should pass user_id separately
            attempted_agent=target_agent,
        )
        return {
            "authorized": False,
            "status_code": 403,
            "error": "Access denied",
        }

    return {"authorized": True}


# ---------------------------------------------------------------------------
# Combined gate
# ---------------------------------------------------------------------------


def auth_gate(
    token: Optional[str], target_agent: str
) -> dict[str, Any]:
    """Authenticate and authorize in one call.

    Returns
    -------
    dict
        On success: ``{"allowed": True, "user_id": ..., "role": ...}``
        On failure: ``{"allowed": False, "status_code": 401|403,
                       "error": "..."}``
    """
    auth_result = authenticate(token)
    if not auth_result["authenticated"]:
        return {
            "allowed": False,
            "status_code": auth_result["status_code"],
            "error": auth_result["error"],
        }

    user_id = auth_result["user_id"]
    role = auth_result["role"]

    authz_result = authorize(role, target_agent)
    if not authz_result["authorized"]:
        _log_unauthorized_access(user_id=user_id, attempted_agent=target_agent)
        return {
            "allowed": False,
            "status_code": authz_result["status_code"],
            "error": authz_result["error"],
        }

    return {
        "allowed": True,
        "user_id": user_id,
        "role": role,
    }


# ---------------------------------------------------------------------------
# Audit logging
# ---------------------------------------------------------------------------


def _log_unauthorized_access(user_id: str, attempted_agent: str) -> None:
    """Log an unauthorized access attempt with structured fields."""
    timestamp = datetime.now(timezone.utc).isoformat()
    logger.warning(
        "UNAUTHORIZED_ACCESS user_id=%s attempted_agent=%s timestamp=%s",
        user_id,
        attempted_agent,
        timestamp,
    )
