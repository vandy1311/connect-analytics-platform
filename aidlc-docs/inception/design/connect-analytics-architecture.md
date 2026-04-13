# Architecture Document — Connect Analytics Platform

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                    ┌──────────────────┐                              │
│                    │  NLQ Interface    │                              │
│                    │  (Natural Lang)   │                              │
│                    └────────┬─────────┘                              │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│                        AUTH LAYER                                    │
│                    ┌────────┴─────────┐                              │
│                    │  Auth / RBAC     │                              │
│                    │  (API Key/Cognito)│                              │
│                    └────────┬─────────┘                              │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────────┐
│              AGENT LAYER — Amazon Bedrock AgentCore                  │
│                    ┌────────┴─────────┐                              │
│                    │  AgentCore       │                              │
│                    │  Gateway         │ (shared by all 3 agents)     │
│                    └──┬─────┬─────┬──┘                              │
│                       │     │     │                                  │
│              ┌────────┘     │     └────────┐                        │
│              ▼              ▼              ▼                         │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │
│   │  Supervisor  │ │   Quality    │ │     WFM      │               │
│   │    Agent     │ │    Agent     │ │    Agent     │               │
│   │ Claude Sonnet│ │ Claude Sonnet│ │  Nova Lite   │               │
│   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘               │
└──────────┼────────────────┼────────────────┼────────────────────────┘
           │                │                │
┌──────────┼────────────────┼────────────────┼────────────────────────┐
│          TOOL LAYER — Lambda Container Images (ECR)                  │
│          │                │                │                         │
│   ┌──────┴──────┐  ┌─────┴──────┐  ┌─────┴──────┐                 │
│   │get_queue_   │  │get_senti-  │  │get_staffing│                 │
│   │  health     │  │ment_trends │  │ _forecast  │                 │
│   │get_abandon- │  │get_coaching│  │get_burnout │                 │
│   │  ment_anlys │  │ _recommend │  │ _signals   │                 │
│   │get_agent_   │  │get_compli- │  └────────────┘                 │
│   │  utilization│  │ance_violat │                                  │
│   │trigger_sla_ │  └────────────┘                                  │
│   │  alert      │                                                   │
│   └──────┬──────┘                                                   │
└──────────┼──────────────────────────────────────────────────────────┘
           │
┌──────────┼──────────────────────────────────────────────────────────┐
│          QUERY LAYER                                                 │
│   ┌──────┴──────┐                                                   │
│   │   Amazon    │  Workgroup: connect-analytics                     │
│   │   Athena    │  Query timeout: 30s                               │
│   └──────┬──────┘                                                   │
└──────────┼──────────────────────────────────────────────────────────┘
           │
┌──────────┼──────────────────────────────────────────────────────────┐
│          DATA LAYER — S3 + Glue Data Catalog                        │
│   ┌──────┴──────┐     ┌─────────────────────────────────┐          │
│   │  Glue Data  │     │  s3://connect-analytics-demo/   │          │
│   │  Catalog    │────▶│  ├── ctr/          (Parquet)    │          │
│   │  3 tables   │     │  ├── agent-events/ (Parquet)    │          │
│   └─────────────┘     │  └── contact-lens/ (JSON)       │          │
│                        └─────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│          ALERT PIPELINE                                              │
│                                                                      │
│   Tool Lambda ──▶ EventBridge ──▶ SNS Topics ──▶ Slack Webhook     │
│                                                                      │
│   Alert Types:                                                       │
│   • SLA_BREACH          → #connect-sla-alerts                       │
│   • ABANDONMENT_SPIKE   → #connect-sla-alerts                       │
│   • OCCUPANCY_CRITICAL  → #connect-sla-alerts                       │
│   • COMPLIANCE_VIOLATION→ #connect-compliance                       │
│   • BURNOUT_RISK        → #connect-wfm-alerts                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│          VOICE — Amazon Polly (Neural Engine)                        │
│                                                                      │
│   Agent text response ──▶ Polly SynthesizeSpeech ──▶ MP3 stream    │
│   Optional: voice=true flag on request                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow

```
User ──▶ NLQ Interface ──▶ Auth/RBAC ──▶ AgentCore Gateway
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                              Supervisor  Quality     WFM
                                Agent      Agent     Agent
                                    │         │         │
                                    ▼         ▼         ▼
                              AgentCore Gateway (tool routing)
                                    │
                                    ▼
                              Lambda Tool Handler
                                    │
                              ┌─────┼─────┐
                              ▼           ▼
                           Athena    EventBridge
                              │      (if alert)
                              ▼           │
                           S3 Data        ▼
                              │      SNS → Slack
                              ▼
                        Query Results
                              │
                              ▼
                     Agent NL Summary
                              │
                     ┌────────┼────────┐
                     ▼                 ▼
               Text Response    Polly Audio
                     │          (if voice=true)
                     ▼
                   User
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    DATA SOURCES (Synthetic)                    │
│                                                               │
│  generate_synthetic_data.py                                   │
│       │                                                       │
│       ├──▶ 10,000 CTR records (Parquet)                      │
│       │    • Mean 7 min handle time                           │
│       │    • 10am-2pm peak (3x volume)                       │
│       │    • 18% abandonment spike at 2pm                    │
│       │                                                       │
│       ├──▶ 50,000 Agent Event records (Parquet)              │
│       │    • 25 agents, 2-week span                          │
│       │    • 2 agents on break at 2pm simultaneously         │
│       │    • Agent-023/031: >92% occupancy for 8 days        │
│       │                                                       │
│       └──▶ 10,000 Contact Lens records (JSON)                │
│            • 60% positive / 25% neutral / 15% negative       │
│            • Agent-017: ≥4 negative calls                    │
│            • Categories: Escalation, Billing, Compliance     │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    S3 BUCKET                                  │
│  s3://connect-analytics-demo/                                │
│  ├── ctr/year=2026/month=03/day=18/*.parquet                │
│  ├── agent-events/year=2026/month=03/day=18/*.parquet       │
│  ├── contact-lens/year=2026/month=03/day=18/*.json          │
│  └── athena-results/                                         │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    GLUE DATA CATALOG                          │
│  Database: connect_analytics                                  │
│  ├── connect_ctr           (11 columns + 3 partition keys)   │
│  ├── connect_agent_events  (10 columns + 3 partition keys)   │
│  └── connect_contact_lens  (10 fields + 3 partition keys)    │
│  Partition projection: year/month/day                         │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    ATHENA                                      │
│  Workgroup: connect-analytics                                 │
│  Output: s3://connect-analytics-demo/athena-results/         │
│  Query timeout: 30 seconds                                    │
│  Target: results within 30s for 90-day queries               │
└──────────────────────────────────────────────────────────────┘
```

## CDK Stack Dependency Graph

```
                    ┌──────────────┐
                    │   CDK App    │
                    │   app.py     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌────────────┐ ┌───────────┐ ┌──────────┐
     │ DataStack  │ │ AuthStack │ │          │
     │            │ │           │ │          │
     │ • S3 bucket│ │ • API key │ │          │
     │ • Glue DB  │ │   (hack)  │ │          │
     │ • 3 tables │ │ • Cognito │ │          │
     │ • Athena WG│ │   (prod)  │ │          │
     │ • SynthGen │ │ • RBAC    │ │          │
     │   Lambda   │ │   config  │ │          │
     │   (→ ECR)  │ │           │ │          │
     └─────┬──────┘ └─────┬─────┘ │          │
           │               │       │          │
           └───────┬───────┘       │          │
                   ▼               │          │
          ┌────────────────┐       │          │
          │  AgentStack    │◀──────┘          │
          │                │                  │
          │ • Gateway      │                  │
          │ • 3 Agents     │                  │
          │ • Tool Handler │                  │
          │   Lambda       │                  │
          │   (→ ECR)      │                  │
          │ • IAM roles    │                  │
          └────────┬───────┘                  │
                   │                          │
                   ▼                          │
          ┌────────────────┐                  │
          │  AlertStack    │◀─────────────────┘
          │                │
          │ • EventBridge  │
          │   rules (5)    │
          │ • SNS topics(5)│
          │ • Slack Lambda │
          │ • CloudWatch   │
          └────────────────┘

  ECR Note: CDK auto-creates ECR repos for both
  container images (tool handler + data generator).
  DockerImageCode.fromImageAsset() handles build,
  tag, and push on every `cdk deploy`. Zero manual
  ECR setup required.
```

## Agent-to-Tool Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  SUPERVISOR AGENT (Claude Sonnet)                               │
│  ├── get_queue_health          → Athena (CTR + Agent Events)    │
│  ├── get_abandonment_analysis  → Athena (CTR)                   │
│  ├── get_agent_utilization     → Athena (Agent Events)          │
│  └── trigger_sla_alert         → EventBridge                    │
│                                                                  │
│  QUALITY AGENT (Claude Sonnet)                                  │
│  ├── get_sentiment_trends      → Athena (Contact Lens) + Chart  │
│  ├── get_coaching_recommendations → Athena (Contact Lens)       │
│  └── get_compliance_violations → Athena (Contact Lens) + Alert  │
│                                                                  │
│  WFM AGENT (Nova Lite)                                          │
│  ├── get_staffing_forecast     → Athena (CTR) + Chart           │
│  └── get_burnout_signals       → Athena (Agent Events) + Alert  │
│                                                                  │
│  SHARED                                                          │
│  ├── AgentCore Gateway         → Routes all tool invocations    │
│  ├── Athena Client             → Query execution + polling      │
│  ├── Error Handler             → Sanitizes errors for users     │
│  ├── Circuit Breaker           → In-memory, 5 failures → open  │
│  └── Alert Publisher           → EventBridge PutEvents wrapper  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│  LEAST PRIVILEGE IAM                                             │
│                                                                  │
│  AgentCore Role:                                                │
│  ├── s3:GetObject, s3:ListBucket  (scoped to demo bucket)      │
│  ├── athena:StartQueryExecution    (scoped to workgroup)        │
│  ├── athena:GetQueryResults        (scoped to workgroup)        │
│  └── glue:GetTable, GetDatabase    (scoped to connect_analytics)│
│                                                                  │
│  Tool Lambda Role:                                              │
│  ├── s3:GetObject                  (scoped to data prefixes)    │
│  ├── athena:*QueryExecution        (scoped to workgroup)        │
│  ├── events:PutEvents              (alert tools only)           │
│  ├── polly:SynthesizeSpeech        (voice tools only)           │
│  └── s3:PutObject                  (chart upload, reports/ only)│
│                                                                  │
│  Alert Pipeline Role:                                           │
│  ├── sns:Publish                   (scoped to alert topics)     │
│  └── logs:PutLogEvents             (CloudWatch logging)         │
│                                                                  │
│  RBAC Enforcement:                                              │
│  ├── supervisor    → Supervisor Agent only                      │
│  ├── qa_analyst    → Quality Agent only                         │
│  └── wfm_planner   → WFM Agent only                            │
│                                                                  │
│  Error Sanitization:                                            │
│  ├── No SQL in user-facing errors                               │
│  ├── No table/column names                                      │
│  ├── No stack traces                                            │
│  ├── No ARNs or account IDs                                     │
│  └── Correlation ID included for support                        │
└─────────────────────────────────────────────────────────────────┘
```
