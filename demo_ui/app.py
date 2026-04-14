"""
Connect Analytics Platform — Demo UI
Streamlit app for hackathon demo with 3 agent tabs + architecture view.
Run: streamlit run demo_ui/app.py
"""

import base64
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Slack integration
# ---------------------------------------------------------------------------
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Load from .env file if present
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "SLACK_WEBHOOK_URL" and v.strip():
                SLACK_WEBHOOK_URL = v.strip()


def post_to_slack(alert: dict) -> bool:
    """Post an alert to Slack via webhook. Returns True on success."""
    if not SLACK_WEBHOOK_URL or "YOUR" in SLACK_WEBHOOK_URL:
        return False

    emoji_map = {
        "SLA_BREACH": "🚨",
        "COMPLIANCE_VIOLATION": "🛑",
        "BURNOUT_RISK": "🔥",
    }
    emoji = emoji_map.get(alert["type"], "⚠️")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {alert['type'].replace('_', ' ').title()}", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Time:* {alert['time']}\n{alert['message']}"},
        },
    ]

    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Connect Analytics Platform",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── Global ── */
    .stApp { background: linear-gradient(160deg, #0a1628 0%, #1a2744 50%, #0d1f3c 100%); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0; padding: 10px 24px;
        font-weight: 600; font-size: 0.95rem;
    }

    /* ── Agent headers ── */
    .supervisor-header { color: #2ecc71; border-left: 4px solid #2ecc71; padding-left: 14px; font-size: 1.5rem; }
    .quality-header { color: #FF9900; border-left: 4px solid #FF9900; padding-left: 14px; font-size: 1.5rem; }
    .wfm-header { color: #3498db; border-left: 4px solid #3498db; padding-left: 14px; font-size: 1.5rem; }

    /* ── Chat bubbles ── */
    .user-msg {
        background: linear-gradient(135deg, #1e3a5f, #1a2f4a); border-radius: 16px; padding: 14px 18px;
        margin: 10px 0; border-left: 4px solid #3498db; color: #e8e8e8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    .agent-msg {
        background: linear-gradient(135deg, #162d1f, #1a3328); border-radius: 16px; padding: 14px 18px;
        margin: 10px 0; border-left: 4px solid #2ecc71; color: #e8e8e8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* ── Slack alerts in sidebar ── */
    .slack-alert {
        background: linear-gradient(135deg, #1e2a3a, #1a2540); border: 1px solid #2a3a50;
        border-radius: 10px; padding: 12px 14px; margin: 8px 0; font-size: 0.85rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2); color: #e8e8e8;
    }
    .slack-alert .alert-type { font-weight: 700; font-size: 0.95rem; }
    .slack-alert.sla { border-left: 4px solid #e74c3c; }
    .slack-alert.compliance { border-left: 4px solid #FF9900; }
    .slack-alert.burnout { border-left: 4px solid #3498db; }

    /* ── Hero banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #FF9900 0%, #e88600 50%, #cc7700 100%);
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px; text-align: center;
        box-shadow: 0 4px 20px rgba(255,153,0,0.3);
    }
    .hero-banner h1 { color: #0a1628; font-size: 2.2rem; margin: 0; font-weight: 800; }
    .hero-banner p { color: #1a2744; font-size: 1rem; margin: 4px 0 0 0; font-weight: 500; }

    /* ── Agent cards on Architecture tab ── */
    .agent-card {
        border-radius: 12px; padding: 18px; margin: 8px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .agent-card.sup { background: linear-gradient(135deg, #0d2818, #1a3d28); border: 1px solid #2ecc71; }
    .agent-card.qual { background: linear-gradient(135deg, #2d1a00, #3d2800); border: 1px solid #FF9900; }
    .agent-card.wfm { background: linear-gradient(135deg, #0d1a2d, #1a2d44); border: 1px solid #3498db; }

    /* ── Sidebar styling ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1a2d 0%, #131a2e 100%);
    }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2744, #1e3050);
        border: 1px solid #2a3a55; border-radius: 12px; padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    [data-testid="stMetricValue"] { color: #FF9900; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar — Slack alert feed + architecture
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("diagrams/architecture.png", width="stretch")
    st.markdown("---")

    # Voice toggle
    st.markdown("### 🔊 Voice Output")
    voice_enabled = st.toggle("Enable Nova Sonic voice", value=False, key="voice_toggle")
    if voice_enabled:
        st.caption("Agent responses will be spoken aloud via Nova Sonic on Bedrock")
    else:
        st.caption("Text-only mode")

    st.markdown("---")

    # Slack status
    st.markdown("### 💬 Slack Integration")
    if SLACK_WEBHOOK_URL and "YOUR" not in SLACK_WEBHOOK_URL:
        st.success("Connected", icon="✅")
        st.caption("Alerts will post to Slack in real time")
    else:
        st.warning("Not configured", icon="⚠️")
        st.caption("Add webhook URL to demo_ui/.env")

    st.markdown("---")
    st.markdown("### 🔔 Slack Alert Feed")

    if "alerts" not in st.session_state:
        st.session_state.alerts = []

    for alert in reversed(st.session_state.alerts):
        css_class = "sla" if "SLA" in alert["type"] else "burnout" if "BURNOUT" in alert["type"] else "compliance"
        st.markdown(f"""
        <div class="slack-alert {css_class}">
            <span class="alert-type">{alert['emoji']} {alert['type']}</span><br>
            <span style="color:#5f6b7a">{alert['time']}</span><br>
            {alert['message']}
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.alerts:
        st.caption("Alerts will appear here during the demo...")

    st.markdown("---")
    st.markdown("### 💰 Estimated Cost")
    st.metric("Monthly (demo load)", "$22–34")
    st.caption("AgentCore + Athena + Lambda + S3 + SNS")


# ---------------------------------------------------------------------------
# Main content — Agent tabs
# ---------------------------------------------------------------------------
st.markdown("""
<div style="position:relative; overflow:hidden; border-radius:16px; margin-bottom:24px;
            background: linear-gradient(135deg, #FF9900 0%, #e88600 40%, #232f3e 100%);
            padding: 40px 32px; text-align:center;
            box-shadow: 0 4px 30px rgba(255,153,0,0.4);">
    <!-- Animated floating circles -->
    <style>
        @keyframes float1 { 0%,100% { transform: translateY(0px) translateX(0px); } 50% { transform: translateY(-20px) translateX(10px); } }
        @keyframes float2 { 0%,100% { transform: translateY(0px) translateX(0px); } 50% { transform: translateY(-15px) translateX(-15px); } }
        @keyframes float3 { 0%,100% { transform: translateY(0px); } 50% { transform: translateY(-25px); } }
        @keyframes pulse { 0%,100% { opacity: 0.6; } 50% { opacity: 1; } }
        @keyframes slideIn { 0% { opacity:0; transform:translateY(20px); } 100% { opacity:1; transform:translateY(0); } }
        .hero-circle {
            position:absolute; border-radius:50%; opacity:0.15;
            background: radial-gradient(circle, #fff 0%, transparent 70%);
        }
        .hero-title { animation: slideIn 0.8s ease-out; }
        .hero-sub { animation: slideIn 1s ease-out 0.2s both; }
        .hero-badges { animation: slideIn 1.2s ease-out 0.4s both; }
        .hero-badge {
            display:inline-block; background:rgba(0,0,0,0.3); color:#FF9900;
            padding:6px 14px; border-radius:20px; margin:4px; font-size:0.8rem;
            font-weight:600; border:1px solid rgba(255,153,0,0.3);
        }
    </style>
    <div class="hero-circle" style="width:120px;height:120px;top:-30px;left:10%;animation:float1 6s ease-in-out infinite;"></div>
    <div class="hero-circle" style="width:80px;height:80px;top:20px;right:15%;animation:float2 8s ease-in-out infinite;"></div>
    <div class="hero-circle" style="width:60px;height:60px;bottom:-10px;left:40%;animation:float3 5s ease-in-out infinite;"></div>
    <div class="hero-circle" style="width:100px;height:100px;bottom:10px;right:5%;animation:float1 7s ease-in-out infinite;"></div>
    <div class="hero-title" style="position:relative;">
        <span style="font-size:3rem;">🎧</span>
        <h1 style="color:#0a1628; font-size:2.4rem; margin:8px 0 0 0; font-weight:800; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            Connect Analytics Platform
        </h1>
    </div>
    <p class="hero-sub" style="color:#1a2744; font-size:1.1rem; margin:8px 0 16px 0; font-weight:500;">
        Three AI agents that turn Amazon Connect data into decisions
    </p>
    <div class="hero-badges">
        <span class="hero-badge">🟢 Supervisor · Claude Sonnet</span>
        <span class="hero-badge">🟠 Quality · Claude Sonnet</span>
        <span class="hero-badge">🔵 WFM · Nova Lite</span>
        <span class="hero-badge">⚡ Bedrock AgentCore</span>
        <span class="hero-badge">📊 S3 + Athena</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab_sup, tab_qual, tab_wfm, tab_dash, tab_kb, tab_arch = st.tabs([
    "🟢 Supervisor", "🟠 Quality", "🔵 WFM", "📊 Dashboard", "📚 Knowledge Base", "📐 Architecture"
])


# ---------------------------------------------------------------------------
# Demo response simulator — returns canned responses matching demo script
# ---------------------------------------------------------------------------

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from lambda_tools.shared.knowledge_base import retrieve as kb_retrieve


def simulate_agent_response(agent: str, query: str) -> dict:
    """Return a simulated agent response matching the demo script."""
    q = query.lower()

    # ── Supervisor queries ──
    if "queue health" in q:
        return {
            "text": (
                "**Queue Health Summary (Last 60 min)**\n\n"
                "⚠️ **Billing Queue — SLA BREACH**\n"
                "- Queue size: 87 contacts\n"
                "- Longest wait: 12 min 0 sec\n"
                "- Service level: 68.5% *(threshold: 80%)*\n"
                "- Avg handle time: 5 min 45 sec\n"
                "- Abandonment: 14%\n\n"
                "✅ **Sales Queue — Healthy**\n"
                "- Queue size: 32 contacts\n"
                "- Longest wait: 3 min 0 sec\n"
                "- Service level: 82.0%\n\n"
                "**Recommendation:** Pull 2 agents from Technical queue to Billing immediately."
            ),
            "alert": {
                "type": "SLA_BREACH",
                "emoji": "🚨",
                "message": "Billing queue at 68.5% SLA (threshold 80%). 87 contacts waiting, longest wait 12 min.",
            },
            "metrics": [
                {"label": "Billing SLA", "value": "68.5%", "delta": "-11.5%"},
                {"label": "Queue Size", "value": "87", "delta": "+23"},
                {"label": "Longest Wait", "value": "12 min", "delta": "+8 min"},
                {"label": "Abandonment", "value": "14%", "delta": "+9%"},
            ],
        }

    if "abandonment" in q or "spike" in q:
        return {
            "text": (
                "**Abandonment Root Cause Analysis — 2:00 PM**\n\n"
                "📉 Abandonment spiked to **18%** at 2:00 PM (baseline: 5%)\n\n"
                "**Root Cause:** Two agents (Agent-001 and Agent-002) went on break "
                "simultaneously at 1:58 PM. With peak volume (3x normal) hitting at the "
                "same time, occupancy surged to **96%** for 18 minutes.\n\n"
                "**Impact:**\n"
                "- 18 contacts abandoned in the 2:00–2:18 PM window\n"
                "- Average wait before abandon: 12 min 0 sec\n"
                "- Billing queue was most affected (14 of 18 abandons)\n\n"
                "**Recommendation:** Stagger break schedules during 10 AM–2 PM peak. "
                "Never allow more than 1 agent on break per queue during peak hours."
            ),
            "metrics": [
                {"label": "Peak Abandon Rate", "value": "18%", "delta": "+13%"},
                {"label": "Peak Hour", "value": "2:00 PM", "delta": ""},
                {"label": "Contacts Lost", "value": "18", "delta": ""},
                {"label": "Occupancy Peak", "value": "96%", "delta": "+21%"},
            ],
        }

    if "utilization" in q or "who" in q and "available" in q:
        return {
            "text": (
                "**Agent Utilization (Last 8 hours)**\n\n"
                "| Agent | Occupancy | Status | Handle Time | Contacts |\n"
                "|-------|-----------|--------|-------------|----------|\n"
                "| Agent-023 | 98% | ON_CALL | 7 min 12 sec | 34 |\n"
                "| Agent-031 | 96% | ON_CALL | 6 min 48 sec | 31 |\n"
                "| Agent-017 | 93% | ACW | 8 min 15 sec | 28 |\n"
                "| Agent-005 | 72% | AVAILABLE | 5 min 30 sec | 22 |\n"
                "| Agent-012 | 45% | AVAILABLE | 4 min 50 sec | 18 |\n\n"
                "⚠️ Agent-023 and Agent-031 are running critically high. Consider reassignment."
            ),
        }

    # ── Quality queries ──
    if "coaching" in q or "agents need" in q:
        return {
            "text": (
                "**Coaching Recommendations (This Week)**\n\n"
                "🔴 **Agent-017** — Negative sentiment rate: **30%** (4 negative calls)\n"
                "- Pattern: Frequent interruptions during customer explanations\n"
                "- Sample: *\"Customer was upset about billing error — agent cut off mid-sentence\"*\n"
                "- **Recommendation:** De-escalation coaching + active listening module\n\n"
                "🟡 **Agent-009** — Negative sentiment rate: **20%**\n"
                "- Pattern: Long hold times without status updates\n"
                "- **Recommendation:** Hold management training + empathy refresher\n\n"
                "All other agents are below the 15% threshold."
            ),
        }

    if "worst call" in q or "sentiment" in q:
        return {
            "text": (
                "**Sentiment Trends (Last 7 Days)**\n\n"
                "Monday shows a clear negative spike — 25% negative vs 15% baseline.\n\n"
                "**Worst Call — Agent-017, Monday 2:14 PM**\n"
                "- Overall sentiment: NEGATIVE (-3.8)\n"
                "- Categories: Escalation, Billing\n"
                "- Transcript excerpt: *\"I've been on hold for 20 minutes and nobody "
                "can tell me why I was charged twice...\"*\n"
                "- Agent interrupted customer 3 times in first 2 minutes\n"
                "- Call escalated to supervisor at 8:42 mark"
            ),
            "chart": "sentiment",
        }

    if "compliance" in q or "violation" in q:
        return {
            "text": (
                "**Compliance Violations (Last 7 Days)**\n\n"
                "Found **12 violations** across 3 types:\n\n"
                "| Type | Count | Severity |\n"
                "|------|-------|----------|\n"
                "| MISSING_DISCLOSURE | 7 | MEDIUM |\n"
                "| PCI_VIOLATION | 3 | HIGH |\n"
                "| SCRIPT_DEVIATION | 2 | LOW |\n\n"
                "🛑 **3 PCI violations flagged for immediate review** — "
                "agents read full card numbers aloud on recorded lines."
            ),
            "alert": {
                "type": "COMPLIANCE_VIOLATION",
                "emoji": "🛑",
                "message": "3 PCI violations detected this week. Agents reading card numbers on recorded lines.",
            },
        }

    # ── WFM queries ──
    if "forecast" in q or "staffing" in q or "next monday" in q:
        return {
            "text": (
                "**Staffing Forecast — Next Monday**\n\n"
                "📊 Projected contact volume: **340 contacts** between 10 AM–2 PM (peak)\n\n"
                "| Time Slot | Predicted | Current Staff | Recommended | Gap |\n"
                "|-----------|-----------|---------------|-------------|-----|\n"
                "| 10–11 AM | 78 | 5 | 6 | -1 |\n"
                "| 11–12 PM | 92 | 5 | 7 | -2 |\n"
                "| 12–1 PM | 88 | 4 | 6 | -2 |\n"
                "| 1–2 PM | 82 | 4 | 6 | -2 |\n\n"
                "**Recommendation:** Activate 4 agents from flex pool for 10 AM–2 PM. "
                "Confidence interval: 310–370 contacts (±9%)."
            ),
            "chart": "forecast",
        }

    if "burnout" in q:
        return {
            "text": (
                "**Burnout Risk Assessment**\n\n"
                "🔥 **2 agents at critical burnout risk:**\n\n"
                "**Agent-023** — Burnout score: **0.91**\n"
                "- Occupancy: 98% for 8 consecutive days\n"
                "- Handle time trend: ↑ increasing (+12% week over week)\n"
                "- ACW duration: 5 min 50 sec (avg 1 min 30 sec)\n"
                "- **Action:** Immediate schedule relief — reassign to low-volume queue within 24 hours\n\n"
                "**Agent-031** — Burnout score: **0.88**\n"
                "- Occupancy: 96% for 8 consecutive days\n"
                "- Handle time trend: ↑ increasing (+8% week over week)\n"
                "- **Action:** Schedule relief shift within 48 hours\n\n"
                "All other agents below 0.70 threshold."
            ),
            "alert": {
                "type": "BURNOUT_RISK",
                "emoji": "🔥",
                "message": "Agent-023 (score 0.91) and Agent-031 (score 0.88) at critical burnout risk.",
            },
            "metrics": [
                {"label": "Agent-023 Score", "value": "0.91", "delta": "CRITICAL"},
                {"label": "Agent-031 Score", "value": "0.88", "delta": "CRITICAL"},
                {"label": "Days High Occ.", "value": "8", "delta": ""},
                {"label": "At-Risk Agents", "value": "2", "delta": ""},
            ],
        }

    # Default
    return {
        "text": (
            "I'm not sure how to answer that. Try asking about:\n"
            "- **Supervisor:** queue health, abandonment, agent utilization\n"
            "- **Quality:** sentiment trends, coaching, compliance violations\n"
            "- **WFM:** staffing forecasts, burnout signals"
        ),
    }


def enrich_with_kb(response: dict, query: str) -> dict:
    """Add knowledge base context to an agent response."""
    try:
        kb_results = kb_retrieve(query, max_results=2)
        if kb_results:
            response["kb_docs"] = kb_results
    except Exception:
        pass  # KB enrichment is optional — don't break the response
    return response


def generate_demo_chart(chart_type: str):
    """Generate a matplotlib chart for the demo."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import io

    if chart_type == "sentiment":
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        positive = [45, 58, 62, 60, 63, 65, 61]
        negative = [25, 16, 14, 15, 13, 12, 14]
        neutral = [20, 16, 15, 16, 15, 14, 16]
        mixed = [10, 10, 9, 9, 9, 9, 9]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(days, positive, marker="o", color="#2ecc71", linewidth=2, label="Positive")
        ax.plot(days, negative, marker="o", color="#e74c3c", linewidth=2, label="Negative")
        ax.plot(days, neutral, marker="o", color="#95a5a6", linewidth=2, label="Neutral")
        ax.plot(days, mixed, marker="o", color="#f39c12", linewidth=2, label="Mixed")
        ax.axvline(x=0, color="#e74c3c", linestyle="--", alpha=0.3, label="Monday spike")
        ax.set_ylabel("Percentage (%)")
        ax.set_title("Sentiment Trends — Last 7 Days")
        ax.legend()
        ax.set_ylim(0, 80)
        fig.tight_layout()

    elif chart_type == "forecast":
        hours = list(range(6, 22))
        predicted = [12, 18, 35, 55, 78, 92, 88, 82, 65, 58, 52, 45, 38, 30, 22, 15]
        lower = [max(0, p - int(p * 0.15)) for p in predicted]
        upper = [p + int(p * 0.15) for p in predicted]

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(hours, predicted, color="#3498db", linewidth=2, marker="o", label="Predicted Volume")
        ax.fill_between(hours, lower, upper, alpha=0.2, color="#3498db", label="Confidence Band (±15%)")
        ax.axhline(y=60, color="#e74c3c", linestyle="--", alpha=0.5, label="Current Staffing Capacity")
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Contact Volume")
        ax.set_title("Staffing Forecast — Next Monday")
        ax.legend()
        ax.set_xticks(hours)
        ax.set_xticklabels([f"{h}:00" for h in hours], rotation=45)
        fig.tight_layout()
    else:
        return None

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def try_voice_synthesis(text: str) -> bytes | None:
    """Try Polly neural voice synthesis, return None if it fails."""
    try:
        import boto3
        polly = boto3.client("polly", region_name="us-east-1")
        response = polly.synthesize_speech(
            Text=text[:3000],
            OutputFormat="mp3",
            VoiceId="Matthew",
            Engine="neural",
        )
        return response["AudioStream"].read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Agent chat function
# ---------------------------------------------------------------------------

def agent_chat(agent_name: str, agent_color: str, agent_emoji: str):
    """Render a chat interface for an agent."""
    key = f"chat_{agent_name}"
    if key not in st.session_state:
        st.session_state[key] = []

    # Display chat history
    for msg in st.session_state[key]:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-msg">{agent_emoji} {msg["content"]}</div>', unsafe_allow_html=True)
            if "chart" in msg:
                st.image(msg["chart"], width="stretch")
            if "kb_docs" in msg:
                st.markdown("---")
                for doc in msg["kb_docs"]:
                    with st.expander(f"📎 {doc['title']} — *{doc['source']}*", expanded=False):
                        # Load full doc content
                        doc_path = Path(__file__).parent.parent / "knowledge_base" / doc["source"]
                        if doc_path.exists():
                            st.markdown(doc_path.read_text())
                        else:
                            st.markdown(doc["excerpt"])
            if "metrics" in msg:
                cols = st.columns(len(msg["metrics"]))
                for i, m in enumerate(msg["metrics"]):
                    cols[i].metric(m["label"], m["value"], m.get("delta", ""))
            if "audio" in msg:
                st.audio(msg["audio"], format="audio/mpeg")

    # Input
    query = st.chat_input(f"Ask the {agent_name} Agent...", key=f"input_{agent_name}")

    if query:
        st.session_state[key].append({"role": "user", "content": query})

        with st.spinner(f"{agent_emoji} {agent_name} Agent thinking..."):
            time.sleep(1.2)  # Simulate latency
            response = simulate_agent_response(agent_name, query)
            response = enrich_with_kb(response, query)

        msg_data = {"role": "agent", "content": response["text"]}

        # Add KB docs if present
        if "kb_docs" in response:
            msg_data["kb_docs"] = response["kb_docs"]

        # Generate chart if needed
        if "chart" in response:
            chart_buf = generate_demo_chart(response["chart"])
            if chart_buf:
                msg_data["chart"] = chart_buf

        # Add metrics if present
        if "metrics" in response:
            msg_data["metrics"] = response["metrics"]

        st.session_state[key].append(msg_data)

        # Voice synthesis if enabled
        if st.session_state.get("voice_toggle", False):
            with st.spinner("🔊 Generating voice..."):
                audio_bytes = try_voice_synthesis(response["text"])
                if audio_bytes:
                    msg_data["audio"] = audio_bytes
                else:
                    st.caption("Voice unavailable — check AWS credentials")

        # Fire alert if present
        if "alert" in response:
            alert = response["alert"]
            alert["time"] = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            st.session_state.alerts.append(alert)

            # Post to real Slack
            slack_sent = post_to_slack(alert)
            if slack_sent:
                st.toast(f"🔔 Alert sent to Slack: {alert['type']}", icon="✅")
            else:
                st.toast(f"🔔 Alert: {alert['type']} (Slack not configured)", icon="⚠️")

        st.rerun()


# ---------------------------------------------------------------------------
# Tab content
# ---------------------------------------------------------------------------

with tab_sup:
    st.markdown('<h2 class="supervisor-header">Supervisor Agent</h2>', unsafe_allow_html=True)
    st.caption("Claude Sonnet — Queue health, SLA breaches, agent utilization, abandonment analysis")
    st.markdown("---")
    agent_chat("Supervisor", "#037f0c", "🟢")

with tab_qual:
    st.markdown('<h2 class="quality-header">Quality Agent</h2>', unsafe_allow_html=True)
    st.caption("Claude Sonnet — Sentiment trends, coaching recommendations, compliance violations")
    st.markdown("---")
    agent_chat("Quality", "#eb5f07", "🟠")

with tab_wfm:
    st.markdown('<h2 class="wfm-header">WFM Agent</h2>', unsafe_allow_html=True)
    st.caption("Nova Lite — Staffing forecasts, burnout signals, schedule optimization")
    st.markdown("---")
    agent_chat("WFM", "#0972d3", "🔵")

with tab_dash:
    st.markdown('<h2 style="color:#FF9900;">📊 Agent Operations Dashboard</h2>', unsafe_allow_html=True)
    st.caption("Real-time monitoring of all three AI agents and the alert pipeline")
    st.markdown("---")

    # Agent status cards
    st.markdown("### Agent Status")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="agent-card sup" style="text-align:center;">
            <h4 style="color:#2ecc71; margin:0;">🟢 Supervisor</h4>
            <p style="color:#2ecc71; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#8fbc8f; margin:2px 0;">Claude Sonnet · 4 tools</p>
            <p style="color:#8fbc8f; margin:2px 0;">Avg response: 1.8s</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="agent-card qual" style="text-align:center;">
            <h4 style="color:#FF9900; margin:0;">🟠 Quality</h4>
            <p style="color:#FF9900; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#d4a574; margin:2px 0;">Claude Sonnet · 3 tools</p>
            <p style="color:#d4a574; margin:2px 0;">Avg response: 2.1s</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="agent-card wfm" style="text-align:center;">
            <h4 style="color:#3498db; margin:0;">🔵 WFM</h4>
            <p style="color:#3498db; font-size:1.5rem; font-weight:700; margin:8px 0;">ACTIVE</p>
            <p style="color:#7fb3d4; margin:2px 0;">Nova Lite · 2 tools</p>
            <p style="color:#7fb3d4; margin:2px 0;">Avg response: 1.2s</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Metrics row
    st.markdown("### Platform Metrics (Last 24h)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Queries", "1,247", "+12%")
    m2.metric("Avg Latency", "1.7s", "-0.3s")
    m3.metric("Alerts Fired", "23", "+5")
    m4.metric("Charts Generated", "89", "+15")
    m5.metric("Voice Requests", "34", "+8")

    st.markdown("---")

    # Query volume chart
    st.markdown("### Query Volume by Agent (Last 7 Days)")
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    dates = pd.date_range("2026-04-07", periods=7, freq="D")
    chart_data = pd.DataFrame({
        "Supervisor": np.random.randint(50, 120, 7),
        "Quality": np.random.randint(30, 80, 7),
        "WFM": np.random.randint(20, 60, 7),
    }, index=dates)
    st.area_chart(chart_data, color=["#2ecc71", "#FF9900", "#3498db"])

    st.markdown("---")

    # Alert history
    st.markdown("### Recent Alerts")
    alert_history = pd.DataFrame({
        "Time": ["14:02 UTC", "13:45 UTC", "12:30 UTC", "11:15 UTC", "10:02 UTC"],
        "Type": ["🚨 SLA_BREACH", "🔥 BURNOUT_RISK", "🛑 COMPLIANCE", "🚨 SLA_BREACH", "🔥 BURNOUT_RISK"],
        "Details": [
            "Billing queue at 68.5% (threshold 80%)",
            "Agent-023 score 0.91 — 8 days high occupancy",
            "PCI violation — Agent-017 read card number",
            "Support queue at 72% (threshold 80%)",
            "Agent-031 score 0.88 — rising handle times",
        ],
        "Slack": ["✅ Sent", "✅ Sent", "✅ Sent", "✅ Sent", "✅ Sent"],
    })
    st.dataframe(alert_history, hide_index=True, use_container_width=True)

    st.markdown("---")

    # Infrastructure health
    st.markdown("### Infrastructure Health")
    i1, i2, i3, i4 = st.columns(4)
    i1.metric("AgentCore Gateway", "Healthy ✅")
    i2.metric("Athena Workgroup", "Healthy ✅")
    i3.metric("EventBridge", "Healthy ✅")
    i4.metric("S3 Data Lake", "10.2 GB")


with tab_kb:
    st.markdown('<h2 style="color:#9b59b6;">📚 Knowledge Base — SharePoint Integration</h2>', unsafe_allow_html=True)
    st.caption("Agents pull SOPs, training docs, and compliance policies from SharePoint to enrich responses")
    st.markdown("---")

    # Connection status
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a1a3e, #2d1a4e); border: 1px solid #9b59b6;
                border-radius: 12px; padding: 20px; margin-bottom: 20px;">
        <h4 style="color:#9b59b6; margin:0 0 8px 0;">📎 SharePoint Connector</h4>
        <p style="color:#c8a2e8; margin:4px 0;">Status: <span style="color:#2ecc71; font-weight:700;">Connected</span></p>
        <p style="color:#c8a2e8; margin:4px 0;">Site: <code style="color:#FF9900;">contoso.sharepoint.com/sites/ContactCenter</code></p>
        <p style="color:#c8a2e8; margin:4px 0;">Last sync: 15 minutes ago · 247 documents indexed</p>
        <p style="color:#c8a2e8; margin:4px 0;">Libraries: SOPs, Training, Compliance, Scripts</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### How It Works")
    st.markdown("""
    When an agent needs context beyond the analytics data, it queries the SharePoint knowledge base:

    1. **Supervisor Agent** → pulls escalation procedures, break scheduling policies
    2. **Quality Agent** → pulls compliance checklists, coaching frameworks, script templates
    3. **WFM Agent** → pulls scheduling guidelines, overtime policies, flex pool rules
    """)

    st.markdown("---")
    st.markdown("### Indexed Documents")

    docs = pd.DataFrame({
        "Document": [
            "📄 SLA Escalation Procedure v3.2",
            "📄 PCI-DSS Compliance Checklist",
            "📄 Agent Coaching Framework",
            "📄 Break Scheduling Policy",
            "📄 Flex Pool Allocation Guide",
            "📄 De-escalation Training Module",
            "📄 Overtime Authorization Policy",
            "📄 Quality Scorecard Template",
        ],
        "Library": ["SOPs", "Compliance", "Training", "SOPs", "SOPs", "Training", "SOPs", "Training"],
        "Used By": ["Supervisor", "Quality", "Quality", "Supervisor", "WFM", "Quality", "WFM", "Quality"],
        "Last Updated": ["Apr 10", "Apr 8", "Apr 5", "Mar 28", "Apr 1", "Apr 3", "Mar 25", "Apr 7"],
        "Indexed": ["✅", "✅", "✅", "✅", "✅", "✅", "✅", "✅"],
    })
    st.dataframe(docs, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### Example: Agent Enriched Response")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #162d1f, #1a3328); border-radius: 12px;
                padding: 16px; border-left: 4px solid #2ecc71; margin: 12px 0;">
        <p style="color:#2ecc71; font-weight:700; margin:0 0 8px 0;">🟢 Supervisor Agent</p>
        <p style="color:#e8e8e8; margin:4px 0;">
            <strong>Query:</strong> "Why did abandonment spike at 2pm?"
        </p>
        <p style="color:#e8e8e8; margin:8px 0;">
            <strong>Analytics:</strong> 2 agents went to break simultaneously. Occupancy hit 96%.
        </p>
        <p style="color:#9b59b6; margin:8px 0; font-style:italic;">
            📎 <strong>From SharePoint:</strong> Per "Break Scheduling Policy v3.2" (SOPs library),
            no more than 1 agent per queue should be on break during peak hours (10am-2pm).
            This policy was violated. Recommend: enable automated break staggering in the
            workforce management system.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Architecture: SharePoint → Bedrock Knowledge Base → Agents")
    st.markdown("""
    ```
    SharePoint Online
         │
         ▼ (sync every 15 min)
    Amazon S3 (knowledge-base/)
         │
         ▼
    Bedrock Knowledge Base
    (vector embeddings)
         │
         ▼
    AgentCore Gateway
    ├── Supervisor Agent → retrieves escalation SOPs
    ├── Quality Agent    → retrieves compliance docs
    └── WFM Agent        → retrieves scheduling policies
    ```
    """)


with tab_arch:
    st.markdown("### 🏗️ System Architecture")
    st.image("diagrams/architecture.png", width="stretch")
    st.markdown("---")

    st.markdown("### Agent Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="agent-card sup">
            <h4 style="color:#2ecc71; margin:0;">🟢 Supervisor Agent</h4>
            <p style="color:#8fbc8f; margin:4px 0;"><strong>Model:</strong> Claude Sonnet</p>
            <p style="color:#8fbc8f; margin:2px 0;">Queue Health · SLA Alerts</p>
            <p style="color:#8fbc8f; margin:2px 0;">Agent Utilization · Abandonment RCA</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="agent-card qual">
            <h4 style="color:#FF9900; margin:0;">🟠 Quality Agent</h4>
            <p style="color:#d4a574; margin:4px 0;"><strong>Model:</strong> Claude Sonnet</p>
            <p style="color:#d4a574; margin:2px 0;">Sentiment Trends · Coaching</p>
            <p style="color:#d4a574; margin:2px 0;">Compliance Violations</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agent-card wfm">
            <h4 style="color:#3498db; margin:0;">🔵 WFM Agent</h4>
            <p style="color:#7fb3d4; margin:4px 0;"><strong>Model:</strong> Nova Lite (40x cheaper)</p>
            <p style="color:#7fb3d4; margin:2px 0;">Staffing Forecasts · Charts</p>
            <p style="color:#7fb3d4; margin:2px 0;">Burnout Detection · Alerts</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Tech Stack")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Agent Runtime", "AgentCore")
    c2.metric("Data Query", "Athena")
    c3.metric("Alerts", "EventBridge")
    c4.metric("Monthly Cost", "~$28")
