"""Reusable persistent chatbot UI for the phase pages."""
from __future__ import annotations

from typing import Callable, List, Tuple, Union

import streamlit as st

# A responder returns either the answer text, or (answer, caption).
Responder = Callable[[str], Union[str, Tuple[str, str]]]


def render_chat(state_key: str, responder: Responder, *, placeholder: str = "Type your message…") -> None:
    """Render a persistent chat: history is kept in session state under `state_key`."""
    history: List[dict] = st.session_state.setdefault(state_key, [])

    if history and st.button("🗑️ Clear chat", key=f"{state_key}_clear"):
        st.session_state[state_key] = []
        st.rerun()

    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("caption"):
                st.caption(msg["caption"])

    prompt = st.chat_input(placeholder, key=f"{state_key}_input")
    if prompt:
        history.append({"role": "user", "content": prompt})
        result = responder(prompt)
        content, caption = result if isinstance(result, tuple) else (result, None)
        history.append({"role": "assistant", "content": content, "caption": caption})
        st.rerun()
