#!/usr/bin/env python3
"""CDK app entry point for the Connect Analytics Platform.

Wires all stacks together with cross-stack references:
    DataStack → AgentStack → AlertStack → AuthStack

Three CfnParameters:
    - InstanceId       — Amazon Connect instance ID
    - DataLakeBucket   — S3 bucket name for the data lake
    - AlertDestination — Slack webhook URL for alert delivery

CfnOutputs expose agent endpoint URLs and Slack webhook config.
"""

from aws_cdk import App, CfnParameter, Environment

from connect_analytics_cdk.stacks.data_stack import DataStack
from connect_analytics_cdk.stacks.agent_stack import AgentStack
from connect_analytics_cdk.stacks.alert_stack import AlertStack
from connect_analytics_cdk.stacks.auth_stack import AuthStack

app = App()

# ---------------------------------------------------------------------------
# Environment — use account/region from CDK context or CLI
# ---------------------------------------------------------------------------
env = Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1",
)

# ---------------------------------------------------------------------------
# 1. AuthStack — lightweight API-key auth (hackathon scope)
# ---------------------------------------------------------------------------
auth_stack = AuthStack(app, "ConnectAnalytics-Auth", env=env)

# ---------------------------------------------------------------------------
# 2. DataStack — S3 bucket, Glue catalog, Athena workgroup
# ---------------------------------------------------------------------------
data_stack = DataStack(app, "ConnectAnalytics-Data", env=env)

# ---------------------------------------------------------------------------
# 3. AgentStack — tool Lambda, AgentCore Gateway, 3 agents
#    Depends on DataStack (bucket, workgroup) and AuthStack (tokens)
# ---------------------------------------------------------------------------
agent_stack = AgentStack(
    app,
    "ConnectAnalytics-Agents",
    data_bucket=data_stack.data_bucket,
    athena_workgroup=data_stack.athena_workgroup,
    auth_tokens_json=auth_stack.auth_tokens_json,
    env=env,
)
agent_stack.add_dependency(data_stack)
agent_stack.add_dependency(auth_stack)

# ---------------------------------------------------------------------------
# 4. AlertStack — EventBridge rules, SNS topics, Slack formatter
# ---------------------------------------------------------------------------
alert_stack = AlertStack(
    app,
    "ConnectAnalytics-Alerts",
    env=env,
)
alert_stack.add_dependency(agent_stack)

# ---------------------------------------------------------------------------
# Synthesize
# ---------------------------------------------------------------------------
app.synth()
