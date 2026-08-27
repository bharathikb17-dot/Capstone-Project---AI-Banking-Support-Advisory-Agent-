"""Phase 5 — Enable Tool Usage (function calling, routing, safeguards)."""
import streamlit as st

from core.tools import TOOLS, route, run_with_tools
from phases.chat_ui import render_chat


def render() -> None:
    st.header("Phase 5 · Enable Tool Usage")

    tab_chat, tab_tools, tab_fail, tab_safe = st.tabs(
        ["💬 Banking AI Assistant", "🧰 Tools", "🧪 Failed call", "🛡️ Safeguards"]
    )

    with tab_chat:

        def _respond(message: str):
            decision = route(message)
            result = run_with_tools(message)
            if result["blocked"]:
                return f"⛔ Blocked: {result['reason']}", f"Router: `{decision.tool}` · {decision.reason}"
            return str(result["output"]), f"Used `{result['tool']}` · trace: {result['trace']}"

        render_chat("phase5_chat", _respond, placeholder="Estimate a loan of 10000 at 8% over 24 months")

    with tab_tools:
        st.subheader("Available tools (all read-only / non-transactional)")
        for tool in TOOLS.values():
            st.markdown(f"- **`{tool.name}`** — {tool.description}")

    with tab_fail:
        st.subheader("What a bad tool call looks like")
        st.markdown("Asking for a loan calc with no numbers safely falls back to a knowledge lookup:")
        from core.tools import loan_calculator

        st.markdown("Calling the calculator with invalid values `amount=-5, months=0`:")
        st.warning(loan_calculator.invoke({"amount": -5, "annual_rate_pct": 8, "months": 0}))

    with tab_safe:
        st.subheader("Safeguards against misuse and loops")
        st.markdown(
            "- **Intent blocklist** — transfer / pay / withdraw / approve → no tool may act.\n"
            "- **Loop prevention** — `MAX_TOOL_CALLS = 3` caps repeated calls.\n"
            "- **Argument validation** — tools reject invalid inputs gracefully.\n"
            "- **Read-only tools only** — nothing can change account state."
        )
        st.markdown("**Blocked misuse example:**")
        blocked = run_with_tools("transfer $500 and also approve my overdraft")
        st.error(f"⛔ {blocked['reason']}")

