"""Agent stack: Tool handler Lambda, AgentCore Gateway, and all 3 agents.

Defines:
- Tool handler Lambda (DockerImageFunction from ``lambda_tools/``)
- SupervisorAgent (creates the shared AgentCore Gateway, exposes gateway_id)
- QualityAgent (references shared gateway)
- WfmAgent (references shared gateway)
- Least-privilege IAM: Athena, S3 read, EventBridge put, Nova Sonic invoke

Accepts ``data_bucket`` and ``athena_workgroup`` from DataStack as parameters.
"""

from __future__ import annotations

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_s3 as s3,
    aws_athena as athena,
)
from constructs import Construct

from connect_analytics_cdk.agents.supervisor_agent import SupervisorAgent
from connect_analytics_cdk.agents.quality_agent import QualityAgent
from connect_analytics_cdk.agents.wfm_agent import WfmAgent


class AgentStack(Stack):
    """AgentCore agents + tool handler Lambda for Connect Analytics.

    Parameters
    ----------
    data_bucket : s3.IBucket
        The S3 bucket holding Connect analytics data (from DataStack).
    athena_workgroup : athena.CfnWorkGroup
        The Athena workgroup for running queries (from DataStack).
    auth_tokens_json : str
        JSON-serialised auth token store for Lambda env vars.
    slack_webhook_url : str
        Slack webhook URL for alert delivery (passed through to env).

    Attributes
    ----------
    supervisor_agent : SupervisorAgent
        The Supervisor Agent construct (exposes ``gateway_id``).
    quality_agent : QualityAgent
        The Quality Agent construct.
    wfm_agent : WfmAgent
        The WFM Agent construct.
    tool_lambda : lambda_.DockerImageFunction
        The shared tool handler Lambda.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        data_bucket: s3.IBucket,
        athena_workgroup: athena.CfnWorkGroup,
        auth_tokens_json: str = "{}",
        slack_webhook_url: str = "",
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # ------------------------------------------------------------------
        # CloudWatch Log Group for agents
        # ------------------------------------------------------------------
        log_group = logs.LogGroup(
            self,
            "AgentLogGroup",
            log_group_name="/connect-analytics/agents",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ------------------------------------------------------------------
        # Tool handler Lambda (DockerImageFunction → ECR)
        # Single Lambda dispatches all 9 tools by tool_name
        # ------------------------------------------------------------------
        self.tool_lambda = lambda_.DockerImageFunction(
            self,
            "ToolHandler",
            code=lambda_.DockerImageCode.from_image_asset("lambda_tools"),
            environment={
                "BUCKET": data_bucket.bucket_name,
                "WORKGROUP": athena_workgroup.name or "connect-analytics",
                "AUTH_SECRET_ARN": auth_tokens_json,  # Secrets Manager ARN
            },
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=log_group,
            description=(
                "Shared tool handler for all Connect Analytics agent tools. "
                "Dispatches by tool_name to supervisor/quality/wfm handlers."
            ),
        )

        # ------------------------------------------------------------------
        # Least-privilege IAM for the tool Lambda
        # ------------------------------------------------------------------

        # S3 read-only on the data bucket
        data_bucket.grant_read(self.tool_lambda)

        # Secrets Manager read for auth tokens
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="SecretsManagerReadAuth",
                actions=["secretsmanager:GetSecretValue"],
                resources=[auth_tokens_json],  # Scoped to the specific secret ARN
            )
        )

        # Athena query execution — scoped to workgroup
        workgroup_name = athena_workgroup.name or "connect-analytics"
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="AthenaQueryExecution",
                actions=[
                    "athena:StartQueryExecution",
                    "athena:GetQueryExecution",
                    "athena:GetQueryResults",
                    "athena:StopQueryExecution",
                ],
                resources=[
                    f"arn:aws:athena:{self.region}:{self.account}:workgroup/{workgroup_name}",
                ],
            )
        )

        # Glue Data Catalog read — scoped to connect_analytics database
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="GlueCatalogRead",
                actions=[
                    "glue:GetDatabase",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:GetPartitions",
                ],
                resources=[
                    f"arn:aws:glue:{self.region}:{self.account}:catalog",
                    f"arn:aws:glue:{self.region}:{self.account}:database/connect_analytics",
                    f"arn:aws:glue:{self.region}:{self.account}:table/connect_analytics/*",
                ],
            )
        )

        # S3 write for Athena query results
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="AthenaResultsWrite",
                actions=["s3:PutObject", "s3:GetBucketLocation"],
                resources=[
                    data_bucket.bucket_arn,
                    f"{data_bucket.bucket_arn}/athena-results/*",
                ],
            )
        )

        # EventBridge put events — scoped to default event bus
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="EventBridgePutEvents",
                actions=["events:PutEvents"],
                resources=[
                    f"arn:aws:events:{self.region}:{self.account}:event-bus/default",
                ],
            )
        )

        # Nova Sonic invoke (for voice synthesis)
        self.tool_lambda.add_to_role_policy(
            iam.PolicyStatement(
                sid="NovaSonicInvoke",
                actions=["bedrock:InvokeModel"],
                resources=["arn:aws:bedrock:*::foundation-model/amazon.nova-sonic-v1:0"],
            )
        )

        # ------------------------------------------------------------------
        # Supervisor Agent (creates the shared AgentCore Gateway)
        # ------------------------------------------------------------------
        self.supervisor_agent = SupervisorAgent(
            self,
            "SupervisorAgent",
            tool_lambda=self.tool_lambda,
        )

        # ------------------------------------------------------------------
        # Quality Agent (references shared gateway)
        # ------------------------------------------------------------------
        self.quality_agent = QualityAgent(
            self,
            "QualityAgent",
            tool_lambda=self.tool_lambda,
            gateway_id=self.supervisor_agent.gateway_id,
        )

        # ------------------------------------------------------------------
        # WFM Agent (references shared gateway)
        # ------------------------------------------------------------------
        self.wfm_agent = WfmAgent(
            self,
            "WfmAgent",
            tool_lambda=self.tool_lambda,
            gateway_id=self.supervisor_agent.gateway_id,
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "GatewayId",
            value=self.supervisor_agent.gateway_id,
            description="Shared AgentCore Gateway ID",
        )
        CfnOutput(
            self,
            "SupervisorAgentId",
            value=self.supervisor_agent.agent_id,
            description="Supervisor Agent ID",
        )
        CfnOutput(
            self,
            "QualityAgentId",
            value=self.quality_agent.agent_id,
            description="Quality Agent ID",
        )
        CfnOutput(
            self,
            "WfmAgentId",
            value=self.wfm_agent.agent_id,
            description="WFM Agent ID",
        )
