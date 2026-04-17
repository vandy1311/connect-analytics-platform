"""Connect Analytics Platform — Full Demo."""

import time
import random
import streamlit as st
import plotly.graph_objects as go

st.markdown("""<style>
.block-container { padding-top: 1.5rem; }
div[data-testid="stMetric"] {
    background: #141414; border: 1px solid #222;
    border-radius: 10px; padding: 12px 16px;
}
</style>""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎯 Connect Analytics")
    st.caption("AI-Powered Contact Center Platform")
    st.divider()
    page = st.radio(
        "Navigate",
        ["Overview", "Agents", "Architecture", "Live Demo", "Dashboard", "Alerts"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Bedrock AgentCore · CDK · Lambda · Athena")
    st.divider()
    if st.button("← Landing Page", use_container_width=True):
        st.switch_page("pages/landing.py")

# ── Data ─────────────────────────────────────────────────────────────────
QUEUE_DATA = [
    {"Queue": "General Support", "In Queue": 12, "Longest Wait": "2m 34s", "SLA %": 87.3, "AHT": "4m 12s"},
    {"Queue": "Billing", "In Queue": 5, "Longest Wait": "1m 08s", "SLA %": 92.1, "AHT": "3m 45s"},
    {"Queue": "Technical", "In Queue": 18, "Longest Wait": "4m 51s", "SLA %": 71.2, "AHT": "6m 30s"},
    {"Queue": "Sales", "In Queue": 3, "Longest Wait": "0m 42s", "SLA %": 95.4, "AHT": "5m 18s"},
]
AGENT_UTIL = [
    {"Agent": "A-1042", "Occupancy": "94%", "Status": "🔴 ON_CALL", "AHT": "5m 12s", "Contacts": 47},
    {"Agent": "A-1087", "Occupancy": "82%", "Status": "🟡 AVAILABLE", "AHT": "4m 03s", "Contacts": 41},
    {"Agent": "A-1103", "Occupancy": "67%", "Status": "🟢 AVAILABLE", "AHT": "3m 48s", "Contacts": 35},
    {"Agent": "A-1056", "Occupancy": "91%", "Status": "🔴 ACW", "AHT": "6m 22s", "Contacts": 38},
    {"Agent": "A-1078", "Occupancy": "73%", "Status": "🟢 AVAILABLE", "AHT": "4m 15s", "Contacts": 32},
]
FORECAST = [
    {"Day": "Mon", "Predicted": 342, "CI": 28, "Agents Needed": 18},
    {"Day": "Tue", "Predicted": 318, "CI": 25, "Agents Needed": 17},
    {"Day": "Wed", "Predicted": 356, "CI": 31, "Agents Needed": 19},
    {"Day": "Thu", "Predicted": 371, "CI": 33, "Agents Needed": 20},
    {"Day": "Fri", "Predicted": 289, "CI": 22, "Agents Needed": 15},
    {"Day": "Sat", "Predicted": 198, "CI": 18, "Agents Needed": 11},
    {"Day": "Sun", "Predicted": 156, "CI": 15, "Agents Needed": 9},
]

RESPONSES = {
    "supervisor": {
        "tools": ["get_queue_health", "get_abandonment_analysis", "get_agent_utilization", "trigger_sla_alert"],
        "keywords": {
            "queue": (
                "🔧 `get_queue_health(time_range='last_1h')`\n\n"
                "| Queue | In Queue | Wait | SLA | AHT |\n|---|---|---|---|---|\n"
                "| General Support | 12 | 2m 34s | 87.3% | 4m 12s |\n"
                "| Billing | 5 | 1m 08s | 92.1% | 3m 45s |\n"
                "| Technical | 18 | 4m 51s | **71.2%** ⚠️ | 6m 30s |\n"
                "| Sales | 3 | 0m 42s | 95.4% | 5m 18s |\n\n"
                "⚠️ Technical queue below 80% — triggered `trigger_sla_alert`."
            ),
            "abandon": (
                "🔧 `get_abandonment_analysis(time_range='last_24h')`\n\n"
                "- **Rate:** 4.2% (127 / 3,024)\n- **Peak:** 2–3 PM (8.1%)\n"
                "- **Avg wait before abandon:** 3m 22s\n\n"
                "Staffing gap in Technical queue during 2 PM shift change."
            ),
            "utilization": (
                "🔧 `get_agent_utilization(time_range='last_8h')`\n\n"
                "| Agent | Occ. | Status | AHT | Contacts |\n|---|---|---|---|---|\n"
                "| A-1042 | 94% 🔴 | ON_CALL | 5m 12s | 47 |\n"
                "| A-1087 | 82% 🟡 | AVAILABLE | 4m 03s | 41 |\n"
                "| A-1103 | 67% 🟢 | AVAILABLE | 3m 48s | 35 |\n"
                "| A-1056 | 91% 🔴 | ACW | 6m 22s | 38 |\n\n"
                "Two agents above 90% — flagging for burnout review."
            ),
        },
    },
    "quality": {
        "tools": ["get_sentiment_trends", "get_coaching_recommendations", "get_compliance_violations"],
        "keywords": {
            "sentiment": (
                "🔧 `get_sentiment_trends(time_range='last_7d')`\n\n"
                "| Sentiment | % | Trend |\n|---|---|---|\n"
                "| Positive | 62% | ↑ +3% |\n| Neutral | 24% | — |\n"
                "| Negative | 11% | ↓ -2% |\n| Mixed | 3% | — |\n\n"
                "Improving overall. Billing queue biggest positive shift."
            ),
            "coaching": (
                "🔧 `get_coaching_recommendations()`\n\n"
                "**A-1056** — 28% negative (avg 11%)\n"
                "> *\"There's nothing I can do.\"*\n→ Empathy training.\n\n"
                "**A-1091** — 22% negative\n"
                "> *\"Call back during business hours.\"*\n→ Warm transfer training."
            ),
            "compliance": (
                "🔧 `get_compliance_violations()`\n\n"
                "🔴 **HIGH** PCI_VIOLATION — C-8847, A-1056\n"
                "Card number read aloud, no IVR redirect.\n\n"
                "🟡 **MED** MISSING_DISCLOSURE — C-9012\nRecording disclosure late.\n\n"
                "🟢 **LOW** MISSING_DISCLOSURE — C-9234\nNon-verbatim format."
            ),
        },
    },
    "wfm": {
        "tools": ["get_staffing_forecast", "get_burnout_signals"],
        "keywords": {
            "forecast": (
                "🔧 `get_staffing_forecast(days=7)`\n\n"
                "| Day | Vol. | ±CI | Agents |\n|---|---|---|---|\n"
                "| Mon | 342 | ±28 | 18 |\n| Tue | 318 | ±25 | 17 |\n"
                "| Wed | 356 | ±31 | 19 |\n| Thu | 371 | ±33 | 20 |\n"
                "| Fri | 289 | ±22 | 15 |\n\n"
                "Thursday peak — need 3 more agents than scheduled."
            ),
            "burnout": (
                "🔧 `get_burnout_signals(threshold=0.85)`\n\n"
                "🔴 **CRITICAL** A-1042 — Score **0.93**\n"
                "94% occ. × 5 days, AHT +18%.\n→ Mandatory break rotation.\n\n"
                "🟡 **WARNING** A-1056 — Score **0.87**\n"
                "91% occ., 3 overtime shifts.\n→ Schedule review.\n\n"
                "Alert sent to `#connect-wfm-alerts`."
            ),
        },
    },
}

PROMPT_LABELS = {
    "queue": "🏥 Queue health", "abandon": "📞 Abandonment", "utilization": "👤 Utilization",
    "sentiment": "😊 Sentiment", "coaching": "🎓 Coaching", "compliance": "⚖️ Compliance",
    "forecast": "📈 Forecast", "burnout": "🔥 Burnout",
}


def match_response(agent_key, msg):
    kw = RESPONSES[agent_key]["keywords"]
    for k, v in kw.items():
        if k in msg.lower():
            return v
    return next(iter(kw.values()))


_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#ccc"),
    margin=dict(t=30, b=40, l=50, r=20),
)

# ═══════════════════════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════════════════════

if page == "Overview":
    st.header("🎯 Connect Analytics Platform")
    st.markdown(
        "Three specialized **Bedrock AgentCore** agents working together to "
        "monitor queue health, ensure quality compliance, and optimize "
        "workforce management — all in real time."
    )
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Service Level", "87.3%", "▲ 2.1%")
    k2.metric("Abandon Rate", "4.2%", "▼ 0.8%", delta_color="inverse")
    k3.metric("Agents Online", "24", "▲ 3")
    k4.metric("Contacts Today", "1,847", "▲ 312")
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🎯 Monitor")
        st.markdown("Supervisor Agent watches queue health, SLA compliance, and agent utilization.")
    with c2:
        st.subheader("✅ Analyze")
        st.markdown("Quality Agent digs into sentiment, flags compliance violations, generates coaching.")
    with c3:
        st.subheader("📊 Optimize")
        st.markdown("WFM Agent forecasts staffing needs and detects burnout signals.")

elif page == "Agents":
    st.header("🤖 Meet the Agents")
    st.divider()
    st.subheader("🎯 Supervisor Agent")
    st.caption("Claude Sonnet 4 · 4 tools")
    st.markdown("Monitors queue health, SLA breaches, agent utilization, abandonment patterns.")
    st.code("get_queue_health · get_abandonment_analysis · get_agent_utilization · trigger_sla_alert")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("✅ Quality Agent")
        st.caption("Claude Sonnet 4 · 3 tools")
        st.markdown("Sentiment trends, coaching recommendations, compliance violations.")
        st.code("get_sentiment_trends · get_coaching_recommendations · get_compliance_violations")
    with c2:
        st.subheader("📊 WFM Agent")
        st.caption("Nova Lite v2 · 2 tools")
        st.markdown("Staffing forecasts with confidence intervals, burnout detection.")
        st.code("get_staffing_forecast · get_burnout_signals")
    st.divider()
    st.info("All agents share a single AgentCore Gateway (Lambda type). Out-of-scope questions redirect to the right agent.")

elif page == "Architecture":
    st.header("🏗️ Architecture")
    st.divider()
    st.markdown("""
```mermaid
graph TD
    A["☁️ Amazon Connect"] --> B["📦 S3 Data Lake"]
    B --> C["📚 Glue Catalog"]
    B --> D["🔍 Athena"]
    B --> E["🧠 Knowledge Base"]
    C --> F["🌐 AgentCore Gateway"]
    D --> F
    E --> F
    F --> G["🎯 Supervisor · Claude 4 · 4 tools"]
    F --> H["✅ Quality · Claude 4 · 3 tools"]
    F --> I["📊 WFM · Nova Lite · 2 tools"]
    G --> J["⚡ Tool Lambda · 9 tools"]
    H --> J
    I --> J
    J --> K["📡 EventBridge"]
    K --> L["📬 SNS · 5 topics"]
    L --> M["💬 Slack · 3 channels"]
```
    """)
    st.divider()
    st.subheader("CDK Stacks")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.success("🔐 Auth")
    s2.success("💾 Data")
    s3.success("🤖 Agent")
    s4.success("🚨 Alert")
    s5.success("📚 KB")
    with st.expander("📋 Data Flow"):
        st.markdown(
            "1. Connect → S3\n2. Glue Catalog (3 tables)\n3. Athena workgroup\n"
            "4. Knowledge Base (RAG)\n5. AgentCore Gateway → Lambda\n"
            "6. Lambda dispatches by tool_name\n7. EventBridge → SNS → Slack"
        )

elif page == "Live Demo":
    st.header("💬 Chat with an Agent")
    st.divider()
    choice = st.radio("Agent:", ["🎯 Supervisor", "✅ Quality", "📊 WFM"], horizontal=True)
    key_map = {"🎯 Supervisor": "supervisor", "✅ Quality": "quality", "📊 WFM": "wfm"}
    name_map = {"supervisor": "Supervisor Agent", "quality": "Quality Agent", "wfm": "WFM Agent"}
    model_map = {"supervisor": "Claude Sonnet 4", "quality": "Claude Sonnet 4", "wfm": "Nova Lite v2"}
    ak = key_map[choice]
    cfg = RESPONSES[ak]
    st.caption(f"{model_map[ak]} · Tools: `{'` `'.join(cfg['tools'])}`")
    cols = st.columns(len(cfg["keywords"]))
    clicked = None
    for i, kw in enumerate(cfg["keywords"]):
        if cols[i].button(PROMPT_LABELS[kw], key=f"p_{ak}_{kw}", use_container_width=True):
            clicked = PROMPT_LABELS[kw]
    st.divider()
    hk = f"h_{ak}"
    if hk not in st.session_state:
        st.session_state[hk] = []
    for m in st.session_state[hk]:
        with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🤖"):
            st.markdown(m["content"])
    user_input = clicked or st.chat_input(f"Ask {name_map[ak]}...")
    if user_input:
        st.session_state[hk].append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)
        resp = match_response(ak, user_input)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                time.sleep(0.8)
            st.markdown(resp)
        st.session_state[hk].append({"role": "assistant", "content": resp})

elif page == "Dashboard":
    st.header("📊 Real-Time Dashboard")
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Queue SLA %")
        q = [d["Queue"] for d in QUEUE_DATA]
        s = [d["SLA %"] for d in QUEUE_DATA]
        fig = go.Figure(go.Bar(
            x=q, y=s,
            marker_color=["#3fb950" if v >= 80 else "#f85149" for v in s],
            text=[f"{v}%" for v in s], textposition="outside",
        ))
        fig.add_hline(y=80, line_dash="dash", line_color="#d29922", annotation_text="Target 80%")
        fig.update_layout(**_LAYOUT, height=320, yaxis_range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Sentiment Breakdown")
        fig = go.Figure(go.Pie(
            labels=["Positive", "Neutral", "Negative", "Mixed"],
            values=[62, 24, 11, 3], hole=0.5,
            marker_colors=["#3fb950", "#58a6ff", "#f85149", "#d29922"],
        ))
        fig.update_layout(**_LAYOUT, height=320, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    left2, right2 = st.columns(2)
    with left2:
        st.subheader("Staffing Forecast")
        days = [f["Day"] for f in FORECAST]
        pred = [f["Predicted"] for f in FORECAST]
        ci = [f["CI"] for f in FORECAST]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=[p+c for p,c in zip(pred,ci)], mode="lines", line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=days, y=[p-c for p,c in zip(pred,ci)], mode="lines", line=dict(width=0), fill="tonexty", fillcolor="rgba(124,108,240,0.12)", showlegend=False))
        fig.add_trace(go.Scatter(x=days, y=pred, mode="lines+markers", line=dict(color="#7c6cf0", width=3), marker=dict(size=8), name="Predicted"))
        fig.update_layout(**_LAYOUT, height=320, yaxis_title="Contacts")
        st.plotly_chart(fig, use_container_width=True)
    with right2:
        st.subheader("Agent Occupancy")
        agents = [a["Agent"] for a in AGENT_UTIL]
        occ = [int(a["Occupancy"].rstrip("%")) for a in AGENT_UTIL]
        fig = go.Figure(go.Bar(
            x=agents, y=occ,
            marker_color=["#f85149" if v >= 90 else "#d29922" if v >= 80 else "#3fb950" for v in occ],
            text=[f"{v}%" for v in occ], textposition="outside",
        ))
        fig.add_hline(y=90, line_dash="dash", line_color="#f85149", annotation_text="Burnout Risk")
        fig.update_layout(**_LAYOUT, height=320, yaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Hourly Volume — Today")
    hours = [f"{h}:00" for h in range(8, 21)]
    random.seed(42)
    vol = [random.randint(80, 180) for _ in hours]
    vol[6], vol[7] = 210, 195
    fig = go.Figure(go.Bar(x=hours, y=vol, marker_color="#7c6cf0", opacity=0.85))
    fig.update_layout(**_LAYOUT, height=250, xaxis_title="Hour", yaxis_title="Contacts")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Alerts":
    st.header("🚨 Alert Pipeline")
    st.markdown("EventBridge → SNS (5 topics) → Slack Lambda → Slack channels")
    st.divider()
    alerts = [
        ("🔴", "SLA Breach", "#connect-sla-alerts", "Service level below threshold"),
        ("🟡", "Abandonment Spike", "#connect-sla-alerts", "Unusual abandon increase"),
        ("🔵", "Occupancy Critical", "#connect-sla-alerts", "Agent occupancy too high"),
        ("🟣", "Compliance Violation", "#connect-compliance", "PCI / disclosure issues"),
        ("🟢", "Burnout Risk", "#connect-wfm-alerts", "Burnout score exceeded"),
    ]
    for icon, name, channel, desc in alerts:
        with st.expander(f"{icon} {name}"):
            st.markdown(f"**{desc}**")
            st.markdown(f"Channel: `{channel}`")
            st.json({"source": "connect-analytics", "detail-type": name.upper().replace(" ", "_"),
                      "detail": {"queue": "Technical", "severity": "HIGH", "ts": "2026-04-17T14:32:00Z"}})
    st.divider()
    st.subheader("Recent Alerts")
    for t, badge, detail in [
        ("14:32", "🔴 SLA_BREACH", "Technical queue SLA at 71.2%"),
        ("14:15", "🟢 BURNOUT_RISK", "Agent A-1042 score 0.93"),
        ("13:48", "🟡 ABANDONMENT", "Technical queue 8.1% abandon rate"),
        ("11:22", "🟣 COMPLIANCE", "PCI violation — Contact C-8847"),
        ("09:15", "🔵 OCCUPANCY", "3 agents above 90% for 4+ hours"),
    ]:
        st.markdown(f"`{t}` **{badge}** — {detail}")

st.divider()
st.caption("Connect Analytics Platform · Bedrock AgentCore · CDK · Lambda · Athena · EventBridge · Hackathon 2026")
