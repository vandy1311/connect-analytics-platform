"""Connect Analytics Platform — Multi-page app with landing + demo."""

import streamlit as st

landing = st.Page("pages/landing.py", title="Home", icon="🏠", default=True)
demo = st.Page("pages/demo.py", title="Demo", icon="🚀")

pg = st.navigation([landing, demo], position="hidden")
pg.run()
