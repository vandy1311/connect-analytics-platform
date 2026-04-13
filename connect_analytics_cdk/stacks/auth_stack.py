"""Authentication stack for Connect Analytics Platform.

Hackathon scope: simple API-key-based token validation with role-to-agent
mapping stored as Lambda environment variables.  Cognito integration is
planned for post-hackathon.

Defines:
- Role-to-agent mapping configuration (passed to tool Lambdas as env vars)
- API key validation parameters
"""

from __future__ import annotations

import json

from aws_cdk import (
    CfnOutput,
    Stack,
)
from constructs import Construct

# ---------------------------------------------------------------------------
# Default role → agent mapping
# ---------------------------------------------------------------------------
DEFAULT_ROLE_AGENT_MAP: dict[str, str] = {
    "supervisor": "Supervisor_Agent",
    "qa_analyst": "Quality_Agent",
    "wfm_planner": "WFM_Agent",
}

# Default demo tokens (hackathon only — NOT for production)
DEFAULT_AUTH_TOKENS: dict[str, dict[str, str]] = {
    "demo-supervisor-token": {"user_id": "supervisor-001", "role": "supervisor"},
    "demo-qa-token": {"user_id": "qa-analyst-001", "role": "qa_analyst"},
    "demo-wfm-token": {"user_id": "wfm-planner-001", "role": "wfm_planner"},
}


class AuthStack(Stack):
    """Lightweight API-key auth stack for hackathon scope.

    Exposes configuration values that other stacks inject into Lambda
    environment variables.  Post-hackathon this will be replaced by a
    Cognito User Pool with custom attributes for role mapping.

    Attributes
    ----------
    role_agent_map : dict[str, str]
        Role-to-agent mapping (e.g. ``supervisor`` → ``Supervisor_Agent``).
    auth_tokens_json : str
        JSON-serialised token store for Lambda env vars.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        role_agent_map: dict[str, str] | None = None,
        auth_tokens: dict[str, dict[str, str]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.role_agent_map = role_agent_map or DEFAULT_ROLE_AGENT_MAP
        self.auth_tokens_json = json.dumps(auth_tokens or DEFAULT_AUTH_TOKENS)

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "RoleAgentMapping",
            value=json.dumps(self.role_agent_map),
            description="Role-to-agent mapping (JSON)",
        )

        CfnOutput(
            self,
            "AuthMode",
            value="api-key",
            description="Authentication mode (api-key for hackathon, cognito post-hackathon)",
        )
