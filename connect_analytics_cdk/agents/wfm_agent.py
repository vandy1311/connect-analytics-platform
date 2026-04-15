"""WFM Agent construct for Bedrock AgentCore.

Creates the WFM (Workforce Management) Agent (Nova Lite) with its two tools,
referencing the shared AgentCore Gateway created by the Supervisor Agent
construct.

Exposed properties
------------------
- agent_id – logical ID of the WFM Agent (for cross-stack refs)
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
WFM_MODEL_ID = "amazon.nova-lite-v2:0"

WFM_SYSTEM_PROMPT = (
    "You are the WFM (Workforce Management) Agent for an Amazon Connect "
    "contact center analytics platform. Your domain covers staffing "
    "forecasts, schedule optimization, and agent burnout detection.\n\n"
    "When a user asks a question:\n"
    "1. Determine which tool(s) to call based on the query intent.\n"
    "2. Interpret the tool results and provide a concise, actionable summary.\n"
    "3. If a critical burnout risk is detected, highlight it prominently.\n\n"
    "You have access to two tools:\n"
    "- get_staffing_forecast: Analyzes historical contact volume patterns "
    "and projects future demand with confidence intervals and a chart.\n"
    "- get_burnout_signals: Detects agents at risk of burnout based on "
    "sustained high occupancy, extended ACW, and increasing handle times.\n\n"
    "Stay within the workforce planning domain. If a question is about queue "
    "health, SLA breaches, sentiment analysis, or compliance violations, "
    "respond that it is outside your scope and suggest the appropriate agent "
    "(Supervisor or Quality)."
)

# ---------------------------------------------------------------------------
# Tool schema definitions
# ---------------------------------------------------------------------------
WFM_TOOLS = [
    {
        "name": "get_staffing_forecast",
        "description": (
            "Analyzes historical contact volume patterns and projects future "
            "demand with confidence intervals. Returns a forecast with "
            "predicted volume, recommended staffing, and an area chart with "
            "confidence bands."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "forecast_horizon_days": {
                    "type": "integer",
                    "description": (
                        "Number of days to forecast. Defaults to 7."
                    ),
                },
                "queue_name": {
                    "type": "string",
                    "description": "Queue to forecast. Omit for all queues.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_burnout_signals",
        "description": (
            "Detects agents at risk of burnout by analyzing occupancy rates, "
            "after-contact-work durations, and handle time trends. Returns a "
            "ranked list of at-risk agents with burnout scores and recommended "
            "actions. Critical burnout risks trigger automatic alerts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "number",
                    "description": (
                        "Minimum burnout score (0.0-1.0) to include in results. "
                        "Defaults to the critical threshold (0.85)."
                    ),
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range, e.g. 'last_7d'. Defaults to 'last_7d'.",
                },
            },
            "required": [],
        },
    },
]


class WfmAgent(Construct):
    """CDK construct for the WFM Agent on Bedrock AgentCore.

    Creates the WFM Agent registered with the shared gateway and two tools.
    The gateway must already exist (created by the Supervisor Agent construct).

    Parameters
    ----------
    scope : Construct
        CDK scope.
    id : str
        Construct ID.
    tool_lambda : lambda_.IFunction
        The Lambda function that handles all WFM tool invocations.
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
        # IAM role for the WFM Agent
        # ------------------------------------------------------------------
        self._agent_role = iam.Role(
            self,
            "WfmAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Execution role for the WFM AgentCore agent",
        )

        # ------------------------------------------------------------------
        # WFM Agent (CfnResource — no L2 construct yet)
        # ------------------------------------------------------------------
        self._agent = CfnResource(
            self,
            "WfmAgent",
            type="AWS::BedrockAgentCore::Agent",
            properties={
                "AgentName": "connect-wfm-agent",
                "Description": (
                    "WFM Agent — generates staffing forecasts and detects "
                    "agent burnout signals for workforce planning."
                ),
                "ModelId": WFM_MODEL_ID,
                "Instruction": WFM_SYSTEM_PROMPT,
                "GatewayId": gateway_id,
                "RoleArn": self._agent_role.role_arn,
                "Tools": [
                    {
                        "Name": tool["name"],
                        "Description": tool["description"],
                        "Parameters": tool["parameters"],
                    }
                    for tool in WFM_TOOLS
                ],
            },
        )

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def agent_id(self) -> str:
        """Logical ID / Ref of the WFM Agent resource."""
        return self._agent.ref
