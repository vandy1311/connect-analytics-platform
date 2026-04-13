# Execution Plan — Connect Analytics Platform

## Timeline

| Date | Milestone | Owner |
|------|-----------|-------|
| Apr 6 | Hackathon officially starts | All |
| Apr 6–8 | Step 1: Data Foundation (S3 + Glue + Athena + Synthetic Data) | Yunjie |
| Apr 8–9 | Step 2: Supervisor Agent (AgentCore Gateway + first agent) | Yunjie |
| Apr 9–10 | Step 3: Alert Pipeline (EventBridge + SNS → Slack) | Vandana |
| Apr 10–11 | Step 4: Quality + WFM Agents (repeat pattern + charts) | Brigette + Vandana |
| Apr 11–12 | Step 5: Polly Voice Output | Brigette |
| Apr 12–13 | Step 6: CDK Stack Assembly (one-command deploy) | Yunjie |
| Apr 13–14 | Step 7: Demo Dry-Run (validate all 8 queries) | All |
| Apr 15 | Submission deadline | All |
| Apr 16–23 | Yunjie OOO | — |

## Build Order

```
Step 1 → Data Foundation    (S3 + Glue 3 tables + Athena + Synthetic Data)
Step 2 → Supervisor Agent   (AgentCore — verify Gateway first)
Step 3 → Alerts             (EventBridge + SNS → Slack — live demo moment)
Step 4 → Quality + WFM      (repeat pattern + charts)
Step 5 → Polly              (wire voice into AgentCore response)
Step 6 → CDK                (lean hackathon deploy — one command)
Step 7 → Demo Dry-Run       (validate all 8 scripted responses)
```

## Prerequisites Checklist

- [ ] AWS account with Amazon Bedrock enabled (Yunjie's Isengard account)
- [ ] AgentCore access enabled (may require service quota request)
- [ ] AgentCore Gateway quota enabled
- [ ] Claude Sonnet and Nova Lite model access granted in Bedrock console
- [ ] Amazon Polly Neural voices enabled
- [ ] S3 bucket created (or will be created by CDK on deploy)
- [ ] Docker Desktop running locally (CDK uses it to build Lambda container images)
- [ ] AWS CDK v2 installed (`npm install -g aws-cdk`)
- [ ] AWS CLI configured with deploy permissions
- [ ] Slack workspace with webhook URL for alert testing

## Team Responsibilities

| Member | Primary Focus | Secondary |
|--------|--------------|-----------|
| Yunjie | Data foundation, AgentCore agents, CDK stack | Infrastructure, account access |
| Brigette | Quality Agent, Polly integration, demo script | AI-DLC methodology, coaching |
| Vandana | Alert pipeline, WFM Agent, Supervisor tools | Testing, integration |

## Risk Register

| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|-----------|-------|
| AgentCore Gateway API not GA | Medium | Critical | Verify API Day 1 before coding | Yunjie |
| Team OOO conflicts (Yunjie Apr 16–23) | Certain | High | Must be done by Apr 15; Yunjie drives infra early | All |
| Lambda container cold starts | Low | Medium | Pre-warm before demo | Yunjie |
| Synthetic data doesn't match demo script | Medium | High | Validation query in Step 1d confirms patterns | Yunjie |
| Slack webhook config issues | Low | Medium | Test webhook independently in Step 3 | Vandana |

## Demo Validation Checklist

| # | Query | Expected Response | Speaker | Status |
|---|-------|-------------------|---------|--------|
| 1 | "Show me queue health right now" | Billing queue 12 min wait, SLA breach, 14% abandonment | Vandana | ☐ |
| 2 | "Why did abandonment spike at 2pm?" | 2 agents on break, 96% occupancy for 18 min | Vandana | ☐ |
| 3 | LIVE: EventBridge → Slack | ⚠️ SLA breach alert fires in Slack | LIVE | ☐ |
| 4 | "Which agents need coaching this week?" | Agent-017: 4 negative calls, interruption pattern | Brigette | ☐ |
| 5 | "Show me the worst call" | Transcript + sentiment chart | Brigette | ☐ |
| 6 | "Forecast staffing for next Monday" | 340 contacts 10am-2pm, need 22, have 18 + chart | Yunjie | ☐ |
| 7 | "Any agents showing burnout signals?" | Agent-023/031: >92% occupancy for 8 days | Yunjie | ☐ |
| 8 | Live `cdk deploy` | Stack deploys in ~8 min | Brigette | ☐ |

## What We're NOT Building

| You Don't Need | Why |
|----------------|-----|
| EKS / ECS / Fargate | AgentCore is fully managed |
| API Gateway | AgentCore Gateway handles tool routing |
| LangChain / custom orchestration | AgentCore handles multi-step tool execution |
| Session management code | AgentCore manages session state |
| Custom retry logic | AgentCore handles LLM retries and tool failures |
| ECR repo setup | CDK DockerImageCode creates and pushes automatically |
| Amazon Bedrock Agents (original) | Different product, different SDK, different billing |

## Cost Estimate

| Service | Monthly Estimate |
|---------|-----------------|
| Bedrock AgentCore (Sonnet) | ~$15–25 |
| Bedrock AgentCore (Nova Lite) | ~$1–3 |
| AgentCore Gateway | ~$0.23 |
| Athena | ~$0.75 |
| Lambda | ~$2 |
| S3 | ~$0.23 |
| EventBridge + SNS | ~$0.10 |
| Polly | ~$2 |
| CloudWatch | ~$0.25 |
| **Total** | **~$22–34/mo** |

## Definition of Done

- [ ] All 8 demo queries return correct responses against synthetic data
- [ ] Slack alert fires live during demo
- [ ] `cdk deploy` completes in < 10 minutes with 3 parameters
- [ ] Sentiment and forecast charts render as valid PNGs
- [ ] Voice output works for at least one query
- [ ] No raw SQL or stack traces in any user-facing error
- [ ] All code in a single CDK project, deployable from Yunjie's Isengard account
