"""Shared Lambda handler — dispatches tool invocations by tool_name."""
import json
import logging
logger = logging.getLogger()
_TOOLS = {}
def _register():
    if _TOOLS:
        return
    from lambda_tools.supervisor.get_queue_health import handler as h1
    from lambda_tools.supervisor.get_abandonment_analysis import handler as h2
    from lambda_tools.supervisor.get_agent_utilization import handler as h3
    from lambda_tools.supervisor.trigger_sla_alert import handler as h4
    from lambda_tools.quality.get_sentiment_trends import handler as h5
    from lambda_tools.quality.get_coaching_recommendations import handler as h6
    from lambda_tools.quality.get_compliance_violations import handler as h7
    from lambda_tools.wfm.get_staffing_forecast import handler as h8
    from lambda_tools.wfm.get_burnout_signals import handler as h9
    _TOOLS.update({"get_queue_health":h1,"get_abandonment_analysis":h2,"get_agent_utilization":h3,"trigger_sla_alert":h4,"get_sentiment_trends":h5,"get_coaching_recommendations":h6,"get_compliance_violations":h7,"get_staffing_forecast":h8,"get_burnout_signals":h9})
def lambda_handler(event, context):
    _register()
    tool = event.get("tool_name","")
    if tool not in _TOOLS:
        return {"statusCode":400,"body":json.dumps({"error":f"Unknown tool: {tool}"})}
    try:
        return {"statusCode":200,"body":json.dumps(_TOOLS[tool](event.get("parameters",{})),default=str)}
    except Exception:
        logger.exception("Tool %s failed",tool)
        return {"statusCode":500,"body":json.dumps({"error":"Internal error"})}
