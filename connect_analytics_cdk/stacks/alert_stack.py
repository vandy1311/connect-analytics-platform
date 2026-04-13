"""Alert Pipeline stack: EventBridge rules, SNS topics, and Slack formatter Lambda.

Routes alert events from EventBridge to per-type SNS topics, then to a
shared Slack formatter Lambda that POSTs Block Kit messages to Slack.

Alert types
-----------
- SLA_BREACH
- ABANDONMENT_SPIKE
- OCCUPANCY_CRITICAL
- COMPLIANCE_VIOLATION
- BURNOUT_RISK

Each type gets its own EventBridge rule (matching on ``detail-type``) and
its own SNS topic, enabling per-type Slack channel routing.
"""

import json

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)
from constructs import Construct

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_EVENT_SOURCE = "connect-analytics"

_ALERT_TYPES: list[dict[str, str]] = [
    {"type": "SLA_BREACH", "topic": "sla-alerts"},
    {"type": "ABANDONMENT_SPIKE", "topic": "abandonment-alerts"},
    {"type": "OCCUPANCY_CRITICAL", "topic": "occupancy-alerts"},
    {"type": "COMPLIANCE_VIOLATION", "topic": "compliance-alerts"},
    {"type": "BURNOUT_RISK", "topic": "burnout-alerts"},
]

_DEFAULT_CHANNEL_MAP = {
    "SLA_BREACH": "#connect-sla-alerts",
    "ABANDONMENT_SPIKE": "#connect-sla-alerts",
    "OCCUPANCY_CRITICAL": "#connect-sla-alerts",
    "COMPLIANCE_VIOLATION": "#connect-compliance",
    "BURNOUT_RISK": "#connect-wfm-alerts",
}


class AlertStack(Stack):
    """EventBridge → SNS → Slack formatter Lambda for Connect Analytics alerts.

    Attributes:
        sns_topics: Mapping of alert type to its SNS topic.
        slack_lambda: The Slack formatter Lambda function.
        log_group: CloudWatch log group for alert failures.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        slack_webhook_url: str = "",
        alert_channel_map: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        channel_map = alert_channel_map or _DEFAULT_CHANNEL_MAP

        # ------------------------------------------------------------------
        # CloudWatch Log Group — alert failure logging
        # ------------------------------------------------------------------
        self.log_group = logs.LogGroup(
            self,
            "AlertLogGroup",
            log_group_name="/connect-analytics/alerts",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # ------------------------------------------------------------------
        # Slack Formatter Lambda (container image)
        # ------------------------------------------------------------------
        self.slack_lambda = lambda_.DockerImageFunction(
            self,
            "SlackFormatterLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "lambda_tools/alerts/slack_formatter",
            ),
            environment={
                "SLACK_WEBHOOK_URL": slack_webhook_url,
                "ALERT_CHANNEL_MAP": json.dumps(channel_map),
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=self.log_group,
            description="Formats alert payloads into Slack Block Kit and POSTs to webhook",
        )

        # ------------------------------------------------------------------
        # SNS Topics — one per alert type
        # ------------------------------------------------------------------
        self.sns_topics: dict[str, sns.Topic] = {}

        for alert_cfg in _ALERT_TYPES:
            alert_type = alert_cfg["type"]
            topic_name = alert_cfg["topic"]

            topic = sns.Topic(
                self,
                f"Topic-{alert_type}",
                topic_name=topic_name,
                display_name=f"Connect Analytics — {alert_type.replace('_', ' ').title()}",
            )

            # Subscribe the Slack formatter Lambda to every topic
            topic.add_subscription(subs.LambdaSubscription(self.slack_lambda))

            self.sns_topics[alert_type] = topic

        # ------------------------------------------------------------------
        # EventBridge Rules — one per alert type, targeting its SNS topic
        # ------------------------------------------------------------------
        for alert_cfg in _ALERT_TYPES:
            alert_type = alert_cfg["type"]
            topic = self.sns_topics[alert_type]

            events.Rule(
                self,
                f"Rule-{alert_type}",
                rule_name=f"connect-analytics-{alert_type.lower().replace('_', '-')}",
                description=f"Routes {alert_type} events to SNS topic {alert_cfg['topic']}",
                event_pattern=events.EventPattern(
                    source=[_EVENT_SOURCE],
                    detail_type=[alert_type],
                ),
                targets=[targets.SnsTopic(topic)],
            )
