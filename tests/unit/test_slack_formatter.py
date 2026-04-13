"""Unit tests for lambda_tools.alerts.slack_formatter.handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from lambda_tools.alerts.slack_formatter.handler import (
    format_slack_message,
    handler,
    post_to_slack,
)


# ---------------------------------------------------------------------------
# format_slack_message tests
# ---------------------------------------------------------------------------
class TestFormatSlackMessage:
    """Tests for Slack Block Kit message formatting."""

    def _make_detail(self, alert_type="SLA_BREACH", severity="HIGH", **payload_fields):
        return {
            "alert_id": "abc-123",
            "alert_type": alert_type,
            "timestamp": "2024-06-15T14:00:00Z",
            "severity": severity,
            "payload": payload_fields,
        }

    def test_returns_blocks_key(self):
        msg = format_slack_message(self._make_detail())
        assert "blocks" in msg

    def test_has_header_and_section(self):
        msg = format_slack_message(self._make_detail())
        types = [b["type"] for b in msg["blocks"]]
        assert "header" in types
        assert "section" in types

    def test_header_contains_emoji_and_label(self):
        msg = format_slack_message(self._make_detail("SLA_BREACH"))
        header = msg["blocks"][0]
        assert "🚨" in header["text"]["text"]
        assert "SLA Breach" in header["text"]["text"]

    def test_section_contains_severity(self):
        msg = format_slack_message(self._make_detail(severity="HIGH"))
        section = msg["blocks"][1]
        assert "HIGH" in section["text"]["text"]

    def test_section_contains_timestamp(self):
        msg = format_slack_message(self._make_detail())
        section = msg["blocks"][1]
        assert "2024-06-15T14:00:00Z" in section["text"]["text"]

    # -- SLA_BREACH type-specific fields --
    def test_sla_breach_includes_queue_name(self):
        msg = format_slack_message(
            self._make_detail("SLA_BREACH", queue_name="Sales")
        )
        section = msg["blocks"][1]["text"]["text"]
        assert "Sales" in section

    def test_sla_breach_includes_sla_pct(self):
        msg = format_slack_message(
            self._make_detail("SLA_BREACH", current_sla_pct=62.5, threshold_pct=80.0)
        )
        section = msg["blocks"][1]["text"]["text"]
        assert "62.5" in section
        assert "80.0" in section

    # -- COMPLIANCE_VIOLATION type-specific fields --
    def test_compliance_violation_fields(self):
        msg = format_slack_message(
            self._make_detail(
                "COMPLIANCE_VIOLATION",
                violation_type="MISSING_DISCLOSURE",
                contact_id="c-123",
                agent_id="a-456",
            )
        )
        section = msg["blocks"][1]["text"]["text"]
        assert "MISSING_DISCLOSURE" in section
        assert "c-123" in section
        assert "a-456" in section

    # -- BURNOUT_RISK type-specific fields --
    def test_burnout_risk_fields(self):
        msg = format_slack_message(
            self._make_detail(
                "BURNOUT_RISK",
                agent_id="a-789",
                burnout_score=0.87,
                occupancy_rate=0.95,
            )
        )
        section = msg["blocks"][1]["text"]["text"]
        assert "a-789" in section
        assert "0.87" in section
        assert "0.95" in section

    # -- All 5 alert types produce valid blocks --
    @pytest.mark.parametrize(
        "alert_type",
        [
            "SLA_BREACH",
            "ABANDONMENT_SPIKE",
            "OCCUPANCY_CRITICAL",
            "COMPLIANCE_VIOLATION",
            "BURNOUT_RISK",
        ],
    )
    def test_all_alert_types_produce_valid_blocks(self, alert_type):
        msg = format_slack_message(self._make_detail(alert_type))
        assert len(msg["blocks"]) >= 2
        assert msg["blocks"][0]["type"] == "header"
        assert msg["blocks"][1]["type"] == "section"

    def test_unknown_alert_type_still_produces_blocks(self):
        msg = format_slack_message(self._make_detail("UNKNOWN_TYPE"))
        assert len(msg["blocks"]) >= 2


# ---------------------------------------------------------------------------
# post_to_slack tests
# ---------------------------------------------------------------------------
class TestPostToSlack:
    """Tests for Slack webhook POST with retry logic."""

    @patch("lambda_tools.alerts.slack_formatter.handler.urlopen")
    def test_success_on_first_attempt(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        post_to_slack("https://hooks.slack.com/test", {"blocks": []})
        assert mock_urlopen.call_count == 1

    @patch("lambda_tools.alerts.slack_formatter.handler.time.sleep")
    @patch("lambda_tools.alerts.slack_formatter.handler.urlopen")
    def test_retries_on_failure_then_succeeds(self, mock_urlopen, mock_sleep):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        # Fail twice, succeed on third
        mock_urlopen.side_effect = [
            Exception("timeout"),
            Exception("timeout"),
            mock_resp,
        ]

        post_to_slack("https://hooks.slack.com/test", {"blocks": []})
        assert mock_urlopen.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("lambda_tools.alerts.slack_formatter.handler.time.sleep")
    @patch("lambda_tools.alerts.slack_formatter.handler.urlopen")
    def test_raises_after_all_retries_exhausted(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = Exception("timeout")

        with pytest.raises(RuntimeError, match="failed after 3 retries"):
            post_to_slack("https://hooks.slack.com/test", {"blocks": []})

        assert mock_urlopen.call_count == 3
        assert mock_sleep.call_count == 3

    @patch("lambda_tools.alerts.slack_formatter.handler.time.sleep")
    @patch("lambda_tools.alerts.slack_formatter.handler.urlopen")
    def test_exponential_backoff_delays(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = Exception("timeout")

        with pytest.raises(RuntimeError):
            post_to_slack("https://hooks.slack.com/test", {"blocks": []})

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1, 2, 4]


# ---------------------------------------------------------------------------
# handler (Lambda entry point) tests
# ---------------------------------------------------------------------------
class TestHandler:
    """Tests for the Lambda handler processing SNS events."""

    def _make_sns_event(self, detail: dict) -> dict:
        return {
            "Records": [
                {
                    "Sns": {
                        "Message": json.dumps(detail),
                    }
                }
            ]
        }

    @patch("lambda_tools.alerts.slack_formatter.handler.post_to_slack")
    @patch.dict(
        "os.environ",
        {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/test", "ALERT_CHANNEL_MAP": "{}"},
    )
    def test_handler_calls_post_to_slack(self, mock_post):
        detail = {
            "alert_id": "abc",
            "alert_type": "SLA_BREACH",
            "timestamp": "2024-06-15T14:00:00Z",
            "severity": "HIGH",
            "payload": {"queue_name": "Sales"},
        }
        result = handler(self._make_sns_event(detail), None)
        assert result["statusCode"] == 200
        mock_post.assert_called_once()

    @patch("lambda_tools.alerts.slack_formatter.handler.post_to_slack")
    @patch.dict(
        "os.environ",
        {
            "SLACK_WEBHOOK_URL": "https://hooks.slack.com/test",
            "ALERT_CHANNEL_MAP": json.dumps({"SLA_BREACH": "#sla-channel"}),
        },
    )
    def test_handler_adds_channel_from_map(self, mock_post):
        detail = {
            "alert_id": "abc",
            "alert_type": "SLA_BREACH",
            "timestamp": "2024-06-15T14:00:00Z",
            "severity": "HIGH",
            "payload": {},
        }
        handler(self._make_sns_event(detail), None)
        message = mock_post.call_args[0][1]
        assert message["channel"] == "#sla-channel"

    @patch("lambda_tools.alerts.slack_formatter.handler.post_to_slack")
    @patch.dict(
        "os.environ",
        {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/test", "ALERT_CHANNEL_MAP": "{}"},
    )
    def test_handler_skips_invalid_json(self, mock_post):
        event = {"Records": [{"Sns": {"Message": "not-json"}}]}
        result = handler(event, None)
        assert result["statusCode"] == 200
        mock_post.assert_not_called()
