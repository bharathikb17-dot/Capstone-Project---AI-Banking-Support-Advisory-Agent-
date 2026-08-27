"""Phase 6 — Planning, Memory & Context (multi-step + memory)."""
import streamlit as st

from core.agent import smart_agent
from core.memory import ConversationMemory
from core.tools import route, run_with_tools


def _plan(question: str):
    """Very small task-decomposition planner for demonstration."""
    steps = ["Apply safety guardrail to the request"]
    decision = route(question)
    if decision.blocked:
        steps.append("Detected transactional/approval intent → refuse & stop")
        return steps, decision
    steps.append(f"Select tool → `{decision.tool}` ({decision.reason})")
    steps.append("Retrieve/compute result")
    steps.append("Compose grounded answer + cite sources")
    steps.append("Apply output guardrail before replying")
    return steps, decision


def render() -> None:
    st.header("Phase 6 · Planning, Memory & Context")

    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory(short_term_window=6)
    mem: ConversationMemory = st.session_state.memory

    tab_chat, tab_plan, tab_mem = st.tabs(
        ["💬 Banking AI Assistant", "🧭 Planning", "🧠 Memory internals"]
    )

    with tab_chat:
        st.caption("Ask a few questions in a row — the agent remembers context.")
        for t in mem.turns:
            with st.chat_message("user" if t.role == "user" else "assistant"):
                st.write(t.content)
        turn = st.chat_input("Ask a banking question…", key="p6_chat_input")
        if turn:
            mem.add("user", turn)
            res = smart_agent(turn, history=mem.full_context())
            mem.add("assistant", res.response)
            st.rerun()

    with tab_plan:
        st.subheader("Multi-step planning")
        st.caption("The agent lists its steps before acting.")
        pq = st.text_input("Question to plan", "Estimate a loan of 10000 at 8% over 24 months")
        if st.button("Show plan & execute"):
            steps, decision = _plan(pq)
            for i, s in enumerate(steps, 1):
                st.markdown(f"{i}. {s}")
            result = run_with_tools(pq)
            st.success(f"Result: {result['output']}" if not result["blocked"] else f"Refused: {result['reason']}")

    with tab_mem:
        st.subheader("What's stored")
        st.markdown(f"**Short-term window:** last {mem.short_term_window} turns (currently {len(mem.turns)})")
        st.markdown("**Long-term summary (redacted):**")
        st.info(mem.long_term_summary or "*(empty — fills as the window overflows)*")

        st.subheader("Retention & reset rules")
        st.markdown(
            "- Only the **last N turns** are kept word-for-word; older turns become a **redacted** summary.\n"
            "- Long-term memory stores **no raw personal data**."
        )

