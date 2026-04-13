"""Quality Agent construct for Bedrock AgentCore.

Creates the Quality Agent (Claude Sonnet) with its three tools, referencing
the shared AgentCore Gateway created by the Supervisor Agent construct.

Exposed properties
------------------
- agent_id – logical ID of the Quality Agent (for cross-stack refs)
"""

from aws_cdk import (
    CfnResource,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
QUALITY_MODEL_ID = "anthropic.claude-sonnet-4"

QUALITY_SYSTEM_PROMPT = (
    "You are the Quality Agent for an Amazon Connect contact center analytics "
    "platform. Your domain covers customer sentiment analysis, agent coaching "
    "recommendations, and compliance violation detection.\n\n"
    "When a user asks a question:\n"
    "1. Determine which tool(s) to call based on the query intent.\n"
    "2. Interpret the tool results and provide a concise, actionable summary.\n"
    "3. If a high-severity compliance violation is detected, note it clearly.\n\n"
    "You have access to three tools:\n"
    "- get_sentiment_trends: Returns sentiment aggregation over time with a "
    "trend chart (positive, negative, neutral, mixed percentages by period).\n"
    "- get_coaching_recommendations: Identifies agents with high negative "
    "sentiment rates and provides coaching suggestions with sample excerpts.\n"
    "- get_compliance_violations: Scans for compliance violations in contact "
    "transcripts and flags high-severity issues.\n\n"
    "Stay within the quality/compliance domain. If a question is about queue "
    "health, SLA breaches, staffing forecasts, or burnout signals, respond "
    "that it is outside your scope and suggest the appropriate agent "
    "(Supervisor or WFM)."
)

# ---------------------------------------------------------------------------
# Tool schema definitions
# ---------------------------------------------------------------------------
QUALITY_TOOLS = [
    {
        "name": "get_sentiment_trends",
        "description": (
            "Returns aggregated sentiment percentages (positive, negative, "
            "neutral, mixed) by period with a trend line chart. Optionally "
            "filter by agent ID and time range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "description": (
                        "Time range for the query, e.g. 'last_7d', 'last_30d'. "
                        "Defaults to 'last_7d'."
                    ),
                },
                "agent_id": {
                    "type": "string",
                    "description": "Specific agent ID. Omit for all agents.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_coaching_recommendations",
        "description": (
            "Identifies agents with high negative sentiment rates and returns "
            "coaching recommendations with sample transcript excerpts and "
            "actionable coaching suggestions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Specific agent ID. Omit for all agents.",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range, e.g. 'last_7d'. Defaults to 'last_7d'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_compliance_violations",
        "description": (
            "Scans Contact Lens data for compliance violations. Returns "
            "violation type, contact ID, agent ID, timestamp, and transcript "
            "excerpt. High-severity violations trigger alerts automatically."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "description": "Time range, e.g. 'last_7d'. Defaults to 'last_7d'.",
                },
                "violation_type": {
                    "type": "string",
                    "description": (
                        "Filter by violation type, e.g. 'PCI_VIOLATION', "
                        "'MISSING_DISCLOSURE'. Omit for all types."
                    ),
                },
            },
            "required": [],
        },
    },
]


class QualityAgent(Construct):
    """CDK construct for the Quality Agent on Bedrock AgentCore.

    Creates the Quality Agent registered with the shared gateway and
    three tools.  The gateway must already exist (created by the
    Supervisor Agent construct).

    Parameters
    ----------
    scope : Construct
        CDK scope.
    id : str
        Construct ID.
    tool_lambda : lambda_.IFunction
        The Lambda function that handles all quality tool invocations.
    gateway_id : str
        The shared AgentCore Gateway ID (from Supervisor Agent construct).
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        tool_lambda: lambda_.IFunction,
        gateway_id: str,
    ) -> None:
        super().__init__(scope, id)

        # ------------------------------------------------------------------
        # IAM role for the Quality Agent
        # ------------------------------------------------------------------
        self._agent_role = iam.Role(
            self,
            "QualityAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Execution role for the Quality AgentCore agent",
        )

        # ------------------------------------------------------------------
        # Quality Agent (CfnResource — no L2 construct yet)
        # ------------------------------------------------------------------
        self._agent = CfnResource(
            self,
            "QualityAgent",
            type="AWS::BedrockAgentCore::Agent",
            properties={
                "AgentName": "connect-quality-agent",
                "Description": (
                    "Quality Agent — analyzes sentiment trends, provides "
                    "coaching recommendations, and detects compliance violations."
                ),
                "ModelId": QUALITY_MODEL_ID,
                "Instruction": QUALITY_SYSTEM_PROMPT,
                "GatewayId": gateway_id,
                "RoleArn": self._agent_role.role_arn,
                "Tools": [
                    {
                        "Name": tool["name"],
                        "Description": tool["description"],
                        "Parameters": tool["parameters"],
                    }
                    for tool in QUALITY_TOOLS
                ],
            },
        )

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def agent_id(self) -> str:
        """Logical ID / Ref of the Quality Agent resource."""
        return self._agent.ref
