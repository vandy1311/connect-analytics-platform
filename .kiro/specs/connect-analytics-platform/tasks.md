# Implementation Plan: Connect Analytics Platform

## Overview

Build an Amazon Connect Analytics Platform with three Bedrock AgentCore AI agents (Supervisor, Quality, WFM), a shared data lake (S3 + Glue + Athena), an alert pipeline (EventBridge → SNS → Slack), Polly voice output, and CDK infrastructure — all in Python. Tasks follow the team's build order: Data Foundation → Supervisor Agent → Alerts → Quality + WFM Agents → Polly → CDK → Demo Dry-Run.

## Tasks

- [x] 1. Data Foundation — S3, Glue Catalog, Athena, and Synthetic Data
  - [x] 1.1 Create the synthetic data generator script
    - Create `scripts/generate_synthetic_data.py` using faker + numpy
    - Generate 10,000 CTR records (Parquet, partitioned year/month/day) with fields: contact_id, queue_name, agent_id, initiation_timestamp, connected_timestamp, disconnect_timestamp, queue_duration_seconds, handle_time_seconds, outcome, service_level_met
    - Generate 50,000 Agent Event records (Parquet, partitioned year/month/day) with fields: event_id, agent_id, agent_name, event_type, current_state, state_start_timestamp, state_duration_seconds, contacts_handled_today, occupancy_rate
    - Generate 10,000 Contact Lens records (JSON, partitioned year/month/day) with fields: contact_id, agent_id, overall_sentiment, customer_sentiment_score, agent_sentiment_score, categories, transcript_excerpt, compliance_flags, analysis_timestamp
    - Embed reproducible demo patterns: SLA breaches at 2pm, negative sentiment spikes on Mondays, burnout signals for 3 specific agent IDs
    - Use deterministic seed for reproducible output
    - _Requirements: 8.1, 2.1, 4.1, 7.1_

  - [x] 1.2 Create Glue Data Catalog table definitions module
    - Create `connect_analytics_cdk/glue_tables.py` with CDK L2 constructs for `connect_ctr`, `connect_agent_events`, `connect_contact_lens` tables
    - Define schemas matching the data models in the design doc (Parquet for CTR/Agent Events, JSON for Contact Lens)
    - Configure partition keys (year, month, day) and partition projection for automatic partition discovery
    - _Requirements: 8.1, 8.3_

  - [x] 1.3 Create the data stack (S3 + Glue + Athena)
    - Create `connect_analytics_cdk/stacks/data_stack.py`
    - Define S3 bucket `connect-analytics-demo` with prefix structure: `ctr/`, `agent-events/`, `contact-lens/`
    - Define Glue database `connect_analytics` and reference the table definitions from 1.2
    - Define Athena workgroup `connect-analytics` with query result location in S3
    - _Requirements: 8.1, 8.2_

  - [ ]* 1.4 Write property tests for synthetic data generator
    - **Property 9: Sentiment aggregation percentages sum to 100%**
    - Verify generated Contact Lens records have sentiment distributions that sum correctly
    - **Validates: Requirements 4.1**

  - [ ]* 1.5 Write unit tests for Glue table schemas
    - Verify each table definition has all required columns and correct types per design doc
    - Verify partition keys are correctly defined
    - _Requirements: 8.1_

- [ ] 2. Checkpoint — Data foundation validated
  - Ensure all tests pass, ask the user if questions arise.
  - Run synthetic data generator and verify output files exist with correct structure
  - Verify CDK synth produces data stack without errors

- [x] 3. Supervisor Agent — AgentCore Gateway and First Agent
  - [x] 3.1 Create shared utility modules
    - Create `lambda_tools/shared/athena_client.py` — wrapper around boto3 Athena client with query execution, result polling, and timeout handling (30s)
    - Create `lambda_tools/shared/error_handler.py` — error sanitization that strips SQL, table names, stack traces, ARNs; adds correlation ID
    - Create `lambda_tools/shared/circuit_breaker.py` — in-memory circuit breaker (closed→open after 5 failures in 60s, half-open after 30s cooldown)
    - Create `lambda_tools/shared/alert_publisher.py` — EventBridge PutEvents wrapper with standard event schema
    - _Requirements: 1.5, 8.4_

  - [ ]* 3.2 Write property tests for error handler
    - **Property 3: Error messages never expose raw SQL or stack traces**
    - Generate random error strings containing SQL keywords, table names, Python tracebacks; verify sanitized output contains none
    - **Validates: Requirements 1.5, 8.4**

  - [x] 3.3 Implement `get_queue_health` Lambda tool
    - Create `lambda_tools/supervisor/get_queue_health/handler.py`
    - Accept input `{ queue_name?: str, time_range?: str }`
    - Build Athena SQL against `connect_ctr` + `connect_agent_events`
    - Return `{ queue_name, queue_size, longest_wait_seconds, service_level_pct, avg_handle_time }`
    - Use shared athena_client and error_handler
    - Create `lambda_tools/supervisor/get_queue_health/Dockerfile` for container image build
    - _Requirements: 2.1_

  - [ ]* 3.4 Write property test for queue health response
    - **Property 4: Queue health response contains all required fields**
    - Generate random Athena result sets; verify output always contains non-null queue_name, queue_size, longest_wait_seconds, service_level_pct
    - **Validates: Requirements 2.1**

  - [x] 3.5 Implement `get_abandonment_analysis` Lambda tool
    - Create `lambda_tools/supervisor/get_abandonment_analysis/handler.py`
    - Accept input `{ queue_name?: str, time_range?: str }`
    - Query `connect_ctr` for abandonment metrics
    - Return `{ abandonment_rate, peak_abandonment_hour, avg_wait_before_abandon, total_abandoned }`
    - _Requirements: 2.1_

  - [x] 3.6 Implement `get_agent_utilization` Lambda tool
    - Create `lambda_tools/supervisor/get_agent_utilization/handler.py`
    - Accept input `{ agent_id?: str, time_range?: str }`
    - Query `connect_agent_events` for per-agent occupancy and status
    - Return list of agents with agent_id, occupancy_rate (0.0–1.0), current_status (AVAILABLE|ON_CALL|AFTER_CONTACT_WORK|OFFLINE), avg_handle_time, contacts_handled
    - _Requirements: 2.2_

  - [ ]* 3.7 Write property test for agent utilization response
    - **Property 5: Agent utilization response contains per-agent metrics**
    - Generate random Athena result sets; verify each agent entry has agent_id, occupancy_rate in [0.0, 1.0], current_status from valid set
    - **Validates: Requirements 2.2**

  - [x] 3.8 Implement `trigger_sla_alert` Lambda tool
    - Create `lambda_tools/supervisor/trigger_sla_alert/handler.py`
    - Accept input `{ queue_name, current_sla_pct, threshold_pct, breach_timestamp }`
    - Implement SLA threshold lookup (per-queue config from env var, fallback to default)
    - Publish `SLA_BREACH` event to EventBridge via shared alert_publisher
    - Return `{ alert_id, status: "published" }`
    - _Requirements: 3.1, 3.3_

  - [ ]* 3.9 Write property tests for SLA threshold and alert triggering
    - **Property 6: Threshold breach triggers alert if and only if metric is below threshold**
    - Generate random metric/threshold pairs; verify alert published iff metric < threshold
    - **Property 7: SLA threshold lookup returns per-queue or default config**
    - Generate random queue names; verify per-queue config returned when configured, default otherwise; verify target_pct and window_seconds are positive
    - **Validates: Requirements 3.1, 3.3**

  - [x] 3.10 Create Supervisor Agent configuration for Bedrock AgentCore
    - Create `connect_analytics_cdk/agents/supervisor_agent.py`
    - Define AgentCore agent with Claude Sonnet model, system prompt scoped to supervisor domain
    - Register tools: get_queue_health, get_abandonment_analysis, get_agent_utilization, trigger_sla_alert
    - Configure AgentCore Gateway shared resource (first agent creates it, others reference it)
    - _Requirements: 2.3, 1.1_

  - [ ]* 3.11 Write property test for query intent routing
    - **Property 1: Query intent routing correctness**
    - Generate random queries with deterministic intent labels; verify routing maps to correct agent identifier; verify unknown intents return "unsupported"
    - **Validates: Requirements 1.1, 1.4**

  - [ ]* 3.12 Write property test for SQL generation safety
    - **Property 2: Generated SQL references only catalog tables and columns**
    - Generate random SQL strings from query builders; verify all table refs in {connect_ctr, connect_agent_events, connect_contact_lens} and all column refs exist in table schema
    - **Validates: Requirements 1.2**

- [ ] 4. Checkpoint — Supervisor Agent functional
  - Ensure all tests pass, ask the user if questions arise.
  - Verify Supervisor Agent tools return correct responses against synthetic data
  - Verify AgentCore Gateway configuration is valid

- [x] 5. Alert Pipeline — EventBridge, SNS, Slack
  - [x] 5.1 Implement Slack webhook formatter Lambda
    - Create `lambda_tools/alerts/slack_formatter/handler.py`
    - Accept SNS event payload, extract alert details
    - Format alert into Slack Block Kit JSON (header block + section with alert details)
    - POST to Slack webhook URL (from env var)
    - Implement retry logic: 3 retries with exponential backoff, log failures to CloudWatch
    - _Requirements: 9.2, 9.4_

  - [ ]* 5.2 Write property tests for alert formatting and routing
    - **Property 15: Alert routing maps each alert type to correct SNS topic and Slack channel**
    - Generate random alert events with valid detail-types; verify routing to correct SNS topic and Slack channel per config
    - **Property 16: Slack alert formatter produces valid Block Kit JSON**
    - Generate random alert payloads; verify output has `blocks` array with header and section
    - **Validates: Requirements 9.1, 9.2, 9.3**

  - [ ]* 5.3 Write property test for Slack delivery retry logic
    - **Property 17: Slack delivery retry logic**
    - Generate random failure sequences; verify exactly 3 retries with exponentially increasing delays; verify CloudWatch logging on each failure
    - **Validates: Requirements 9.4**

  - [ ]* 5.4 Write property test for SLA breach alert message
    - **Property 8: SLA breach alert message contains all required fields**
    - Generate random SLA breach payloads; verify formatted Slack message contains queue_name, current_sla_pct, threshold_pct, breach_timestamp
    - **Validates: Requirements 3.4**

  - [x] 5.5 Create the alert stack (EventBridge + SNS + Slack Lambda)
    - Create `connect_analytics_cdk/stacks/alert_stack.py`
    - Define EventBridge rules: one per alert type (SLA_BREACH, ABANDONMENT_SPIKE, OCCUPANCY_CRITICAL, COMPLIANCE_VIOLATION, BURNOUT_RISK) matching on `detail-type`
    - Define SNS topics: one per alert type for per-type Slack channel routing
    - Define Slack formatter Lambda (container image) subscribed to all SNS topics
    - Configure Slack webhook URL and channel routing via environment variables
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 6. Checkpoint — Alert pipeline wired
  - Ensure all tests pass, ask the user if questions arise.
  - Verify EventBridge rules match expected alert types
  - Verify SNS topics and Slack formatter Lambda are correctly configured

- [x] 7. Quality Agent and WFM Agent — Remaining Tools and Agents
  - [x] 7.1 Implement `get_sentiment_trends` Lambda tool
    - Create `lambda_tools/quality/get_sentiment_trends/handler.py`
    - Accept input `{ time_range?: str, agent_id?: str }`
    - Query `connect_contact_lens` for sentiment aggregation by period
    - Aggregate sentiment percentages (positive, negative, neutral, mixed) per period
    - Generate matplotlib line chart of sentiment over time, encode as base64 PNG
    - Return `{ periods: [...], chart: base64_png }`
    - _Requirements: 4.1, 4.2_

  - [ ]* 7.2 Write property tests for sentiment and chart generation
    - **Property 9: Sentiment aggregation percentages sum to 100%**
    - Generate random Contact Lens records; verify positive + negative + neutral + mixed = 100% (±0.01 tolerance)
    - **Property 10: Chart generation produces valid output for any non-empty dataset**
    - Generate random non-empty datasets; verify base64 output decodes to valid PNG (magic bytes check)
    - **Validates: Requirements 4.1, 4.2, 6.2**

  - [x] 7.3 Implement `get_coaching_recommendations` Lambda tool
    - Create `lambda_tools/quality/get_coaching_recommendations/handler.py`
    - Accept input `{ agent_id?: str, time_range?: str }`
    - Query `connect_contact_lens` for agents with high negative sentiment rates
    - Return recommendations with agent_id, negative_sentiment_rate, sample_excerpts, coaching_suggestions
    - _Requirements: 4.3_

  - [ ]* 7.4 Write property test for coaching recommendations
    - **Property 11: Coaching recommendations identify agents above negative sentiment threshold**
    - Generate random Contact Lens records; verify returned agents are exactly those above threshold, none below
    - **Validates: Requirements 4.3**

  - [x] 7.5 Implement `get_compliance_violations` Lambda tool
    - Create `lambda_tools/quality/get_compliance_violations/handler.py`
    - Accept input `{ time_range?: str, violation_type?: str }`
    - Query `connect_contact_lens` for records with non-empty compliance_flags
    - Return violations with violation_type, contact_id, agent_id, timestamp, transcript_excerpt
    - If severity=HIGH, publish `COMPLIANCE_VIOLATION` event to EventBridge via shared alert_publisher
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 7.6 Write property test for compliance violation records
    - **Property 12: Compliance violation detection returns complete violation records**
    - Generate random Contact Lens records with compliance_flags; verify each returned record has non-null violation_type, contact_id, agent_id, timestamp, transcript_excerpt
    - **Validates: Requirements 5.1, 5.2**

  - [x] 7.7 Create Quality Agent configuration for Bedrock AgentCore
    - Create `connect_analytics_cdk/agents/quality_agent.py`
    - Define AgentCore agent with Claude Sonnet model, system prompt scoped to QA/compliance domain
    - Register tools: get_sentiment_trends, get_coaching_recommendations, get_compliance_violations
    - Reference shared AgentCore Gateway
    - _Requirements: 4.1, 5.1, 1.1_

  - [x] 7.8 Implement `get_staffing_forecast` Lambda tool
    - Create `lambda_tools/wfm/get_staffing_forecast/handler.py`
    - Accept input `{ forecast_horizon_days: int, queue_name?: str }`
    - Query `connect_ctr` for historical volume patterns
    - Calculate projected contact volume with confidence intervals (lower, upper bounds)
    - Generate matplotlib area chart with confidence bands, encode as base64 PNG
    - Return `{ forecast: [...], chart: base64_png }`
    - _Requirements: 6.1, 6.2, 6.4_

  - [ ]* 7.9 Write property test for staffing forecast
    - **Property 13: Staffing forecast structure and confidence interval invariant**
    - Generate random CTR volume data with horizon N; verify entries cover requested horizon, predicted_volume >= 0, confidence_lower <= predicted_volume <= confidence_upper
    - **Validates: Requirements 6.1, 6.4**

  - [x] 7.10 Implement `get_burnout_signals` Lambda tool
    - Create `lambda_tools/wfm/get_burnout_signals/handler.py`
    - Accept input `{ threshold?: float, time_range?: str }`
    - Query `connect_agent_events` for burnout patterns (sustained high occupancy, extended ACW, increasing handle times)
    - Calculate burnout_score (0.0–1.0) per agent, sort descending
    - If burnout_score > critical threshold (env var, default 0.85), publish `BURNOUT_RISK` event to EventBridge
    - Return ranked list with agent_id, burnout_score, occupancy_rate, avg_acw_duration, handle_time_trend, recommended_action
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 7.11 Write property test for burnout detection
    - **Property 14: Burnout detection produces valid ranked results**
    - Generate random Agent Event records; verify scores in [0.0, 1.0], list sorted by burnout_score descending, each entry has all required fields
    - **Validates: Requirements 7.1, 7.2**

  - [x] 7.12 Create WFM Agent configuration for Bedrock AgentCore
    - Create `connect_analytics_cdk/agents/wfm_agent.py`
    - Define AgentCore agent with Nova Lite model, system prompt scoped to workforce planning domain
    - Register tools: get_staffing_forecast, get_burnout_signals
    - Reference shared AgentCore Gateway
    - _Requirements: 6.3, 1.1_

- [ ] 8. Checkpoint — All three agents and tools functional
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all 9 tool Lambdas return correct responses
  - Verify all 3 AgentCore agent configurations are valid

- [x] 9. Nova Sonic Voice Output Integration
  - [x] 9.1 Implement Nova Sonic voice synthesis module
    - Create `lambda_tools/shared/voice_client.py`
    - Implement `synthesize_speech(text: str) -> bytes` using Nova Sonic via Bedrock InvokeModel API
    - Integrate into NLQ response flow: when `voice=true`, call Nova Sonic after agent text response, return both text and audio stream
    - Handle Nova Sonic failures gracefully — return text-only response on error
    - _Requirements: 11.1, 11.2, 11.3_

  - [ ]* 9.2 Write property test for voice synthesis conditional invocation
    - **Property 20: Voice synthesis conditional invocation**
    - Generate random agent responses with voice=true/false; verify audio field present iff voice=true, audio is non-empty bytes when present
    - **Validates: Requirements 11.1**

- [x] 10. Authentication and Authorization
  - [x] 10.1 Implement auth middleware
    - Create `lambda_tools/shared/auth.py`
    - Implement authentication gate: reject requests without valid token, return 401 with "Authentication required" message
    - Implement RBAC enforcement: supervisor→Supervisor_Agent, qa_analyst→Quality_Agent, wfm_planner→WFM_Agent
    - Log unauthorized access attempts with user_id, attempted_agent, timestamp
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 10.2 Write property tests for auth and RBAC
    - **Property 18: Authentication gate rejects unauthenticated requests**
    - Generate random requests with/without valid tokens; verify unauthenticated requests rejected with auth-required error, valid tokens proceed
    - **Property 19: Role-based access control enforcement with audit logging**
    - Generate random (user_role, target_agent) pairs; verify access granted iff mapping permits; verify denied requests produce audit log entry with user_id, attempted_agent, timestamp
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4**

  - [x] 10.3 Create the auth stack
    - Create `connect_analytics_cdk/stacks/auth_stack.py`
    - Define Cognito user pool (or API key auth for hackathon scope) with role attributes
    - Configure role-to-agent mapping
    - _Requirements: 12.1, 12.2_

- [x] 11. CDK Stack — Full Infrastructure Assembly
  - [x] 11.1 Create the agent stack
    - Create `connect_analytics_cdk/stacks/agent_stack.py`
    - Define all 9 Lambda container image functions (DockerImageFunction) with ECR repositories
    - Define shared Dockerfile base image with matplotlib, numpy, pyarrow, faker, boto3, bedrock-agentcore SDK
    - Define AgentCore Gateway with tool-to-Lambda ARN mappings
    - Define all 3 AgentCore agents (Supervisor/Claude Sonnet, Quality/Claude Sonnet, WFM/Nova Lite)
    - Apply least-privilege IAM: each Lambda gets only the permissions it needs (Athena, S3 read, EventBridge put, Polly synthesize)
    - _Requirements: 10.1, 10.3_

  - [x] 11.2 Create CDK app entry point and wire all stacks
    - Create `connect_analytics_cdk/app.py` as CDK app entry point
    - Create `connect_analytics_cdk/cdk.json` with context parameters for multi-environment support (dev, staging, prod)
    - Create `connect_analytics_cdk/requirements.txt` with CDK + boto3 dependencies
    - Wire DataStack → AgentStack → AlertStack → AuthStack with cross-stack references
    - Add CfnOutputs for agent endpoint URLs and Slack webhook configuration parameters
    - _Requirements: 10.1, 10.2, 10.4_

  - [ ]* 11.3 Write CDK snapshot and integration tests
    - Create `tests/integration/test_cdk_synth.py`
    - Verify CDK synth produces all expected resources (S3, Glue, Athena, Lambda, EventBridge, SNS, AgentCore)
    - Verify multi-environment synthesis works with different context parameters
    - Verify IAM policies have no wildcard actions (least-privilege check)
    - Verify CfnOutputs include agent endpoints and Slack config
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 12. Checkpoint — Full CDK stack synthesizes cleanly
  - Ensure all tests pass, ask the user if questions arise.
  - Run `cdk synth` and verify no errors
  - Verify all cross-stack references resolve correctly

- [x] 13. Demo Dry-Run — Validate All 8 Scripted Responses
  - [x] 13.1 Create end-to-end test harness for demo scenarios
    - Create `tests/integration/test_demo_scenarios.py`
    - Write automated tests for all 8 scripted demo responses against synthetic data
    - Test Supervisor queries: queue health, abandonment analysis, agent utilization, SLA alert trigger
    - Test Quality queries: sentiment trends (with chart), coaching recommendations, compliance violations
    - Test WFM queries: staffing forecast (with chart), burnout signals
    - Verify each tool Lambda returns expected output structure and non-empty data
    - Verify alert events are published for threshold-breach scenarios
    - Verify chart outputs are valid base64 PNG for sentiment and forecast tools
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 4.1, 4.2, 4.3, 5.1, 6.1, 6.2, 7.1, 7.2_

  - [ ]* 13.2 Write property test for alert threshold triggering across all alert types
    - **Property 6: Threshold breach triggers alert if and only if metric is below/above threshold**
    - Generate random metric/threshold pairs for SLA, compliance severity, and burnout score; verify alert published iff condition met
    - **Validates: Requirements 3.1, 5.3, 7.3**

- [ ] 14. Final checkpoint — All tests pass, platform demo-ready
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all 20 correctness properties are covered by property tests
  - Verify all 12 requirements are covered by implementation tasks

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All Lambda tools use container images (DockerImageFunction) due to matplotlib/numpy/pyarrow exceeding zip limit
- Bedrock AgentCore (not older Bedrock Agents) with bedrock-agentcore SDK
- Python throughout: CDK, Lambdas, tests, synthetic data generator
- Hypothesis library for property-based tests with `@settings(max_examples=100)`
- Property tests validate universal correctness properties; unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation at each build phase
