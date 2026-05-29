"""Landing page — serves the static HTML landing page."""
import base64
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Connect Analytics Platform", page_icon="🎧", layout="wide", initial_sidebar_state="collapsed")

# Hide sidebar on landing
st.markdown("""<style>
[data-testid="stSidebar"] { display: none; }
section[data-testid="stSidebarCollapsedControl"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }
iframe { border: none; }
</style>""", unsafe_allow_html=True)


def _badge_img(filename: str) -> str:
    """Return an <img> tag with a base64-embedded PNG, or '' if the file is missing."""
    path = Path(__file__).parent.parent / "assets" / "badges" / filename
    if not path.exists():
        return ""
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f'<img src="data:image/png;base64,{b64}" alt="AWS Certification" />'


_BADGES_HTML = _badge_img("cert1.png") + _badge_img("cert2.png")

# Read and serve the landing HTML
html_path = Path(__file__).parent.parent / "landing.html"
html = html_path.read_text()

# Replace demo links to use Streamlit navigation
html = html.replace('href="/demo"', 'href="/demo" target="_parent"')
html = html.replace('href="/demo" target="_parent" class="btn-primary">Open Demo', 'href="/demo" target="_parent" class="btn-primary">Open Demo')

# Inject certification badges under each team member
html = html.replace("{{BADGES}}", _BADGES_HTML)

st.html(html)
