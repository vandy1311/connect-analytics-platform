"""Landing page."""

import streamlit as st

# Hide sidebar on landing
st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarNav"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 0 !important; max-width: 1000px; }

.landing-hero { text-align: center; padding: 6rem 1rem 3rem; }
.landing-title {
    font-size: 3.5rem; font-weight: 800;
    letter-spacing: -1px; line-height: 1.15; margin-bottom: 1rem;
}
.landing-gradient {
    background: linear-gradient(135deg, #7c6cf0, #58a6ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.landing-sub {
    font-size: 1.25rem; color: #999;
    max-width: 650px; margin: 0 auto 2.5rem; line-height: 1.7;
}
.feature-card {
    background: #141414; border: 1px solid #222;
    border-radius: 14px; padding: 2rem 1.5rem;
    text-align: center; height: 100%;
}
.feature-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
.feature-title { font-size: 1.15rem; font-weight: 700; margin-bottom: 0.5rem; }
.feature-desc { color: #999; font-size: 0.9rem; line-height: 1.6; }
.tech-pill {
    display: inline-block; background: #141414; border: 1px solid #222;
    padding: 6px 16px; border-radius: 20px;
    font-size: 0.82rem; color: #bbb; margin: 4px;
}
.stat-row {
    display: flex; justify-content: center; gap: 3rem;
    flex-wrap: wrap; margin: 2rem 0;
}
.stat-item { text-align: center; }
.stat-num { font-size: 2.2rem; font-weight: 800; color: #7c6cf0; }
.stat-label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
</style>""", unsafe_allow_html=True)

st.markdown("""
<div class="landing-hero">
    <div class="landing-title">
        AI-Powered<br><span class="landing-gradient">Contact Center</span> Analytics
    </div>
    <div class="landing-sub">
        Three specialized Bedrock AgentCore agents that monitor queue health,
        ensure quality compliance, and optimize workforce management — in real time.
    </div>
</div>
""", unsafe_allow_html=True)

_, center, _ = st.columns([1, 1, 1])
with center:
    if st.button("🚀  Launch Demo", use_container_width=True, type="primary"):
        st.switch_page("pages/demo.py")

st.write("")

st.markdown("""
<div class="stat-row">
    <div class="stat-item"><div class="stat-num">3</div><div class="stat-label">AI Agents</div></div>
    <div class="stat-item"><div class="stat-num">9</div><div class="stat-label">Tools</div></div>
    <div class="stat-item"><div class="stat-num">5</div><div class="stat-label">Alert Types</div></div>
    <div class="stat-item"><div class="stat-num">5</div><div class="stat-label">CDK Stacks</div></div>
</div>
""", unsafe_allow_html=True)

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""<div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">Supervisor Agent</div>
        <div class="feature-desc">Queue health monitoring, SLA breach detection,
        agent utilization tracking, abandonment analysis.<br><br><b>Claude Sonnet 4 · 4 tools</b></div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown("""<div class="feature-card">
        <div class="feature-icon">✅</div>
        <div class="feature-title">Quality Agent</div>
        <div class="feature-desc">Sentiment trend analysis, coaching recommendations,
        compliance violation detection from Contact Lens.<br><br><b>Claude Sonnet 4 · 3 tools</b></div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown("""<div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">WFM Agent</div>
        <div class="feature-desc">Staffing forecasts with confidence intervals,
        burnout signal detection for proactive planning.<br><br><b>Nova Lite v2 · 2 tools</b></div>
    </div>""", unsafe_allow_html=True)

st.write("")
st.divider()
st.markdown("""<div style="text-align:center; padding: 1rem 0;">
    <div style="font-size:1.3rem; font-weight:700; margin-bottom:0.5rem;">Built on AWS</div>
    <div>
        <span class="tech-pill">Bedrock AgentCore</span>
        <span class="tech-pill">AWS CDK</span>
        <span class="tech-pill">Lambda</span>
        <span class="tech-pill">Athena</span>
        <span class="tech-pill">S3</span>
        <span class="tech-pill">Glue</span>
        <span class="tech-pill">EventBridge</span>
        <span class="tech-pill">SNS</span>
        <span class="tech-pill">Bedrock KB</span>
    </div>
</div>""", unsafe_allow_html=True)

st.write("")
st.divider()
st.caption("Connect Analytics Platform · AWS Hackathon 2026")
