#!/usr/bin/env python3
"""Convert pitch one-pager to Word format."""
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

# Title
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Connect Analytics Platform")
run.bold = True
run.font.size = Pt(24)
run.font.color.rgb = RGBColor(0xFF, 0x99, 0x00)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Team FIFA | CSM Agentic Hackathon 2026")
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_paragraph()

# Headline
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Three AI agents. One command to deploy. $34/month. Every answer in 2 seconds.")
run.bold = True
run.font.size = Pt(14)

doc.add_paragraph()
doc.add_paragraph()

# The Problem
h = doc.add_heading("The Problem", level=1)
h.runs[0].font.color.rgb = RGBColor(0xE7, 0x4C, 0x3C)

problems = [
    "Every Connect deployment hits the same wall on Day 2",
    "Supervisors check 5 dashboards to answer one question — takes 20 minutes",
    "Customers build custom Kinesis → Lambda → S3 → QuickSight pipelines — costs $150K+/year",
    "No native natural language query interface for supervisors",
    "No automated coaching from Contact Lens data",
    "Burnout detected after agents quit — 25% annual attrition",
]
for p in problems:
    doc.add_paragraph(p, style="List Bullet")

# The Solution
h = doc.add_heading("The Solution", level=1)
h.runs[0].font.color.rgb = RGBColor(0x2E, 0xCC, 0x71)

doc.add_paragraph(
    "Three specialized AI agents on Bedrock AgentCore that answer the questions "
    "contact center teams actually ask — in natural language, with actions attached."
)

table = doc.add_table(rows=4, cols=4)
table.style = "Light Grid Accent 1"
headers = ["Agent", "Persona", "Model", "Capability"]
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h

data = [
    ["Supervisor", "Floor manager", "Claude Sonnet 4", "Queue health, SLA alerts, abandonment RCA"],
    ["Quality", "QA / Compliance", "Claude Sonnet 4", "Sentiment, coaching, compliance violations"],
    ["WFM", "Workforce planner", "Nova Lite 2", "Staffing forecasts, burnout detection"],
]
for r, row_data in enumerate(data):
    for c, val in enumerate(row_data):
        table.rows[r + 1].cells[c].text = val

doc.add_paragraph()

# Key Metrics
h = doc.add_heading("Key Metrics", level=1)
h.runs[0].font.color.rgb = RGBColor(0x34, 0x98, 0xDB)

metrics_table = doc.add_table(rows=7, cols=3)
metrics_table.style = "Light Grid Accent 1"
metrics_headers = ["Metric", "Before", "After"]
for i, h in enumerate(metrics_headers):
    metrics_table.rows[0].cells[i].text = h

metrics = [
    ["Time to insight", "20 minutes", "2 seconds"],
    ["Analytics cost", "$150K/year", "$34/month"],
    ["Call coverage", "2% (manual QA)", "100% (AI-powered)"],
    ["SLA breach detection", "15+ min late", "< 60 seconds"],
    ["Burnout detection", "After they quit", "8 days early"],
    ["Deploy time", "3 months", "8 minutes"],
]
for r, row_data in enumerate(metrics):
    for c, val in enumerate(row_data):
        metrics_table.rows[r + 1].cells[c].text = val

doc.add_paragraph()

# Story Arc
h = doc.add_heading("Story Arc", level=1)
h.runs[0].font.color.rgb = RGBColor(0xFF, 0x99, 0x00)

acts = [
    ("Act 1 — The Problem",
     "A 200-agent contact center. Supervisors drowning in dashboards. SLA breaches "
     "going unnoticed for 15 minutes. Agents burning out and quitting. $150K/year spent "
     "on custom analytics that still can't answer a simple question in real time."),
    ("Act 2 — Team FIFA Steps In",
     "Three CSMs — Brigette, Yunjie, and Vandana — saw this pattern across every Connect "
     "engagement. They built the solution in 10 days using AI-DLC methodology and Kiro IDE."),
    ("Act 3 — The Solution",
     "One command. 8 minutes. Three AI agents that talk to your data and take action. "
     "Ask a question in English, get an answer in 2 seconds. SLA breach? Slack alert fires "
     "in under 60 seconds. Agent burning out? Detected 8 days before they quit."),
    ("Act 4 — The Impact",
     "$150K/year → $34/month. 20 minutes → 2 seconds. 2% call coverage → 100%. "
     "Any CSM can deploy it for their customer in their first week."),
]
for title, body in acts:
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(12)
    doc.add_paragraph(body)

# Differentiators
h = doc.add_heading("Differentiators", level=1)
h.runs[0].font.color.rgb = RGBColor(0x9B, 0x59, 0xB6)

diffs = [
    "Agents collaborate — Supervisor detects burnout → WFM adjusts schedules → Quality schedules coaching",
    "Knowledge base enrichment — agents cite SOPs and policies in their responses",
    "One-command deploy — cdk deploy with 3 parameters, done in 8 minutes",
    "Cost model — $34/month vs $150K/year for custom pipelines",
    "Voice output — hear responses spoken aloud, hands-free for floor supervisors",
    "Real Slack integration — alerts fire live during the demo",
]
for d in diffs:
    doc.add_paragraph(d, style="List Bullet")

# AWS Services
h = doc.add_heading("AWS Services Featured", level=1)
services = [
    "Amazon Bedrock AgentCore (primary)",
    "Claude Sonnet 4 + Nova Lite 2",
    "Amazon Athena + Glue",
    "EventBridge + SNS",
    "Amazon Polly (Neural voice)",
    "Bedrock Knowledge Base + Titan Embed v2",
    "AWS CDK (Python)",
]
for s in services:
    doc.add_paragraph(s, style="List Bullet")

# Footer
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Built with AI-DLC methodology • Powered by Kiro IDE")
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

doc.save("docs/pitch-one-pager.docx")
print("Saved: docs/pitch-one-pager.docx")
