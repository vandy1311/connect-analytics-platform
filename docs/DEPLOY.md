# Connect Analytics Platform — Deployment Guide

## Prerequisites

Before deploying, ensure you have:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| AWS CLI | v2+ | `aws --version` |
| AWS CDK | v2.150+ | `cdk --version` |
| Python | 3.12+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| Docker | Running | `docker info` |
| AWS Account | With Bedrock access | `aws sts get-caller-identity` |

### AWS Permissions Needed

Your IAM user/role needs permissions for:
- CloudFormation (stack management)
- S3 (data lake bucket)
- Lambda (tool functions)
- ECR (Docker image push)
- Athena + Glue (query engine)
- Bedrock (AgentCore + Knowledge Base)
- EventBridge + SNS (alerts)
- Secrets Manager (auth tokens)
- IAM (role creation)

> **Tip:** Use `AdministratorAccess` for the hackathon. Scope down for production.

### Enable Bedrock Models

In the AWS Console → Bedrock → Model access, enable:
- `anthropic.claude-sonnet-4` (Supervisor + Quality agents)
- `amazon.nova-lite-v2:0` (WFM agent)
- `amazon.titan-embed-text-v2:0` (Knowledge Base embeddings)

---

## Step 1: Clone & Install (2 minutes)

```bash
git clone https://github.com/vandy1311/connect-analytics-platform.git
cd connect-analytics-platform

# Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Step 2: Generate Synthetic Data (30 seconds)

```bash
python scripts/generate_synthetic_data.py --output-dir output
```

This creates 70K records:
- `output/ctr/` — 10K Contact Trace Records (Parquet)
- `output/agent-events/` — 50K Agent Event records (Parquet)
- `output/contact-lens/` — 10K Contact Lens analyses (JSON)

## Step 3: Configure (30 seconds)

Edit `cdk.json` context or pass parameters via CLI:

```bash
# Option A: Edit cdk.json
# Set your account ID and region in the "context" section

# Option B: Pass via CLI (recommended)
export CDK_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_REGION=us-east-1
```

### Optional: Point to Your Own S3 Bucket

If you already have Connect data in S3:
```bash
# Deploy with your existing bucket
cdk deploy --all \
  -c account=$CDK_ACCOUNT \
  -c region=$CDK_REGION \
  -c data_lake_bucket=your-existing-bucket-name
```

If omitted, CDK creates a new bucket: `connect-analytics-{account}-{region}`

## Step 4: Bootstrap CDK (first time only, 1 minute)

```bash
cdk bootstrap aws://$CDK_ACCOUNT/$CDK_REGION
```

## Step 5: Deploy (~8 minutes)

```bash
cdk deploy --all \
  -c account=$CDK_ACCOUNT \
  -c region=$CDK_REGION
```

CDK automatically:
1. ✅ Builds Docker images for Lambda tools → pushes to ECR
2. ✅ Creates S3 bucket + Glue catalog (3 tables) + Athena workgroup
3. ✅ Stores auth tokens in Secrets Manager
4. ✅ Deploys AgentCore Gateway + 3 AI agents
5. ✅ Creates Knowledge Base with SOPs and compliance docs
6. ✅ Wires EventBridge → SNS (5 topics) → Slack formatter Lambda
7. ✅ Outputs agent endpoints + gateway ID

### What Gets Created (5 stacks)

| Stack | Resources |
|-------|-----------|
| `ConnectAnalytics-Auth` | Secrets Manager secret (auth tokens) |
| `ConnectAnalytics-Data` | S3 bucket, Glue database + 3 tables, Athena workgroup |
| `ConnectAnalytics-KB` | S3 bucket (docs), Bedrock Knowledge Base, data source |
| `ConnectAnalytics-Agents` | Tool Lambda (Docker), AgentCore Gateway, 3 agents |
| `ConnectAnalytics-Alerts` | Slack secret, Slack Lambda, 5 SNS topics, 5 EventBridge rules |

## Step 6: Upload Data to S3

```bash
# Upload synthetic data to the S3 bucket
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name ConnectAnalytics-Data \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text)

aws s3 sync output/ctr/ s3://$BUCKET/ctr/
aws s3 sync output/agent-events/ s3://$BUCKET/agent-events/
aws s3 sync output/contact-lens/ s3://$BUCKET/contact-lens/
```

## Step 7: Configure Slack Alerts (optional)

```bash
# Store your Slack webhook URL in Secrets Manager
aws secretsmanager put-secret-value \
  --secret-id connect-analytics/slack-webhook \
  --secret-string "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## Step 8: Verify ✅

```bash
# Check stack outputs
cdk list
aws cloudformation describe-stacks --stack-name ConnectAnalytics-Agents \
  --query "Stacks[0].Outputs" --output table

# Run tests
pytest tests/ -v
```

## Step 9: Launch Demo UI

```bash
cd demo_ui
pip install streamlit plotly matplotlib
streamlit run app.py
```

Open http://localhost:8501 — agents are live, querying your data via Athena.

---

## Cleanup

```bash
cdk destroy --all
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `cdk bootstrap` fails | Ensure your IAM user has CloudFormation + S3 + ECR permissions |
| Docker build fails | Ensure Docker Desktop is running: `docker info` |
| Bedrock model access denied | Enable models in AWS Console → Bedrock → Model access |
| Athena query fails | Check Glue tables exist: `aws glue get-tables --database-name connect_analytics` |
| Slack alerts not arriving | Verify webhook URL in Secrets Manager: `aws secretsmanager get-secret-value --secret-id connect-analytics/slack-webhook` |
