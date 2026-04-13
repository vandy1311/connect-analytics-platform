"""Unit tests for Supervisor Agent Lambda tools."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock boto3 before importing any modules that depend on it
sys.modules.setdefault("boto3", MagicMock())


# ---------------------------------------------------------------------------
# get_queue_health
# ---------------------------------------------------------------------------

class TestGetQueueHealth:
    """Tests for lambda_tools.supervisor.get_queue_health."""

    def _import_handler(self):
        from lambda_tools.supervisor.get_queue_health import handler
        return handler

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_returns_single_queue_result(self, mock_cb):
        mock_cb.call.return_value = [
            {
                "queue_name": "Sales",
                "queue_size": "42",
                "longest_wait_seconds": "180",
                "service_level_pct": "75.5",
                "avg_handle_time": "320.0",
            }
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_queue_health", "parameters": {"queue_name": "Sales"}},
            None,
        )
        assert result["result"]["queue_name"] == "Sales"
        assert result["result"]["queue_size"] == 42
        assert result["result"]["longest_wait_seconds"] == 180
        assert result["result"]["service_level_pct"] == 75.5
        assert result["result"]["avg_handle_time"] == 320.0

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_returns_empty_result_when_no_data(self, mock_cb):
        mock_cb.call.return_value = []
        handler = self._import_handler()
        result = handler(
            {"tool": "get_queue_health", "parameters": {}},
            None,
        )
        assert result["result"]["queue_size"] == 0
        assert result["result"]["service_level_pct"] == 100.0

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_returns_multiple_queues(self, mock_cb):
        mock_cb.call.return_value = [
            {"queue_name": "Sales", "queue_size": "10", "longest_wait_seconds": "60",
             "service_level_pct": "80.0", "avg_handle_time": "200.0"},
            {"queue_name": "Support", "queue_size": "20", "longest_wait_seconds": "120",
             "service_level_pct": "65.0", "avg_handle_time": "400.0"},
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_queue_health", "parameters": {}},
            None,
        )
        assert isinstance(result["result"], list)
        assert len(result["result"]) == 2

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_handles_circuit_open(self, mock_cb):
        from lambda_tools.shared.circuit_breaker import CircuitOpenError
        mock_cb.call.side_effect = CircuitOpenError(retry_after=15.0)
        handler = self._import_handler()
        result = handler(
            {"tool": "get_queue_health", "parameters": {}},
            None,
        )
        assert "error" in result
        assert "Retry after" in result["error"]

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_handles_generic_exception(self, mock_cb):
        mock_cb.call.side_effect = RuntimeError("Athena query failed: syntax error")
        handler = self._import_handler()
        result = handler(
            {"tool": "get_queue_health", "parameters": {}},
            None,
        )
        assert "error" in result
        assert "correlation_id" in result


# ---------------------------------------------------------------------------
# get_abandonment_analysis
# ---------------------------------------------------------------------------

class TestGetAbandonmentAnalysis:
    """Tests for lambda_tools.supervisor.get_abandonment_analysis."""

    def _import_handler(self):
        from lambda_tools.supervisor.get_abandonment_analysis import handler
        return handler

    @patch("lambda_tools.supervisor.get_abandonment_analysis._cb")
    def test_returns_abandonment_metrics(self, mock_cb):
        # First call: aggregation query; second call: peak hour query
        mock_cb.call.side_effect = [
            [{"total_contacts": "100", "total_abandoned": "15",
              "abandonment_rate": "15.0", "avg_wait_before_abandon": "45.5"}],
            [{"abandon_hour": "14", "abandon_count": "8"}],
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_abandonment_analysis", "parameters": {"time_range": "24h"}},
            None,
        )
        r = result["result"]
        assert r["abandonment_rate"] == 15.0
        assert r["peak_abandonment_hour"] == 14
        assert r["avg_wait_before_abandon"] == 45.5
        assert r["total_abandoned"] == 15

    @patch("lambda_tools.supervisor.get_abandonment_analysis._cb")
    def test_handles_no_peak_hour(self, mock_cb):
        mock_cb.call.side_effect = [
            [{"total_contacts": "0", "total_abandoned": "0",
              "abandonment_rate": "0", "avg_wait_before_abandon": "0"}],
            [],  # no peak hour data
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_abandonment_analysis", "parameters": {}},
            None,
        )
        assert result["result"]["peak_abandonment_hour"] is None

    @patch("lambda_tools.supervisor.get_abandonment_analysis._cb")
    def test_handles_circuit_open(self, mock_cb):
        from lambda_tools.shared.circuit_breaker import CircuitOpenError
        mock_cb.call.side_effect = CircuitOpenError(retry_after=10.0)
        handler = self._import_handler()
        result = handler(
            {"tool": "get_abandonment_analysis", "parameters": {}},
            None,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# get_agent_utilization
# ---------------------------------------------------------------------------

class TestGetAgentUtilization:
    """Tests for lambda_tools.supervisor.get_agent_utilization."""

    def _import_handler(self):
        from lambda_tools.supervisor.get_agent_utilization import handler
        return handler

    @patch("lambda_tools.supervisor.get_agent_utilization._cb")
    def test_returns_agent_list(self, mock_cb):
        mock_cb.call.return_value = [
            {"agent_id": "agent-001", "occupancy_rate": "0.85",
             "current_status": "ON_CALL", "avg_handle_time": "300.0",
             "contacts_handled": "25"},
            {"agent_id": "agent-002", "occupancy_rate": "0.45",
             "current_status": "AVAILABLE", "avg_handle_time": "250.0",
             "contacts_handled": "18"},
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_agent_utilization", "parameters": {}},
            None,
        )
        agents = result["result"]["agents"]
        assert len(agents) == 2
        assert agents[0]["agent_id"] == "agent-001"
        assert agents[0]["occupancy_rate"] == 0.85
        assert agents[0]["current_status"] == "ON_CALL"

    @patch("lambda_tools.supervisor.get_agent_utilization._cb")
    def test_clamps_occupancy_rate(self, mock_cb):
        mock_cb.call.return_value = [
            {"agent_id": "agent-003", "occupancy_rate": "1.5",
             "current_status": "ON_CALL", "avg_handle_time": "100.0",
             "contacts_handled": "5"},
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_agent_utilization", "parameters": {}},
            None,
        )
        assert result["result"]["agents"][0]["occupancy_rate"] == 1.0

    @patch("lambda_tools.supervisor.get_agent_utilization._cb")
    def test_normalizes_unknown_status(self, mock_cb):
        mock_cb.call.return_value = [
            {"agent_id": "agent-004", "occupancy_rate": "0.5",
             "current_status": "UNKNOWN_STATE", "avg_handle_time": "200.0",
             "contacts_handled": "10"},
        ]
        handler = self._import_handler()
        result = handler(
            {"tool": "get_agent_utilization", "parameters": {}},
            None,
        )
        assert result["result"]["agents"][0]["current_status"] == "OFFLINE"

    @patch("lambda_tools.supervisor.get_agent_utilization._cb")
    def test_empty_result(self, mock_cb):
        mock_cb.call.return_value = []
        handler = self._import_handler()
        result = handler(
            {"tool": "get_agent_utilization", "parameters": {}},
            None,
        )
        assert result["result"]["agents"] == []


# ---------------------------------------------------------------------------
# trigger_sla_alert
# ---------------------------------------------------------------------------

class TestTriggerSlaAlert:
    """Tests for lambda_tools.supervisor.trigger_sla_alert."""

    def _import_handler(self):
        from lambda_tools.supervisor.trigger_sla_alert import handler
        return handler

    @patch("lambda_tools.supervisor.trigger_sla_alert.publish_alert")
    def test_publishes_sla_breach(self, mock_publish):
        mock_publish.return_value = "alert-uuid-123"
        handler = self._import_handler()
        result = handler(
            {
                "tool": "trigger_sla_alert",
                "parameters": {
                    "queue_name": "Sales",
                    "current_sla_pct": 62.5,
                    "threshold_pct": 80.0,
                    "breach_timestamp": "2024-01-15T14:00:00Z",
                },
            },
            None,
        )
        assert result["result"]["alert_id"] == "alert-uuid-123"
        assert result["result"]["status"] == "published"
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][0] == "SLA_BREACH"

    def test_rejects_missing_params(self):
        handler = self._import_handler()
        result = handler(
            {"tool": "trigger_sla_alert", "parameters": {"queue_name": "Sales"}},
            None,
        )
        assert "error" in result
        assert "Missing required" in result["error"]

    @patch("lambda_tools.supervisor.trigger_sla_alert.publish_alert")
    def test_severity_high_when_well_below_threshold(self, mock_publish):
        mock_publish.return_value = "alert-uuid-456"
        handler = self._import_handler()
        handler(
            {
                "tool": "trigger_sla_alert",
                "parameters": {
                    "queue_name": "Support",
                    "current_sla_pct": 40.0,
                    "threshold_pct": 80.0,
                    "breach_timestamp": "2024-01-15T14:00:00Z",
                },
            },
            None,
        )
        payload = mock_publish.call_args[0][1]
        assert payload["severity"] == "HIGH"

    @patch("lambda_tools.supervisor.trigger_sla_alert.publish_alert")
    def test_severity_medium_when_near_threshold(self, mock_publish):
        mock_publish.return_value = "alert-uuid-789"
        handler = self._import_handler()
        handler(
            {
                "tool": "trigger_sla_alert",
                "parameters": {
                    "queue_name": "Support",
                    "current_sla_pct": 75.0,
                    "threshold_pct": 80.0,
                    "breach_timestamp": "2024-01-15T14:00:00Z",
                },
            },
            None,
        )
        payload = mock_publish.call_args[0][1]
        assert payload["severity"] == "MEDIUM"


class TestSlaThresholdLookup:
    """Tests for the get_threshold helper."""

    def test_returns_default_for_unknown_queue(self):
        from lambda_tools.supervisor.trigger_sla_alert import get_threshold
        config = get_threshold("NonExistentQueue")
        assert config["target_pct"] > 0
        assert config["window_seconds"] > 0

    def test_returns_per_queue_config_from_env(self):
        thresholds = json.dumps({
            "Sales": {"target_pct": 90, "window_seconds": 15},
            "default": {"target_pct": 80, "window_seconds": 20},
        })
        with patch.dict(os.environ, {"SLA_THRESHOLDS": thresholds}):
            # Force re-read from env
            from lambda_tools.supervisor.trigger_sla_alert import get_threshold
            config = get_threshold("Sales")
            assert config["target_pct"] == 90
            assert config["window_seconds"] == 15

    def test_falls_back_on_invalid_json(self):
        with patch.dict(os.environ, {"SLA_THRESHOLDS": "not-json"}):
            from lambda_tools.supervisor.trigger_sla_alert import get_threshold
            config = get_threshold("AnyQueue")
            assert config["target_pct"] > 0
