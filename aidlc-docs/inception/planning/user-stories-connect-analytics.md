# User Stories — Connect Analytics Platform

## Epic 1: Natural Language Query Interface

### US-1.1: Ask questions in plain English
**As a** contact center team member,
**I want to** ask questions about my contact center in plain English,
**So that** I can get analytics insights without writing SQL or navigating dashboards.

**Acceptance Criteria:**
- Query is routed to the correct agent (Supervisor, Quality, or WFM) based on intent
- Agent translates the query into Athena SQL and returns a human-readable summary
- Unsupported queries return a helpful message suggesting valid categories
- Failed SQL queries return a user-friendly error (no raw SQL or stack traces exposed)

**Priority:** P0 — Core platform capability
**Persona:** All users (Supervisor, QA Analyst, WFM Planner)
**Requirements:** R1.1–R1.5

---

## Epic 2: Supervisor Agent — Real-Time Floor Management

### US-2.1: Monitor queue health
**As a** floor supervisor,
**I want to** ask "Show me queue health right now" and get current metrics,
**So that** I can identify service degradation and respond quickly.

**Acceptance Criteria:**
- Returns queue size, longest wait time, service level percentage, and average handle time
- Queries CTR and Agent Event data via Athena
- Uses Claude Sonnet as the foundation model

**Priority:** P0 — Demo query #1
**Persona:** Floor Supervisor
**Requirements:** R2.1, R2.3
**Demo query:** "Show me queue health right now" → "Billing queue at 12 min avg wait — SLA breach. 3 agents available, abandonment at 14%."

### US-2.2: Investigate abandonment spikes
**As a** floor supervisor,
**I want to** ask "Why did abandonment spike at 2pm?" and get root cause analysis,
**So that** I can understand what went wrong and prevent it from recurring.

**Acceptance Criteria:**
- Correlates CTR abandonment data with agent state events at the specified time
- Returns specific root cause (e.g., agents on break simultaneously, occupancy spike)
- Provides actionable recommendations

**Priority:** P0 — Demo query #2
**Persona:** Floor Supervisor
**Requirements:** R2.1
**Demo query:** "Why did abandonment spike at 2pm?" → "2 agents went to break simultaneously. Occupancy hit 96% for 18 minutes."

### US-2.3: Check agent utilization
**As a** floor supervisor,
**I want to** see per-agent occupancy rates and current status,
**So that** I can rebalance workload across queues.

**Acceptance Criteria:**
- Returns per-agent occupancy rate (0.0–1.0) and current status (Available, On Call, ACW, Offline)
- Includes average handle time and contacts handled per agent
- Supports filtering by specific agent ID or all agents

**Priority:** P1
**Persona:** Floor Supervisor
**Requirements:** R2.2

---

## Epic 3: SLA Breach Alerting

### US-3.1: Receive SLA breach alerts in Slack
**As a** floor supervisor,
**I want to** receive a Slack alert when an SLA threshold is breached,
**So that** I can take corrective action before service levels degrade further.

**Acceptance Criteria:**
- Alert fires when SLA metric falls below configured threshold
- Alert delivered to Slack within 60 seconds of breach detection
- Alert message includes queue name, current SLA %, configured threshold, and timestamp
- SLA thresholds are configurable per queue

**Priority:** P0 — Live demo moment (EventBridge → SNS → Slack fires during demo)
**Persona:** Floor Supervisor, Contact Center Manager
**Requirements:** R3.1–R3.4
**Demo moment:** Query "Show me queue health" triggers ⚠️ Slack message live

---

## Epic 4: Quality Agent — Sentiment & Coaching

### US-4.1: Analyze sentiment trends
**As a** QA analyst,
**I want to** ask about customer sentiment trends over a time period,
**So that** I can identify patterns and target coaching efforts.

**Acceptance Criteria:**
- Returns aggregated sentiment scores (positive, negative, neutral, mixed) per period
- Generates a sentiment trend chart (matplotlib → base64 PNG)
- Percentages sum to 100% (±0.01 tolerance)

**Priority:** P0
**Persona:** QA Analyst
**Requirements:** R4.1, R4.2

### US-4.2: Get coaching recommendations
**As a** QA analyst,
**I want to** ask "Which agents need coaching this week?" and get specific recommendations,
**So that** I can provide targeted feedback to improve agent performance.

**Acceptance Criteria:**
- Identifies agents with consistently negative sentiment scores
- Returns agent ID, negative sentiment rate, sample transcript excerpts, and coaching suggestions
- Only recommends agents above the configured negative sentiment threshold

**Priority:** P0 — Demo query #4
**Persona:** QA Analyst
**Requirements:** R4.3
**Demo query:** "Which agents need coaching this week?" → "Agent-017 had 4 negative sentiment calls with a pattern of interruptions. Recommend de-escalation coaching."

### US-4.3: Review worst calls
**As a** QA analyst,
**I want to** ask "Show me the worst call" and see the transcript with sentiment analysis,
**So that** I can understand specific interaction failures.

**Acceptance Criteria:**
- Returns transcript with per-turn sentiment scores and category flags
- Includes a sentiment trend chart for the selected call
- Supports filtering by agent, time range, or violation type

**Priority:** P0 — Demo query #5
**Persona:** QA Analyst
**Requirements:** R4.1, R4.3
**Demo query:** "Show me the worst call" → Transcript with per-turn sentiment + category flags + chart URL

---

## Epic 5: Compliance Violation Detection

### US-5.1: Flag compliance violations
**As a** compliance analyst,
**I want to** query for compliance violations and see flagged interactions,
**So that** I can review and remediate issues promptly.

**Acceptance Criteria:**
- Scans Contact Lens categories and transcripts for predefined violation patterns
- Returns violation type, contact ID, agent ID, timestamp, and transcript excerpt
- High-severity violations trigger immediate Slack notification via Alert Pipeline

**Priority:** P1
**Persona:** Compliance Analyst
**Requirements:** R5.1–R5.3

---

## Epic 6: WFM Agent — Staffing & Burnout

### US-6.1: Get staffing forecasts
**As a** workforce planner,
**I want to** ask "Forecast staffing for next Monday" and get projected demand,
**So that** I can plan schedules that match predicted contact volume.

**Acceptance Criteria:**
- Analyzes historical CTR volume patterns and returns projected contact volume
- Produces a forecast chart (matplotlib area chart with confidence bands)
- Includes confidence intervals for prediction reliability
- Uses Nova Lite as the foundation model (cost-effective for numerical workloads)

**Priority:** P0 — Demo query #6
**Persona:** Workforce Planner
**Requirements:** R6.1–R6.4
**Demo query:** "Forecast staffing for next Monday" → "Expect 340 contacts 10am-2pm. Need 22 agents, have 18. Recommend 4 from flex pool." + chart

### US-6.2: Detect burnout signals
**As a** workforce planner,
**I want to** ask "Any agents showing burnout signals?" and get at-risk agents,
**So that** I can adjust schedules and prevent attrition.

**Acceptance Criteria:**
- Analyzes Agent Event data for burnout patterns (sustained high occupancy, extended ACW, increasing handle times)
- Returns ranked list of at-risk agents with burnout score (0.0–1.0), contributing metrics, and recommended schedule adjustments
- Critical burnout scores (>0.85) trigger alert via Alert Pipeline

**Priority:** P0 — Demo query #7
**Persona:** Workforce Planner
**Requirements:** R7.1–R7.3
**Demo query:** "Any agents showing burnout signals?" → "Agent-023 and Agent-031: occupancy above 92% for 8 consecutive days with rising handle times."

---

## Epic 7: Alert Pipeline

### US-7.1: Route alerts to Slack by type
**As a** contact center manager,
**I want to** receive alerts in Slack organized by type (SLA, compliance, burnout),
**So that** the right team is notified without checking a dashboard.

**Acceptance Criteria:**
- EventBridge routes events by detail-type to the correct SNS topic
- Different alert types can be directed to different Slack channels
- Slack messages use Block Kit formatting with header and detail sections
- Failed deliveries retry 3 times with exponential backoff, failures logged to CloudWatch

**Priority:** P0
**Persona:** Contact Center Manager
**Requirements:** R9.1–R9.4

---

## Epic 8: Data Foundation

### US-8.1: Queryable Connect data lake
**As a** platform operator,
**I want to** have Connect CTR, Agent Event, and Contact Lens data cataloged and queryable,
**So that** all three agents can access consistent, up-to-date analytics data.

**Acceptance Criteria:**
- Glue Data Catalog contains table definitions for all 3 data sources with correct schemas
- Athena queries return results within 30 seconds for up to 90 days of data
- New S3 partitions reflected within 15 minutes via partition projection
- Query failures return structured errors to the requesting agent

**Priority:** P0 — Must be built first (Step 1 in build order)
**Persona:** Platform Operator
**Requirements:** R8.1–R8.4

### US-8.2: Generate synthetic demo data
**As a** hackathon team member,
**I want to** generate synthetic data with specific patterns baked in,
**So that** the 8 scripted demo queries produce reproducible, impressive responses.

**Acceptance Criteria:**
- 10,000 CTR records with 2pm abandonment spike (18%), mean 7 min handle time, 10am-2pm peak
- 50,000 Agent Event records with 2 agents on break simultaneously at 2pm, 95%+ occupancy peaks
- 10,000 Contact Lens records with Agent-017 having ≥4 negative calls, Agent-023/031 at >92% occupancy for 8 days
- Deterministic seed for reproducible output
- Parquet for CTR/Agent Events, JSON for Contact Lens

**Priority:** P0 — Data drives demo responses
**Persona:** Hackathon Team
**Requirements:** R8.1

---

## Epic 9: Voice Output

### US-9.1: Hear responses spoken aloud
**As a** supervisor on the floor,
**I want to** hear analytics responses spoken aloud via Polly,
**So that** I can get updates hands-free while managing the team.

**Acceptance Criteria:**
- When voice=true, response includes both text and MP3 audio stream
- Uses Polly neural voice engine for natural-sounding output
- Audio generated within 5 seconds of text response
- When voice=false or unset, no audio field in response
- Polly failures degrade gracefully to text-only

**Priority:** P1
**Persona:** Floor Supervisor
**Requirements:** R11.1–R11.3

---

## Epic 10: Infrastructure as Code

### US-10.1: One-command deployment
**As a** DevOps engineer,
**I want to** deploy the entire platform with `cdk deploy` and 3 parameters,
**So that** environments are reproducible and the hackathon demo deploys in ~8 minutes.

**Acceptance Criteria:**
- CDK stack defines all resources (S3, Glue, Athena, Lambda, EventBridge, SNS, AgentCore agents)
- Supports multi-environment deployment via CDK context parameters
- Least-privilege IAM policies for each component
- Outputs agent endpoint URLs and Slack webhook config on completion
- Parameters: InstanceId, DataLakeBucket, AlertDestination

**Priority:** P0 — Demo query #8 (live `cdk deploy`)
**Persona:** DevOps Engineer
**Requirements:** R10.1–R10.4
**Demo moment:** Live `cdk deploy` — stack deploys in ~8 min

---

## Epic 11: Authentication & Authorization

### US-11.1: Role-based agent access
**As a** platform administrator,
**I want to** enforce role-based access control,
**So that** supervisors only see Supervisor Agent, QA analysts only see Quality Agent, and WFM planners only see WFM Agent.

**Acceptance Criteria:**
- Users must authenticate before accessing any agent
- Role-to-agent mapping enforced: supervisor→Supervisor, qa_analyst→Quality, wfm_planner→WFM
- Unauthenticated requests rejected with 401
- Unauthorized access attempts denied and logged with user ID, attempted agent, timestamp

**Priority:** P1 (API key auth for hackathon, Cognito for production)
**Persona:** Platform Administrator
**Requirements:** R12.1–R12.4

---

## Story Map Summary

| Epic | P0 Stories | P1 Stories | Demo Queries |
|------|-----------|-----------|-------------|
| NLQ Interface | US-1.1 | — | All queries |
| Supervisor Agent | US-2.1, US-2.2 | US-2.3 | #1, #2 |
| SLA Alerting | US-3.1 | — | Live Slack alert |
| Quality Agent | US-4.1, US-4.2, US-4.3 | — | #4, #5 |
| Compliance | — | US-5.1 | — |
| WFM Agent | US-6.1, US-6.2 | — | #6, #7 |
| Alert Pipeline | US-7.1 | — | Live Slack alert |
| Data Foundation | US-8.1, US-8.2 | — | Underpins all |
| Voice Output | — | US-9.1 | — |
| Infrastructure | US-10.1 | — | #8 (live deploy) |
| Auth & RBAC | — | US-11.1 | — |
