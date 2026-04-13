# Product Requirements Document (PRD)
# Amazon Connect Analytics Platform

## Document Info

| Field | Value |
|-------|-------|
| Product | Connect Analytics Platform |
| Version | 1.0 — Hackathon MVP |
| Target Date | April 15, 2026 |
| Team | Brigette Bucke, Yunjie Chen, Vandana Tewani |
| Methodology | AI-DLC |

---

## 1. Problem Statement

Every Amazon Connect deployment hits the same wall on Day 2. The phones are ringing, agents are logged in, Contact Lens is transcribing — but nobody built the layer that turns all that data into decisions.

Today, contact center teams face:
- Zero native natural language query interface for supervisors
- Zero automated coaching from Contact Lens data
- $150K+ annual cost for custom-built analytics pipelines
- Customers building custom Kinesis → Lambda → S3 → QuickSight pipelines just to answer basic operational questions

Supervisors, QA analysts, and workforce planners each need different views of the same underlying data, but there's no unified, AI-powered way to access it.

## 2. Solution Overview

Three AI agents that sit on Connect's data lake and answer the questions supervisors, QA analysts, and workforce planners actually ask — in natural language, with actions attached.

| Agent | Persona | Model | What It Does |
|-------|---------|-------|-------------|
| Supervisor Agent | Real-time floor manager | Claude Sonnet | Queue health, SLA breaches, agent utilization, abandonment root cause |
| Quality Agent | QA / Compliance analyst | Claude Sonnet | Sentiment trends, coaching recommendations, compliance violations |
| WFM Agent | Workforce planner | Nova Lite | Staffing forecasts, burnout signals, schedule optimization |

All agents run on Amazon Bedrock AgentCore (serverless). No EKS, no containers to manage, no custom orchestration.

## 3. Target Users

### Primary Personas

| Persona | Role | Key Questions They Ask |
|---------|------|----------------------|
| Floor Supervisor | Manages agents in real time | "How are my queues?" "Why did abandonment spike?" "Who's available?" |
| QA Analyst | Reviews call quality and compliance | "Which agents need coaching?" "Show me the worst call" "Any compliance violations?" |
| Workforce Planner | Plans schedules and staffing | "Forecast next Monday" "Any burnout signals?" "Where do I need flex pool?" |
| Contact Center Manager | Oversees operations | Receives Slack alerts for SLA breaches, compliance issues, burnout risks |
| Platform Operator | Deploys and maintains the system | One-command CDK deployment, monitoring via CloudWatch |

## 4. Scope — Hackathon MVP

### In Scope

- 3 AI agents on Bedrock AgentCore with natural language query interface
- Data foundation: S3 + Glue Data Catalog + Athena (3 tables: CTR, Agent Events, Contact Lens)
- Synthetic data generator with reproducible demo patterns
- 9 tool Lambda functions (container images) for Athena queries and chart generation
- Alert pipeline: EventBridge → SNS → Slack (5 alert types)
- Voice output via Amazon Polly (neural engine)
- CDK infrastructure-as-code (Python, one-command deploy)
- Role-based access control (API key auth for hackathon)
- 8 scripted demo queries with validated responses

### Out of Scope (Post-Hackathon)

- Real Connect instance integration (demo uses synthetic data)
- Connect:DescribeInstance auto-discovery
- Q in Connect Events (4th data stream)
- Production auth (Cognito)
- Multi-region deployment
- Real-time streaming (Kinesis integration)
- Dashboard UI (agents are query-based, not dashboard-based)

## 5. Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Demo queries answered correctly | 8/8 | Demo dry-run validation |
| CDK deploy time | < 10 minutes | Timed during demo |
| Slack alert delivery | < 60 seconds from breach | Live demo observation |
| Agent response latency | < 10 seconds for text | Timed during demo |
| Chart generation | Valid PNG for sentiment + forecast | Automated test validation |
| Cost per month (estimated) | < $50 at demo load | AgentCore + Athena + Lambda pricing model |

## 6. Technical Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Agent Runtime | Amazon Bedrock AgentCore | Serverless, managed orchestration, no infra |
| Supervisor/Quality Model | Claude Sonnet | Strong reasoning for root cause + nuanced language |
| WFM Model | Nova Lite | Numerical workloads, 40x cheaper than Sonnet |
| Data Lake | S3 (Parquet + JSON) | Connect-native export format |
| Data Catalog | AWS Glue | Partition projection, schema management |
| Query Engine | Amazon Athena | Serverless SQL on S3 |
| Tool Execution | Lambda Container Images | matplotlib/numpy exceed 50MB zip limit |
| Alerts | EventBridge → SNS → Slack | Decoupled, filterable, retryable |
| Voice | Amazon Polly (Neural) | Natural-sounding speech output |
| Infrastructure | AWS CDK (Python) | Single language for infra + app code |

## 7. Key Business Rules

- Each agent serves exactly one persona — no overlap in tool access
- Agents translate NL to SQL — they don't hardcode responses
- Demo responses are driven by synthetic data patterns, not agent prompts
- SLA thresholds are configurable per queue with sensible defaults
- Burnout detection uses composite scoring (occupancy + ACW + handle time trends)
- All alerts include actionable context (not just "something is wrong")
- Error messages never expose SQL, table names, or stack traces

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| AgentCore Gateway API not yet GA | Blocks all agent functionality | Verify API availability before coding (Step 2a in build plan) |
| Hackathon timeline (April 6–15) | 10 working days, team members OOO | Build order prioritizes demo-critical path; optional tasks marked |
| Synthetic data doesn't match demo script | Demo responses are wrong | Data patterns are specified precisely; validation query confirms before agent work |
| Lambda cold starts affect demo latency | Slow first query | Pre-warm Lambdas before demo; container images have longer cold starts |
| AgentCore ≠ Bedrock Agents (SDK confusion) | Wrong SDK, wrong billing | Documented clearly in impl plan; use `bedrock-agentcore` not `bedrock-agent` |

## 9. Cost Analysis (Estimated Monthly at Demo Load)

| Service | Usage | Estimated Cost |
|---------|-------|---------------|
| Bedrock AgentCore (Supervisor + Quality) | ~1,500 queries/day, Claude Sonnet | ~$15–25/mo |
| Bedrock AgentCore (WFM) | ~500 queries/day, Nova Lite | ~$1–3/mo |
| AgentCore Gateway | ~2,000 tool invocations/day | ~$0.23/mo |
| Athena | ~5GB scanned/day | ~$0.75/mo |
| Lambda (container images) | ~2,000 invocations/day, 512MB, 10s avg | ~$2/mo |
| S3 | ~10GB stored | ~$0.23/mo |
| EventBridge + SNS | ~100 alerts/day | ~$0.10/mo |
| Polly | ~500 requests/day | ~$2/mo |
| CloudWatch Logs | 30-day retention | ~$0.25/mo |
| **Total** | | **~$22–34/mo** |

## 10. Demo Script (5 minutes)

| Time | Speaker | Query / Action | Expected Response |
|------|---------|---------------|-------------------|
| 0:30 | Vandana | "Show me queue health right now" | Billing queue at 12 min avg wait — SLA breach. 3 agents available. |
| 1:00 | Vandana | "Why did abandonment spike at 2pm?" | 2 agents went to break simultaneously. Occupancy hit 96%. |
| 1:00 | LIVE | EventBridge → Slack | ⚠️ "Billing queue SLA breach" fires in Slack |
| 1:30 | Brigette | "Which agents need coaching this week?" | Agent-017: 4 negative calls, interruption pattern. |
| 2:00 | Brigette | "Show me the worst call" | Transcript + sentiment chart |
| 3:00 | Yunjie | "Forecast staffing for next Monday" | 340 contacts 10am-2pm, need 22 agents, have 18 + chart |
| 3:30 | Yunjie | "Any agents showing burnout signals?" | Agent-023 and Agent-031: >92% occupancy for 8 days |
| 4:30 | Brigette | Live `cdk deploy` | Stack deploys in ~8 min |
