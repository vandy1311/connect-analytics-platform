"""Supervisor Agent construct for Bedrock AgentCore.

Creates the Supervisor Agent (Claude Sonnet) with its four tools and an
AgentCore Gateway.  The gateway is a shared resource: the first agent
construct creates it; subsequent agents receive the gateway ID as a
parameter and skip creation.

Exposed properties
------------------
- agent_id   – logical ID of the Supervisor Agent (for cross-stack refs)
- gateway_id – logical ID of the AgentCore Gateway
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
SUPERVISOR_MODEL_ID = "anthropic.claude-sonnet-4"

SUPERVISOR_SYSTEM_PROMPT = (
    "You are the Supervisor Agent for an Amazon Connect contact center analytics "
    "platform. Your domain covers real-time queue health monitoring, SLA breach "
    "detection, agent utilization tracking, and abandonment root-cause analysis.\n\n"
    "When a user asks a question:\n"
    "1. Determine which tool(s) to call based on the query intent.\n"
    "2. Interpret the tool results and provide a concise, actionable summary.\n"
    "3. If an SLA breach is detected, proactively trigger an alert.\n\n"
    "You have access to four tools:\n"
    "- get_queue_health: Returns queue size, longest wait, service level %, "
    "and average handle time.\n"
    "- get_abandonment_analysis: Returns abandonment rate, peak hour, average "
    "wait before abandon, and total abandoned contacts.\n"
    "- get_agent_utilization: Returns per-agent occupancy rate, current status, "
    "average handle time, and contacts handled.\n"
    "- trigger_sla_alert: Publishes an SLA breach event to the alert pipeline.\n\n"
    "Stay within the supervisor domain. If a question is about sentiment analysis, "
    "compliance, staffing forecasts, or burnout signals, respond that it is outside "
    "your scope and suggest the appropriate agent (Quality or WFM)."
)

# ---------------------------------------------------------------------------
# Tool schema definitions
# ---------------------------------------------------------------------------
SUPERVISOR_TOOLS = [
    {
        "name": "get_queue_health",
        "description": (
            "Returns real-time queue health metrics including queue size, "
            "longest wait time in seconds, service level percentage, and "
            "average handle time. Optionally filter by queue name and time range."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "queue_name": {
                    "type": "string",
                    "description": "Name of the queue to check. Omit for all queues.",
                },
                "time_range": {
                    "type": "string",
                    "description": (
                        "Time range for the query, e.g. 'last_1h', 'last_24h', "
                        "'last_7d'. Defaults to 'last_1h'."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_abandonment_analysis",
        "description": (
            "Analyzes call abandonment patterns. Returns abandonment rate, "
            "peak abandonment hour, average wait time before abandon, and "
            "total abandoned contacts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "queue_name": {
                    "type": "string",
                    "description": "Queue to analyze. Omit for all queues.",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range, e.g. 'last_24h'. Defaults to 'last_24h'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_agent_utilization",
        "description": (
            "Returns per-agent utilization metrics: occupancy rate (0.0-1.0), "
            "current status (AVAILABLE, ON_CALL, AFTER_CONTACT_WORK, OFFLINE), "
            "average handle time, and contacts handled."
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
                    "description": "Time range, e.g. 'last_8h'. Defaults to 'last_8h'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "trigger_sla_alert",
        "description": (
            "Publishes an SLA breach alert event to EventBridge. Use when "
            "the current SLA percentage drops below the configured threshold."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "queue_name": {
                    "type": "string",
                    "description": "Queue experiencing the SLA breach.",
                },
                "current_sla_pct": {
                    "type": "number",
                    "description": "Current SLA percentage (e.g. 62.5).",
                },
                "threshold_pct": {
                    "type": "number",
                    "description": "Configured SLA threshold percentage (e.g. 80.0).",
                },
                "breach_timestamp": {
                    "type": "string",
                    "description": "ISO-8601 timestamp when the breach was detected.",
                },
            },
            "required": [
                "queue_name",
                "current_sla_pct",
                "threshold_pct",
                "breach_timestamp",
            ],
        },
    },
]


class SupervisorAgent(Construct):
    """CDK construct for the Supervisor Agent on Bedrock AgentCore.

    Creates:
    - An AgentCore Gateway (LAMBDA type) if *gateway_id* is not supplied.
    - The Supervisor Agent registered with the gateway and four tools.

    Parameters
    ----------
    scope : Construct
        CDK scope.
    id : str
        Construct ID.
    tool_lambda : lambda_.IFunction
        The Lambda function that handles all supervisor tool invocations.
    gateway_id : str | None
        If another agent already created the shared gateway, pass its ID
        here to skip gateway creation.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        tool_lambda: lambda_.IFunction,
        gateway_id: str | None = None,
    ) -> None:
        super().__init__(scope, id)

        # ------------------------------------------------------------------
        # IAM role for the AgentCore Gateway to invoke Lambda
        # ------------------------------------------------------------------
        self._gateway_role = iam.Role(
            self,
            "GatewayRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Allows AgentCore Gateway to invoke tool Lambda functions",
        )
        tool_lambda.grant_invoke(self._gateway_role)

        # ------------------------------------------------------------------
        # AgentCore Gateway (shared — create only if not passed in)
        # ------------------------------------------------------------------
        if gateway_id is None:
            self._gateway = CfnResource(
                self,
                "AgentCoreGateway",
                type="AWS::BedrockAgentCore::Gateway",
                properties={
                    "Name": "connect-analytics-gateway",
                    "Description": (
                        "Shared AgentCore Gateway routing tool invocations "
                        "from all Connect Analytics agents to Lambda."
                    ),
                    "GatewayType": "LAMBDA",
                    "LambdaArn": tool_lambda.function_arn,
                    "RoleArn": self._gateway_role.role_arn,
                },
            )
            self._gateway_id = self._gateway.ref
        else:
            self._gateway = None
            self._gateway_id = gateway_id

        # ------------------------------------------------------------------
        # IAM role for the Supervisor Agent
        # ------------------------------------------------------------------
        self._agent_role = iam.Role(
            self,
            "SupervisorAgentRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Execution role for the Supervisor AgentCore agent",
        )

        # ------------------------------------------------------------------
        # Supervisor Agent (CfnResource — no L2 construct yet)
        # ------------------------------------------------------------------
        self._agent = CfnResource(
            self,
            "SupervisorAgent",
            type="AWS::BedrockAgentCore::Agent",
            properties={
                "AgentName": "connect-supervisor-agent",
                "Description": (
                    "Supervisor Agent — monitors queue health, SLA breaches, "
                    "agent utilization, and abandonment patterns."
                ),
                "ModelId": SUPERVISOR_MODEL_ID,
                "Instruction": SUPERVISOR_SYSTEM_PROMPT,
                "GatewayId": self._gateway_id,
                "RoleArn": self._agent_role.role_arn,
                "Tools": [
                    {
                        "Name": tool["name"],
                        "Description": tool["description"],
                        "Parameters": tool["parameters"],
                    }
                    for tool in SUPERVISOR_TOOLS
                ],
            },
        )

    # ------------------------------------------------------------------
    # Public properties for cross-stack references
    # ------------------------------------------------------------------
    @property
    def agent_id(self) -> str:
        """Logical ID / Ref of the Supervisor Agent resource."""
        return self._agent.ref

    @property
    def gateway_id(self) -> str:
        """Logical ID / Ref of the AgentCore Gateway.

        Pass this to Quality and WFM agent constructs so they share the
        same gateway instead of creating new ones.
        """
        return self._gateway_id
