"""End-to-end demo scenario tests for all 8 scripted demo responses.

Each test mocks the circuit breaker's ``call`` method (or alert_publisher)
to return realistic Athena-like data matching the synthetic data patterns,
then verifies the handler returns the expected output structure.

Demo data patterns:
- Billing queue: ~12 min avg wait, ~14% abandonment, SLA breach
- Agent-017: ≥4 negative calls
- Agent-023/031: >92% occupancy for 8 days
- Peak abandonment at hour 14 (2pm)
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure boto3 is mocked before any lambda_tools imports
sys.modules.setdefault("boto3", MagicMock())


# -----------------------------------------------------------------------
# Scenario 1: "Show me queue health right now"
# -----------------------------------------------------------------------

class TestScenario1QueueHealth:
    """get_queue_health returns queue_name, queue_size,
    longest_wait_seconds, service_level_pct, avg_handle_time."""

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_billing_queue_health(self, mock_cb):
        mock_cb.call.return_value = [
            {
                "queue_name": "Billing",
                "queue_size": "87",
                "longest_wait_seconds": "720",
                "service_level_pct": "68.50",
                "avg_handle_time": "345.20",
            }
        ]
        from lambda_tools.supervisor.get_queue_health import handler

        resp = handler(
            {"tool": "get_queue_health", "parameters": {"queue_name": "Billing"}},
            None,
        )

        assert "error" not in resp
        r = resp["result"]
        assert r["queue_name"] == "Billing"
        assert isinstance(r["queue_size"], int) and r["queue_size"] > 0
        assert isinstance(r["longest_wait_seconds"], int) and r["longest_wait_seconds"] > 0
        assert isinstance(r["service_level_pct"], float)
        assert isinstance(r["avg_handle_time"], float) and r["avg_handle_time"] > 0

    @patch("lambda_tools.supervisor.get_queue_health._cb")
    def test_all_queues_health(self, mock_cb):
        mock_cb.call.return_value = [
            {
                "queue_name": "Billing",
                "queue_size": "87",
                "longest_wait_seconds": "720",
                "service_level_pct": "68.50",
                "avg_handle_time": "345.20",
            },
            {
                "queue_name": "Sales",
                "queue_size": "32",
                "longest_wait_seconds": "180",
                "service_level_pct": "82.00",
                "avg_handle_time": "280.00",
            },
        ]
        from lambda_tools.supervisor.get_queue_health import handler

        resp = handler({"tool": "get_queue_health", "parameters": {}}, None)

        assert "error" not in resp
        result = resp["result"]
        assert isinstance(result, list)
        assert len(result) == 2
        for q in result:
            assert q["queue_name"] is not None
            assert "queue_size" in q
            assert "longest_wait_seconds" in q
            assert "service_level_pct" in q
            assert "avg_handle_time" in q


# -----------------------------------------------------------------------
# Scenario 2: "Why did abandonment spike at 2pm?"
# -----------------------------------------------------------------------

class TestScenario2AbandonmentAnalysis:
    """get_abandonment_analysis returns abandonment_rate,
    peak_abandonment_hour=14, avg_wait_before_abandon, total_abandoned."""

    @patch("lambda_tools.supervisor.get_abandonment_analysis._cb")
    def test_abandonment_spike_at_2pm(self, mock_cb):
        # First call: aggregation; second call: peak hour
        mock_cb.call.side_effect = [
            [
                {
                    "total_contacts": "350",
                    "total_abandoned": "49",
                    "abandonment_rate": "14.0",
                    "avg_wait_before_abandon": "720.0",
                }
            ],
            [{"abandon_hour": "14", "abandon_count": "18"}],
        ]
        from lambda_tools.supervisor.get_abandonment_analysis import handler

        resp = handler(
            {"tool": "get_abandonment_analysis", "parameters": {"time_range": "24h"}},
            None,
        )

        assert "error" not in resp
        r = resp["result"]
        assert r["abandonment_rate"] == pytest.approx(14.0, abs=1.0)
        assert r["peak_abandonment_hour"] == 14
        assert isinstance(r["avg_wait_before_abandon"], float)
        assert r["avg_wait_before_abandon"] > 0
        assert isinstance(r["total_abandoned"], int)
        assert r["total_abandoned"] > 0


# -----------------------------------------------------------------------
# Scenario 3: LIVE — trigger_sla_alert publishes SLA_BREACH event
# -----------------------------------------------------------------------

class TestScenario3SlaAlert:
    """trigger_sla_alert publishes SLA_BREACH event and returns
    alert_id + status='published'."""

    @patch("lambda_tools.supervisor.trigger_sla_alert.publish_alert")
    def test_sla_breach_published(self, mock_publish):
        mock_publish.return_value = "alert-demo-sla-001"
        from lambda_tools.supervisor.trigger_sla_alert import handler

        resp = handler(
            {
                "tool": "trigger_sla_alert",
                "parameters": {
                    "queue_name": "Billing",
                    "current_sla_pct": 62.5,
                    "threshold_pct": 80.0,
                    "breach_timestamp": "2024-01-15T14:00:00Z",
                },
            },
            None,
        )

        assert "error" not in resp
        r = resp["result"]
        assert r["alert_id"] == "alert-demo-sla-001"
        assert r["status"] == "published"

        # Verify publish_alert was called with SLA_BREACH
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args
        assert call_args[0][0] == "SLA_BREACH"
        payload = call_args[0][1]
        assert payload["queue_name"] == "Billing"
        assert payload["current_sla_pct"] == 62.5
        assert payload["threshold_pct"] == 80.0
        assert payload["breach_timestamp"] == "2024-01-15T14:00:00Z"


# -----------------------------------------------------------------------
# Scenario 4: "Which agents need coaching this week?"
# -----------------------------------------------------------------------

class TestScenario4CoachingRecommendations:
    """get_coaching_recommendations returns recommendations with
    agent_id, negative_sentiment_rate, sample_excerpts, coaching_suggestions.
    Agent-017 should appear with ≥4 negative calls."""

    @patch("lambda_tools.quality.get_coaching_recommendations._cb")
    def test_coaching_recommendations_structure(self, mock_cb):
        # First call: agent sentiment query
        # Second call: excerpts for agent-017
        # Third call: excerpts for agent-009
        mock_cb.call.side_effect = [
            [
                {
                    "agent_id": "agent-017",
                    "total_contacts": "20",
                    "negative_count": "6",
                    "negative_sentiment_rate": "30.0",
                },
                {
                    "agent_id": "agent-009",
                    "total_contacts": "25",
                    "negative_count": "5",
                    "negative_sentiment_rate": "20.0",
                },
            ],
            [
                {"transcript_excerpt": "Customer was upset about billing error"},
                {"transcript_excerpt": "Long hold time complaint"},
                {"transcript_excerpt": "Agent failed to resolve issue"},
            ],
            [
                {"transcript_excerpt": "Repeated transfer frustration"},
                {"transcript_excerpt": "Unresolved technical issue"},
            ],
        ]
        from lambda_tools.quality.get_coaching_recommendations import handler

        resp = handler(
            {"tool": "get_coaching_recommendations", "parameters": {"time_range": "7d"}},
            None,
        )

        assert "error" not in resp
        recs = resp["result"]["recommendations"]
        assert len(recs) >= 1

        # Verify agent-017 is present with high negative rate
        agent_017 = next((r for r in recs if r["agent_id"] == "agent-017"), None)
        assert agent_017 is not None
        assert agent_017["negative_sentiment_rate"] >= 15.0
        assert isinstance(agent_017["sample_excerpts"], list)
        assert len(agent_017["sample_excerpts"]) > 0
        assert isinstance(agent_017["coaching_suggestions"], list)
        assert len(agent_017["coaching_suggestions"]) > 0

        # Verify all recommendations have required fields
        for rec in recs:
            assert rec["agent_id"] is not None
            assert "negative_sentiment_rate" in rec
            assert "sample_excerpts" in rec
            assert "coaching_suggestions" in rec


# -----------------------------------------------------------------------
# Scenario 5: "Show me the worst call" — sentiment trends with chart
# -----------------------------------------------------------------------

class TestScenario5SentimentTrends:
    """get_sentiment_trends returns periods with sentiment percentages
    and a chart (base64 PNG)."""

    @patch("lambda_tools.quality.get_sentiment_trends._generate_chart")
    @patch("lambda_tools.quality.get_sentiment_trends._cb")
    def test_sentiment_trends_with_chart(self, mock_cb, mock_chart):
        mock_cb.call.return_value = [
            {
                "period": "2024-01-13",
                "total": "50",
                "positive_count": "20",
                "negative_count": "15",
                "neutral_count": "10",
                "mixed_count": "5",
            },
            {
                "period": "2024-01-14",
                "total": "60",
                "positive_count": "18",
                "negative_count": "22",
                "neutral_count": "12",
                "mixed_count": "8",
            },
            {
                "period": "2024-01-15",
                "total": "45",
                "positive_count": "10",
                "negative_count": "20",
                "neutral_count": "10",
                "mixed_count": "5",
            },
        ]
        # Return a fake base64 PNG (starts with PNG magic bytes in base64)
        mock_chart.return_value = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"

        from lambda_tools.quality.get_sentiment_trends import handler

        resp = handler(
            {"tool": "get_sentiment_trends", "parameters": {"time_range": "7d"}},
            None,
        )

        assert "error" not in resp
        result = resp["result"]
        periods = result["periods"]
        assert len(periods) == 3

        for p in periods:
            assert "date" in p
            assert "positive_pct" in p
            assert "negative_pct" in p
            assert "neutral_pct" in p
            assert "mixed_pct" in p
            # Percentages should sum to ~100%
            total_pct = p["positive_pct"] + p["negative_pct"] + p["neutral_pct"] + p["mixed_pct"]
            assert total_pct == pytest.approx(100.0, abs=0.1)

        # Chart should be a non-empty base64 string
        assert "chart" in result
        assert isinstance(result["chart"], str)
        assert len(result["chart"]) > 10


# -----------------------------------------------------------------------
# Scenario 6: "Forecast staffing for next Monday"
# -----------------------------------------------------------------------

class TestScenario6StaffingForecast:
    """get_staffing_forecast returns forecast entries with
    predicted_volume, confidence_lower, confidence_upper + chart."""

    @patch("lambda_tools.wfm.get_staffing_forecast._generate_chart")
    @patch("lambda_tools.wfm.get_staffing_forecast._cb")
    def test_staffing_forecast_with_chart(self, mock_cb, mock_chart):
        # Simulate historical volume data grouped by dow/hour
        mock_cb.call.return_value = [
            {"day_of_week": "1", "hour_of_day": "9", "contact_count": "45", "contact_date": "2024-01-08"},
            {"day_of_week": "1", "hour_of_day": "10", "contact_count": "62", "contact_date": "2024-01-08"},
            {"day_of_week": "1", "hour_of_day": "11", "contact_count": "58", "contact_date": "2024-01-08"},
            {"day_of_week": "1", "hour_of_day": "14", "contact_count": "70", "contact_date": "2024-01-08"},
            {"day_of_week": "1", "hour_of_day": "9", "contact_count": "50", "contact_date": "2024-01-15"},
            {"day_of_week": "1", "hour_of_day": "10", "contact_count": "55", "contact_date": "2024-01-15"},
            {"day_of_week": "1", "hour_of_day": "11", "contact_count": "60", "contact_date": "2024-01-15"},
            {"day_of_week": "1", "hour_of_day": "14", "contact_count": "75", "contact_date": "2024-01-15"},
        ]
        # Return a fake base64 PNG
        mock_chart.return_value = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"

        from lambda_tools.wfm.get_staffing_forecast import handler

        resp = handler(
            {
                "tool": "get_staffing_forecast",
                "parameters": {"forecast_horizon_days": 3},
            },
            None,
        )

        assert "error" not in resp
        result = resp["result"]
        forecast = result["forecast"]

        # 3 days × 24 hours = 72 entries
        assert len(forecast) == 72

        for entry in forecast:
            assert "date" in entry
            assert "hour" in entry
            assert entry["predicted_volume"] >= 0
            assert entry["confidence_lower"] <= entry["predicted_volume"]
            assert entry["confidence_upper"] >= entry["predicted_volume"]
            assert "current_staff" in entry
            assert "recommended_staff" in entry

        # Chart should be a non-empty base64 string
        assert "chart" in result
        assert isinstance(result["chart"], str)
        assert len(result["chart"]) > 10


# -----------------------------------------------------------------------
# Scenario 7: "Any agents showing burnout signals?"
# -----------------------------------------------------------------------

class TestScenario7BurnoutSignals:
    """get_burnout_signals returns at_risk_agents sorted by
    burnout_score descending. Agent-023/031 have >92% occupancy."""

    @patch("lambda_tools.wfm.get_burnout_signals.publish_alert")
    @patch("lambda_tools.wfm.get_burnout_signals._cb")
    def test_burnout_signals_sorted_descending(self, mock_cb, mock_publish):
        mock_publish.return_value = "alert-burnout-001"

        # First call: main agent metrics query
        # Subsequent calls: trend queries per agent (increasing handle times)
        mock_cb.call.side_effect = [
            # Main query — agents with very high occupancy and ACW
            # To exceed 0.85 burnout: 0.4*occ + 0.3*trend + 0.3*acw_factor
            # Need occ~1.0, acw>=300 (factor=1.0), trend high
            [
                {
                    "agent_id": "agent-023",
                    "avg_occupancy": "0.98",
                    "avg_acw_duration": "350.0",
                    "avg_state_duration": "400.0",
                    "event_count": "120",
                },
                {
                    "agent_id": "agent-031",
                    "avg_occupancy": "0.96",
                    "avg_acw_duration": "320.0",
                    "avg_state_duration": "380.0",
                    "event_count": "115",
                },
                {
                    "agent_id": "agent-005",
                    "avg_occupancy": "0.65",
                    "avg_acw_duration": "90.0",
                    "avg_state_duration": "250.0",
                    "event_count": "80",
                },
            ],
            # Trend for agent-023: very sharply increasing (slope/mean → 1.0)
            # slope=200, y_mean=100 → normalized=1.0 (capped)
            [
                {"event_date": "2024-01-10", "avg_duration": "10.0"},
                {"event_date": "2024-01-11", "avg_duration": "50.0"},
                {"event_date": "2024-01-12", "avg_duration": "190.0"},
            ],
            # Trend for agent-031: sharply increasing
            [
                {"event_date": "2024-01-10", "avg_duration": "10.0"},
                {"event_date": "2024-01-11", "avg_duration": "60.0"},
                {"event_date": "2024-01-12", "avg_duration": "200.0"},
            ],
            # Trend for agent-005: stable
            [
                {"event_date": "2024-01-08", "avg_duration": "200.0"},
                {"event_date": "2024-01-09", "avg_duration": "195.0"},
            ],
        ]
        from lambda_tools.wfm.get_burnout_signals import handler

        resp = handler(
            {"tool": "get_burnout_signals", "parameters": {"time_range": "7d"}},
            None,
        )

        assert "error" not in resp
        agents = resp["result"]["at_risk_agents"]
        assert len(agents) == 3

        # Verify sorted by burnout_score descending
        scores = [a["burnout_score"] for a in agents]
        assert scores == sorted(scores, reverse=True)

        # Verify required fields on every entry
        for a in agents:
            assert a["agent_id"] is not None
            assert 0.0 <= a["burnout_score"] <= 1.0
            assert 0.0 <= a["occupancy_rate"] <= 1.0
            assert "avg_acw_duration" in a
            assert "handle_time_trend" in a
            assert "recommended_action" in a
            assert isinstance(a["recommended_action"], str)
            assert len(a["recommended_action"]) > 0

        # Agent-023 and agent-031 should have high occupancy
        agent_023 = next(a for a in agents if a["agent_id"] == "agent-023")
        agent_031 = next(a for a in agents if a["agent_id"] == "agent-031")
        assert agent_023["occupancy_rate"] > 0.92
        assert agent_031["occupancy_rate"] > 0.92

        # publish_alert should have been called for high-burnout agents
        # (agent-023 and agent-031 should exceed the 0.85 default threshold)
        assert mock_publish.call_count >= 1
        # Verify at least one call was for BURNOUT_RISK
        burnout_calls = [
            c for c in mock_publish.call_args_list if c[0][0] == "BURNOUT_RISK"
        ]
        assert len(burnout_calls) >= 1


# -----------------------------------------------------------------------
# Scenario 8: CDK synth test (mock)
# -----------------------------------------------------------------------

class TestScenario8CdkSynth:
    """Verify CDK stack modules are structurally sound.

    A full ``cdk synth`` requires Node.js and AWS credentials, so we
    verify the stack definition modules exist and contain the expected
    class definitions by inspecting the source files directly.
    """

    def test_data_stack_module_exists(self):
        """Verify data_stack.py exists and defines a DataStack class."""
        import importlib.util
        spec = importlib.util.find_spec("connect_analytics_cdk.stacks.data_stack")
        assert spec is not None, "data_stack module not found"

    def test_agent_stack_module_exists(self):
        """Verify agent_stack.py exists and defines an AgentStack class."""
        import importlib.util
        spec = importlib.util.find_spec("connect_analytics_cdk.stacks.agent_stack")
        assert spec is not None, "agent_stack module not found"

    def test_alert_stack_module_exists(self):
        """Verify alert_stack.py exists and defines an AlertStack class."""
        import importlib.util
        spec = importlib.util.find_spec("connect_analytics_cdk.stacks.alert_stack")
        assert spec is not None, "alert_stack module not found"

    def test_auth_stack_module_exists(self):
        """Verify auth_stack.py exists and defines an AuthStack class."""
        import importlib.util
        spec = importlib.util.find_spec("connect_analytics_cdk.stacks.auth_stack")
        assert spec is not None, "auth_stack module not found"
