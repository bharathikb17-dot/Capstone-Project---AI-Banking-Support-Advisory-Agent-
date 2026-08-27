"""Phase 3 — Make the Agent Smarter (LLM + prompt engineering)."""
import streamlit as st

from core.agent import DEFAULT_STRATEGY, smart_agent
from core.evaluation import PROMPT_EVAL_QUESTIONS, compare_prompts, prompt_metrics
from core.logging_utils import log_interaction
from phases.chat_ui import render_chat


def render() -> None:
    st.header("Phase 3 · Make the Agent Smarter")

    tab_chat, tab_table, tab_default, tab_notes = st.tabs(
        ["💬 Banking AI Assistant", "📊 Comparison table", "⭐ Default choice", "📈 What changed"]
    )

    with tab_chat:

        def _respond(message: str):
            res = smart_agent(message, strategy=DEFAULT_STRATEGY, use_retrieval=True)
            log_interaction("phase3_chat", message, res.response, {"strategy": DEFAULT_STRATEGY})
            badge = {"allow": "✅", "refuse": "⛔", "escalate": "⚠️"}[res.action]
            caption = f"{badge} `{res.action}`"
            if res.sources:
                caption += " · Sources: " + ", ".join(res.sources)
            return res.response, caption

        render_chat("phase3_chat", _respond, placeholder="How is interest on my savings calculated?")

    with tab_table:
        st.subheader("Prompt evaluation on a shared test set")
        st.caption("Required method: same test set · 3 prompt variants · Prompt → Output → what improved/worsened.")
        st.markdown("**Shared test set:**")
        for tq in PROMPT_EVAL_QUESTIONS:
            st.markdown(f"- *{tq}*")
        if st.button("Run prompt comparison"):
            st.markdown("**Aggregate metrics across the test set**")
            st.dataframe(prompt_metrics(), use_container_width=True)
            rep_q = PROMPT_EVAL_QUESTIONS[0]
            st.markdown(f"**Prompt → Output → What improved / worsened** — for *{rep_q}*")
            rows = compare_prompts(rep_q)
            st.dataframe(
                [{
                    "prompt": r["strategy"],
                    "output": (r["response"][:150] + "…") if len(r["response"]) > 150 else r["response"],
                    "cites sources": "yes" if r["cites_sources"] else "no",
                    "action": r["action"],
                } for r in rows],
                use_container_width=True,
            )
            st.info(
                "**Reading the table:** `zero_shot` answers but never cites sources; `persona` is warmer/shorter "
                "but still ungrounded; `grounded` is the only variant that cites the KB and safely declines when "
                "information is missing — which is why it's the chosen default."
            )

    with tab_default:
        st.subheader(f"Chosen default: `{DEFAULT_STRATEGY}`")
        st.success(
            "We use the **grounded** strategy by default. It's the only one that forces the model to "
            "answer strictly from retrieved bank documentation and cite sources. This directly protects "
            "two safety rules — *don't make up customer data* and stay factual — at the small cost of "
            "sometimes saying 'I don't have that information', which is exactly the safe behaviour we want."
        )

    with tab_notes:
        st.subheader("Improvements over the Phase 2 baseline")
        st.markdown(
            "- Understands paraphrased questions (meaning, not keywords).\n"
            "- Applies the safety system prompt on every call.\n"
            "- Gives grounded, cited answers instead of canned templates."
        )
        st.subheader("New risks the LLM introduces (and our fixes)")
        st.warning(
            "- **Making things up** if ungrounded → fixed by the grounded default + output check.\n"
            "- **Rambling** at high creativity → fixed by low default temperature + persona limits.\n"
            "- **Slower & costs money** vs the instant baseline → measured in Phase 8."
        )
