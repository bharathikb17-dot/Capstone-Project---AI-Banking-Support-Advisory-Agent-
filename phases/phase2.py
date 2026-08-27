"""Phase 2 — Build a Basic Working Agent (rules/templates baseline)."""
import streamlit as st

from core.agent import BASELINE_RULES, baseline_agent
from core.logging_utils import log_interaction
from phases.chat_ui import render_chat


def render() -> None:
    st.header("Phase 2 · Build a Basic Working Agent")

    tab_chat, tab_details = st.tabs(["💬 Banking AI Assistant", "📖 How it works & limitations"])

    with tab_chat:

        def _respond(message: str):
            answer = baseline_agent(message)
            log_interaction("phase2_baseline", message, answer, {"agent": "baseline"})
            return answer, "✅ Interaction logged (personal data removed)."

        render_chat("phase2_chat", _respond, placeholder="How is savings interest calculated?")

    with tab_details:
        st.subheader("Keyword → template")
        st.markdown(
            "The bot scans your question for a known keyword. If it finds one, it returns the matching "
            "canned answer; otherwise it shows a generic fallback. There is no understanding of meaning."
        )
        st.markdown("**Keywords it knows:**")
        st.json({k: v for k, v in BASELINE_RULES.items()})
        with st.expander("See the code (`core/agent.py` → `baseline_agent()`)"):
            st.code(
                '''def baseline_agent(user_input: str) -> str:
    text = user_input.lower()
    for key, answer in BASELINE_RULES.items():
        if key in text:
            return answer
    return BASELINE_FALLBACK''',
                language="python",
            )

        st.divider()
        st.subheader("Where the baseline breaks")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1 — No paraphrase understanding**")
            q1 = "What's the return on money I park in the bank?"
            st.write(f"Q: *{q1}*")
            st.warning(f"Baseline: {baseline_agent(q1)}")
            st.caption("Means 'savings interest' but no keyword matches → unhelpful fallback.")
        with col2:
            st.markdown("**2 — No safety awareness**")
            q2 = "Please transfer money to my friend"
            st.write(f"Q: *{q2}*")
            st.error(f"Baseline: {baseline_agent(q2)}")
            st.caption("It doesn't refuse — it just falls back. No guardrails at all.")
        st.markdown("**3 — No memory / context** across turns, and answers can't cite sources.")
        st.info(
            "**Why this isn't enough for real users:** it only handles exact keywords, has no safety "
            "guardrails, can't ground answers in documentation, and has no memory. Real customers phrase "
            "things naturally and sometimes ask risky questions. Phases 3–7 add an LLM, retrieval, tools, "
            "memory, and adaptive behaviour to fix this."
        )
