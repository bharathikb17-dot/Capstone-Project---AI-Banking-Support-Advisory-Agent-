"""Phase 7 — Adaptive Behaviour (feedback → behaviour change)."""
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.feedback import (
    BehaviorProfile,
    clear_feedback,
    derive_profile,
    load_feedback,
    profile_instruction,
    store_feedback,
)
from core.llm import get_chat_model
from core.safety import SAFETY_SYSTEM_RULES
from phases.chat_ui import render_chat


def _answer(question: str, profile: BehaviorProfile) -> str:
    instruction = profile_instruction(profile)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SAFETY_SYSTEM_RULES + "\n\nStyle instruction: {style}"),
            ("human", "Customer: {q}"),
        ]
    )
    chain = prompt | get_chat_model() | StrOutputParser()
    return chain.invoke({"style": instruction, "q": question})


def render() -> None:
    st.header("Phase 7 · Adaptive Behaviour")

    tab_chat, tab_profile, tab_compare = st.tabs(
        ["💬 Banking AI Assistant", "🎚️ Current profile", "🔀 Before vs after"]
    )

    with tab_chat:

        def _respond(message: str):
            return _answer(message, derive_profile())

        render_chat("phase7_chat", _respond, placeholder="How does a standing order work?")

        history = st.session_state.get("phase7_chat", [])
        if len(history) >= 2 and history[-1]["role"] == "assistant":
            last_q, last_a = history[-2]["content"], history[-1]["content"]
            st.caption("Rate the latest answer so the agent can adapt:")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("👍 Good"):
                store_feedback(last_q, last_a, "up", "good")
                st.toast("Thanks — stored 👍")
            if c2.button("👎 Too long"):
                store_feedback(last_q, last_a, "down", "too_long")
                st.toast("Stored: too_long")
            if c3.button("👎 Too short"):
                store_feedback(last_q, last_a, "down", "too_short")
                st.toast("Stored: too_short")
            if c4.button("👎 Unclear"):
                store_feedback(last_q, last_a, "down", "unclear")
                st.toast("Stored: unclear")

    with tab_profile:
        st.subheader("What the agent has learned")
        profile = derive_profile()
        st.write(f"**Verbosity:** `{profile.verbosity}`")
        st.write("**Adjustment notes:** " + ("; ".join(profile.notes) if profile.notes else "*(none yet)*"))
        st.caption(f"Style instruction applied to every answer: {profile_instruction(profile)}")
        st.write(f"Feedback records stored: **{len(load_feedback())}** (all redacted)")
        if st.button("Clear stored feedback"):
            clear_feedback()
            st.rerun()

    with tab_compare:
        st.subheader("See the adaptation in action")
        st.caption("Compares a neutral style against the style learned from your feedback.")
        bq = st.text_input("Comparison question", "Explain how credit card interest works")
        if st.button("Compare behaviour"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Before (neutral)**")
                st.info(_answer(bq, BehaviorProfile(verbosity="normal")))
            with col2:
                st.markdown("**After (adapted from feedback)**")
                st.success(_answer(bq, derive_profile()))

