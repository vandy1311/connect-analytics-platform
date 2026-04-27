"""Authentication stack for Connect Analytics Platform.

Hackathon scope: simple API-key-based token validation with role-to-agent
mapping stored as Lambda environment variables.  Cognito integration is
planned for post-hackathon.

Defines:
- Role-to-agent mapping configuration (passed to tool Lambdas as env vars)
- Auth tokens stored in Secrets Manager (not hardcoded)
"""

from __future__ import annotations

import json

from aws_cdk import (
    CfnOutput,
    Stack,
    aws_secretsmanager as secretsmanager,
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


class AuthStack(Stack):
    """Auth stack with tokens stored in Secrets Manager.

    Attributes
    ----------
    role_agent_map : dict[str, str]
        Role-to-agent mapping.
    auth_tokens_json : str
        Reference to the Secrets Manager secret ARN for Lambda env vars.
    auth_secret : secretsmanager.Secret
        The Secrets Manager secret containing auth tokens.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        role_agent_map: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.role_agent_map = role_agent_map or DEFAULT_ROLE_AGENT_MAP

        # ------------------------------------------------------------------
        # Auth tokens in Secrets Manager (not hardcoded in source)
        # ------------------------------------------------------------------
        self.auth_secret = secretsmanager.Secret(
            self,
            "AuthTokensSecret",
            secret_name="connect-analytics/auth-tokens",
            description="API auth tokens for Connect Analytics Platform",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "demo-supervisor-token": {"user_id": "supervisor-001", "role": "supervisor"},
                    "demo-qa-token": {"user_id": "qa-analyst-001", "role": "qa_analyst"},
                    "demo-wfm-token": {"user_id": "wfm-planner-001", "role": "wfm_planner"},
                }),
                generate_string_key="_rotation_marker",
            ),
        )

        # For Lambda env var — pass the secret ARN, not the value
        self.auth_tokens_json = self.auth_secret.secret_arn

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
            value="secrets-manager",
            description="Authentication mode (secrets-manager for tokens)",
        )

        CfnOutput(
            self,
            "AuthSecretArn",
            value=self.auth_secret.secret_arn,
            description="Secrets Manager ARN for auth tokens",
        )
