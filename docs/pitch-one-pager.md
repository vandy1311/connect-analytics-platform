# Connect Analytics Platform — Pitch One-Pager

## Team FIFA | CSM Agentic Hackathon 2026

---

## Headline

Three AI agents. One command to deploy. $34/month. Every answer in 2 seconds.

---

## The Problem (use these talking points)

- Every Connect deployment hits the same wall on Day 2
- Supervisors check 5 dashboards to answer one question — takes 20 minutes
- Customers build custom Kinesis → Lambda → S3 → QuickSight pipelines — costs $150K+/year
- No native NL query interface for supervisors
- No automated coaching from Contact Lens data
- Burnout detected after agents quit — 25% annual attrition

---

## The Solution (elevator pitch)

Three specialized AI agents on Bedrock AgentCore that answer the questions contact center teams actually ask — in natural language, with actions attached.

| Agent | Who Uses It | Key Capability |
|-------|------------|----------------|
| Supervisor Agent (Claude Sonnet 4) | Floor managers | "Show me queue health" → instant answer + Slack alert |
| Quality Agent (Claude Sonnet 4) | QA analysts | "Which agents need coaching?" → sentiment analysis + recommendations |
| WFM Agent (Nova Lite 2) | Workforce planners | "Forecast next Monday" → staffing chart + burnout detection |

---

## Key Metrics (for the ad)

| Metric | Before | After |
|--------|--------|-------|
| Time to insight | 20 minutes | 2 seconds |
| Analytics cost | $150K/year | $34/month |
| Call coverage | 2% (manual QA) | 100% (AI-powered) |
| SLA breach detection | 15+ min late | < 60 seconds |
| Burnout detection | After they quit | 8 days early |
| Deploy time | 3 months | 8 minutes |

---

## Story Arc (for the advertisement)

### Act 1 — The Problem
A 200-agent contact center. Supervisors drowning in dashboards. SLA breaches going unnoticed for 15 minutes. Agents burning out and quitting. $150K/year spent on custom analytics that still can't answer a simple question in real time.

### Act 2 — Team FIFA Steps In
Three CSMs — Brigette, Yunjie, and Vandana — saw this pattern across every Connect engagement. They built the solution in 10 days using AI-DLC methodology and Kiro IDE.

### Act 3 — The Solution
One command. 8 minutes. Three AI agents that talk to your data and take action. Ask a question in English, get an answer in 2 seconds. SLA breach? Slack alert fires in under 60 seconds. Agent burning out? Detected 8 days before they quit.

### Act 4 — The Impact
$150K/year → $34/month. 20 minutes → 2 seconds. 2% call coverage → 100%. Any CSM can deploy it for their customer in their first week.

---

## Differentiators (what makes this win)

1. Agents collaborate — Supervisor detects burnout → WFM adjusts schedules → Quality schedules coaching. Automatically.
2. Knowledge base enrichment — agents cite SOPs and policies in their responses
3. One-command deploy — `cdk deploy` with 3 parameters, done in 8 minutes
4. Cost model — $34/month vs $150K/year for custom pipelines
5. Voice output — hear responses spoken aloud, hands-free for floor supervisors
6. Real Slack integration — alerts fire live during the demo

---

## Quote (for the ad)

"We were spending $150K/year on a custom analytics pipeline and our supervisors still couldn't get real-time answers. Now they ask a question and get an answer in 2 seconds — with a Slack alert if something's wrong."

---

## Call to Action Options

- "Deploy for your next Connect customer — 8 minutes, zero maintenance"
- "Turn Connect data into decisions — ask us for a demo"
- "Built in a hackathon. Ready for production. $34/month."

---

## Visual Suggestions (for whoever designs the ad)

- Split screen: left side = supervisor drowning in 5 dashboard tabs, right side = clean chat interface with instant answer
- Slack notification popping up in real time
- Architecture diagram showing the 3 agents
- Cost comparison: big red $150K crossed out → green $34/mo
- Team FIFA photo with soccer ball emojis

---

## AWS Services Featured (for internal positioning)

- Amazon Bedrock AgentCore (primary — this is the hero)
- Claude Sonnet 4 + Nova Lite 2 (model diversity story)
- Amazon Athena + Glue (serverless analytics)
- EventBridge + SNS (event-driven alerts)
- Amazon Polly (voice output)
- AWS CDK (infrastructure as code)
- Bedrock Knowledge Base + Titan Embed v2 (RAG)

---

## Methodology

Built using AI-DLC (AI Development Lifecycle) with Kiro IDE — spec-driven development from requirements through design, implementation, and testing. 88 automated tests. Full traceability from requirements to code.
