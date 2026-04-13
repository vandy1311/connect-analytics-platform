# Component Interaction Flows — Connect Analytics Platform

## Flow 1: Natural Language Query → Agent Response

```
1. User submits: "Show me queue health right now"
2. NLQ Interface receives query + auth token
3. Auth middleware validates token → extracts role (supervisor)
4. RBAC check: supervisor → Supervisor Agent ✓
5. AgentCore Gateway routes to Supervisor Agent
6. Agent (Claude Sonnet) reasons about query → decides to call get_queue_health
7. Gateway invokes Lambda: get_queue_health(queue_name="ALL", time_range="60min")
8. Lambda builds Athena SQL:
   SELECT queue_name, COUNT(*) as queue_size,
          MAX(queue_duration_seconds) as longest_wait,
          AVG(CASE WHEN service_level_met THEN 1.0 ELSE 0.0 END) * 100 as sla_pct
   FROM connect_ctr WHERE ...
9. Athena executes against S3 (Parquet scan)
10. Lambda returns structured JSON to Gateway
11. Agent summarizes: "Billing queue at 12 min avg wait — SLA breach..."
12. Agent detects SLA breach → calls trigger_sla_alert
13. Gateway invokes Lambda: trigger_sla_alert(queue="Billing", sla=62.5, threshold=80)
14. Lambda publishes EventBridge event (SLA_BREACH)
15. Agent returns final text response to user
16. If voice=true: Polly synthesizes MP3, returned alongside text
```

## Flow 2: SLA Breach Alert → Slack

```
1. trigger_sla_alert Lambda publishes to EventBridge:
   {
     "source": "connect-analytics",
     "detail-type": "SLA_BREACH",
     "detail": {
       "queue_name": "Billing",
       "current_sla_pct": 62.5,
       "threshold_pct": 80.0,
       "breach_timestamp": "2026-03-18T14:02:00Z"
     }
   }

2. EventBridge rule matches detail-type = "SLA_BREACH"
3. Rule target: SNS topic "sla-alerts"
4. SNS delivers to Slack formatter Lambda (HTTPS subscription)
5. Slack formatter builds Block Kit message:
   ⚠️ SLA Breach — Billing Queue
   Current: 62.5% | Threshold: 80.0%
   Time: 2026-03-18 14:02 UTC
6. Lambda POSTs to Slack webhook URL
7. Message appears in #connect-sla-alerts channel

   If POST fails:
   8. SNS retries (3x exponential backoff)
   9. Failure logged to CloudWatch
```

## Flow 3: Sentiment Analysis with Chart

```
1. QA analyst: "Show me sentiment trends this week"
2. Auth: qa_analyst → Quality Agent ✓
3. Quality Agent calls get_sentiment_trends(time_range="7d")
4. Lambda queries Athena:
   SELECT DATE(analysis_timestamp) as date,
          COUNT(CASE WHEN overall_sentiment='POSITIVE' THEN 1 END) * 100.0 / COUNT(*),
          COUNT(CASE WHEN overall_sentiment='NEGATIVE' THEN 1 END) * 100.0 / COUNT(*),
          ...
   FROM connect_contact_lens WHERE ...
5. Lambda receives aggregated results
6. Lambda generates matplotlib chart:
   - Line chart: sentiment % by day
   - Colors: green (positive), red (negative), gray (neutral), orange (mixed)
7. Chart saved as PNG → base64 encoded
8. Lambda returns { periods: [...], chart: "iVBORw0KGgo..." }
9. Agent summarizes trends + includes chart in response
```

## Flow 4: Burnout Detection with Alert

```
1. WFM planner: "Any agents showing burnout signals?"
2. Auth: wfm_planner → WFM Agent ✓
3. WFM Agent (Nova Lite) calls get_burnout_signals(threshold=0.85)
4. Lambda queries Athena for agent event patterns:
   - Occupancy rate > 92% for 7+ consecutive days
   - Rising handle times over consecutive shifts
   - Extended ACW durations
5. Lambda calculates burnout_score (0.0–1.0) per agent:
   score = 0.4 * occupancy_factor + 0.3 * handle_time_trend + 0.3 * acw_factor
6. Results sorted by burnout_score descending
7. Agent-023 (score: 0.91) and Agent-031 (score: 0.88) exceed threshold
8. Lambda publishes BURNOUT_RISK events to EventBridge for both
9. Lambda returns ranked list with recommended actions
10. Agent summarizes: "Agent-023 and Agent-031: occupancy above 92% for 8 days..."
```

## Flow 5: CDK Deployment

```
1. Developer runs: cdk deploy --parameters InstanceId=xxx DataLakeBucket=yyy AlertDestination=zzz

2. CDK synthesizes CloudFormation template (~8 min total):

   Phase 1 — Docker builds (~3 min):
   ├── docker build lambda/tools/     → ECR push (tool handler image)
   └── docker build lambda/generator/ → ECR push (synthetic data gen image)

   Phase 2 — CloudFormation deploy (~5 min):
   ├── DataStack:
   │   ├── S3 bucket reference (import existing)
   │   ├── Glue database + 3 tables
   │   └── Athena workgroup
   ├── AuthStack:
   │   └── API key auth (hackathon) or Cognito (production)
   ├── AgentStack:
   │   ├── IAM roles (least privilege)
   │   ├── AgentCore Gateway
   │   ├── 9 Lambda container functions
   │   └── 3 AgentCore agents
   └── AlertStack:
       ├── EventBridge rules (5)
       ├── SNS topics (5)
       ├── Slack formatter Lambda
       └── CloudWatch log group

   Phase 3 — Post-deploy:
   └── Synthetic data generator Lambda runs once (custom resource trigger)
       └── Generates 70,000 records → S3

3. CDK outputs:
   ├── SupervisorAgentEndpoint: https://...
   ├── QualityAgentEndpoint: https://...
   ├── WFMAgentEndpoint: https://...
   └── SlackWebhookConfigParam: /connect-analytics/slack-webhook
```

## Flow 6: Error Handling — Athena Failure

```
1. User: "Show me queue health for the last year"
2. Agent calls get_queue_health(time_range="365d")
3. Lambda builds Athena SQL (large scan)
4. Athena query exceeds 30s timeout

   Circuit breaker check:
   ├── If CLOSED: increment failure counter
   │   ├── If failures < 5 in 60s: return timeout error
   │   └── If failures >= 5 in 60s: OPEN circuit
   ├── If OPEN: skip Athena, return "service degraded" immediately
   └── If HALF-OPEN (after 30s): allow one probe query

5. Error handler sanitizes response:
   ✗ "AthenaQueryTimeoutException: SELECT queue_name FROM connect_ctr..."
   ✓ "The query took too long. Try narrowing the time range."
   + correlation_id: "abc-123-def"

6. Agent returns user-friendly message
```

## Flow 7: RBAC Denial

```
1. User with role=supervisor submits: "Show me sentiment trends"
2. Auth middleware validates token ✓
3. Intent classification: sentiment → Quality Agent
4. RBAC check: supervisor → Quality Agent ✗ DENIED
5. Log unauthorized access:
   {
     "event": "UNAUTHORIZED_ACCESS",
     "user_id": "user-456",
     "role": "supervisor",
     "attempted_agent": "quality",
     "timestamp": "2026-03-18T14:30:00Z"
   }
6. Return 403: "You do not have access to this agent. Contact your administrator."
```
