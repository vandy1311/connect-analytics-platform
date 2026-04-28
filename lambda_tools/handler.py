"""Shared Lambda handler — dispatches tool invocations by tool_name.

This is the single entry point for all 9 agent tools. The AgentCore Gateway
invokes this Lambda with a payload containing tool_name and parameters.
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Tool registry — maps tool_name to handler function
_TOOLS = {}


def _register_tools():
    """Lazy-load all tool modules and register their handlers."""
    if _TOOLS:
        return

    from lambda_tools.supervisor.get_queue_health import handler as queue_health
    from lambda_tools.supervisor.get_abandonment_analysis import handler as abandonment
    from lambda_tools.supervisor.get_agent_utilization import handler as utilization
    from lambda_tools.supervisor.trigger_sla_alert import handler as sla_alert
    from lambda_tools.quality.get_sentiment_trends import handler as sentiment
    from lambda_tools.quality.get_coaching_recommendations import handler as coaching
    from lambda_tools.quality.get_compliance_violations import handler as compliance
    from lambda_tools.wfm.get_staffing_forecast import handler as forecast
    from lambda_tools.wfm.get_burnout_signals import handler as burnout

    _TOOLS.update({
        "get_queue_health": queue_health,
        "get_abandonment_analysis": abandonment,
        "get_agent_utilization": utilization,
        "trigger_sla_alert": sla_alert,
        "get_sentiment_trends": sentiment,
        "get_coaching_recommendations": coaching,
        "get_compliance_violations": compliance,
        "get_staffing_forecast": forecast,
        "get_burnout_signals": burnout,
    })


def lambda_handler(event, context):
    """Main Lambda handler — routes by tool_name."""
    _register_tools()

    tool_name = event.get("tool_name", "")
    parameters = event.get("parameters", {})

    logger.info("Dispatching tool: %s", tool_name)

    if tool_name not in _TOOLS:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown tool: {tool_name}"}),
        }

    try:
        result = _TOOLS[tool_name](parameters)
        return {
            "statusCode": 200,
            "body": json.dumps(result, default=str),
        }
    except Exception as e:
        logger.exception("Tool %s failed", tool_name)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal error", "tool": tool_name}),
        }
