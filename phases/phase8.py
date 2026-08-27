"""Phase 8 — Deployment Readiness (packaging, logging/tracing, graceful failure)."""
import time

import streamlit as st

from core.agent import smart_agent
from core.logging_utils import clear_logs, log_interaction, read_logs
from phases.chat_ui import render_chat


def render() -> None:
    st.header("Phase 8 · Deployment Readiness")

    tab_chat, tab_fail, tab_logs = st.tabs(
        ["💬 Banking AI Assistant", "🧯 Graceful failure", "📜 Recent logs"]
    )

    with tab_chat:

        def _respond(message: str):
            start = time.perf_counter()
            error = None
            try:
                answer = smart_agent(message).response
            except Exception as exc:  # graceful capture
                error = str(exc)
                answer = "Sorry — something went wrong on our side. Please try again shortly."
            latency_ms = (time.perf_counter() - start) * 1000
            log_interaction("phase8_trace", message, answer, {"latency_ms": round(latency_ms, 1), "error": error})
            caption = f"⏱️ {latency_ms:.0f} ms · logged (redacted)"
            if error:
                caption += f" · handled error: {error}"
            return answer, caption

        render_chat("phase8_chat", _respond, placeholder="How is savings interest calculated?")

    with tab_fail:
        st.subheader("The app degrades safely at every layer")
        st.markdown(
            "- **No API key** → automatic offline mock mode (never crashes).\n"
            "- **LLM/tool error** → caught; user gets a friendly message; error is logged.\n"
            "- **Empty retrieval** → the agent says it doesn't have the info instead of guessing.\n"
            "- **Unsafe request** → deterministic refuse/escalate path, independent of the LLM."
        )
        if st.button("Simulate a backend failure"):
            try:
                raise ConnectionError("Simulated LLM provider timeout")
            except Exception as exc:
                msg = "Sorry — our assistant is temporarily unavailable. Please try again shortly."
                log_interaction("phase8_failure_sim", "simulate", msg, {"error": str(exc)})
                st.warning(f"Handled gracefully → user sees: '{msg}'")

    with tab_logs:
        st.subheader("Recent traces (redacted)")
        logs = read_logs(limit=15)
        if logs:
            st.dataframe(
                [{"ts": l["ts"], "phase": l["phase"], "input": l["user_input"][:50], "meta": l["meta"]} for l in logs],
                use_container_width=True,
            )
        else:
            st.caption("No logs yet — chat in the Chatbot tab to generate traces.")
        if st.button("Clear logs"):
            clear_logs()
            st.rerun()

