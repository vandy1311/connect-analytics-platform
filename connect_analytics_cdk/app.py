#!/usr/bin/env python3
"""CDK app entry point for the Connect Analytics Platform.

Wires all stacks together with cross-stack references:
    AuthStack → DataStack → KnowledgeBaseStack → AgentStack → AlertStack
"""

from aws_cdk import App, Environment

from connect_analytics_cdk.stacks.data_stack import DataStack
from connect_analytics_cdk.stacks.agent_stack import AgentStack
from connect_analytics_cdk.stacks.alert_stack import AlertStack
from connect_analytics_cdk.stacks.auth_stack import AuthStack
from connect_analytics_cdk.stacks.knowledge_base_stack import KnowledgeBaseStack

app = App()

# ---------------------------------------------------------------------------
# Environment — use account/region from CDK context or CLI
# ---------------------------------------------------------------------------
env = Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region") or "us-east-1",
)

# ---------------------------------------------------------------------------
# 1. AuthStack — tokens in Secrets Manager, role-agent mapping
# ---------------------------------------------------------------------------
auth_stack = AuthStack(app, "ConnectAnalytics-Auth", env=env)

# ---------------------------------------------------------------------------
# 2. DataStack — S3 bucket, Glue catalog, Athena workgroup
# ---------------------------------------------------------------------------
data_stack = DataStack(app, "ConnectAnalytics-Data", env=env)

# ---------------------------------------------------------------------------
# 3. KnowledgeBaseStack — S3 docs + Bedrock Knowledge Base for RAG
# ---------------------------------------------------------------------------
kb_stack = KnowledgeBaseStack(app, "ConnectAnalytics-KB", env=env)
kb_stack.add_dependency(data_stack)

# ---------------------------------------------------------------------------
# 4. AgentStack — tool Lambda, AgentCore Gateway, 3 agents
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
agent_stack.add_dependency(kb_stack)

# ---------------------------------------------------------------------------
# 5. AlertStack — EventBridge rules, SNS topics, Slack formatter
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
