"""AI Banking Support & Advisory Agent — Streamlit capstone.

Track A (LangChain) · Scenario 2 (Non-Transactional). Each of the 9 phases is a
page selectable from the left sidebar.
"""
import streamlit as st

from core.config import APP_TITLE
from phases import phase1, phase2, phase3, phase4, phase5, phase6, phase7, phase8, phase9

st.set_page_config(page_title=APP_TITLE, page_icon="🏦", layout="wide")

# Slightly larger body text across all tabs/pages.
st.markdown(
    """
    <style>
    .stMarkdown, .stMarkdown p, .stMarkdown li,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {
        font-size: 1.08rem;
        line-height: 1.6;
    }
    button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PHASES = {
    "Phase 1 · Problem & Success": phase1.render,
    "Phase 2 · Basic Agent": phase2.render,
    "Phase 3 · Smarter (LLM)": phase3.render,
    "Phase 4 · Knowledge & Retrieval": phase4.render,
    "Phase 5 · Tool Usage": phase5.render,
    "Phase 6 · Planning & Memory": phase6.render,
    "Phase 7 · Adaptive Behaviour": phase7.render,
    "Phase 8 · Deployment Readiness": phase8.render,
    "Phase 9 · Evaluation & Review": phase9.render,
}

with st.sidebar:
    st.title("🏦 " + APP_TITLE)
    st.divider()
    selection = st.radio("Select a phase", list(PHASES.keys()), index=0)

st.markdown(f"### {APP_TITLE}")
st.divider()

PHASES[selection]()
