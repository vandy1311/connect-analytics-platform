"""Unit tests for lambda_tools.shared.alert_publisher."""

import json
import sys
import uuid
from unittest.mock import MagicMock, patch

# Mock boto3 before importing the module under test
_mock_boto3 = MagicMock()
sys.modules.setdefault("boto3", _mock_boto3)

from lambda_tools.shared.alert_publisher import publish_alert


@patch("lambda_tools.shared.alert_publisher._EVENTS")
class TestPublishAlert:
    """Tests for publish_alert with mocked EventBridge client."""

    def test_returns_valid_uuid(self, mock_events):
        alert_id = publish_alert("SLA_BREACH", {"severity": "HIGH"})
        uuid.UUID(alert_id)  # raises if invalid

    def test_calls_put_events(self, mock_events):
        publish_alert("SLA_BREACH", {"severity": "HIGH"})
        mock_events.put_events.assert_called_once()

    def test_event_has_correct_source(self, mock_events):
        publish_alert("SLA_BREACH", {"severity": "HIGH"})
        entry = mock_events.put_events.call_args[1]["Entries"][0]
        assert entry["Source"] == "connect-analytics"

    def test_event_has_correct_detail_type(self, mock_events):
        publish_alert("BURNOUT_RISK", {"severity": "MEDIUM"})
        entry = mock_events.put_events.call_args[1]["Entries"][0]
        assert entry["DetailType"] == "BURNOUT_RISK"

    def test_detail_contains_alert_id_and_timestamp(self, mock_events):
        alert_id = publish_alert("COMPLIANCE_VIOLATION", {"severity": "HIGH"})
        entry = mock_events.put_events.call_args[1]["Entries"][0]
        detail = json.loads(entry["Detail"])
        assert detail["alert_id"] == alert_id
        assert "timestamp" in detail
        assert detail["alert_type"] == "COMPLIANCE_VIOLATION"

    def test_severity_from_payload(self, mock_events):
        publish_alert("SLA_BREACH", {"severity": "LOW", "queue": "Sales"})
        entry = mock_events.put_events.call_args[1]["Entries"][0]
        detail = json.loads(entry["Detail"])
        assert detail["severity"] == "LOW"

    def test_default_severity_when_not_in_payload(self, mock_events):
        publish_alert("SLA_BREACH", {"queue": "Sales"})
        entry = mock_events.put_events.call_args[1]["Entries"][0]
        detail = json.loads(entry["Detail"])
        assert detail["severity"] == "MEDIUM"
