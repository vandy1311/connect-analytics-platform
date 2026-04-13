# Shared utility modules used across all Lambda tools
#
# Modules are imported individually by consumers rather than re-exported here,
# because some modules (athena_client, alert_publisher) depend on boto3 which
# is only available in the Lambda runtime environment.
#
# Usage:
#   from lambda_tools.shared.athena_client import execute_query
#   from lambda_tools.shared.error_handler import sanitize_error
#   from lambda_tools.shared.circuit_breaker import CircuitBreaker, CircuitOpenError
#   from lambda_tools.shared.alert_publisher import publish_alert
