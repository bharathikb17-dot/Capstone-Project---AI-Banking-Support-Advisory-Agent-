"""Phase 4 — Add Knowledge & Retrieval (embeddings + semantic search + RAG)."""
import streamlit as st

from core.agent import smart_agent
from core.rag import list_chunks, retrieve
from phases.chat_ui import render_chat


def render() -> None:
    st.header("Phase 4 · Add Knowledge & Retrieval")

    chunks = list_chunks()
    sources = sorted({c.source for c in chunks})

    tab_chat, tab_search, tab_compare, tab_missing = st.tabs(
        ["💬 Banking AI Assistant", "🔎 Search the KB", "⚖️ With vs without", "🕳️ Missing info"]
    )

    with tab_chat:

        def _respond(message: str):
            res = smart_agent(message, strategy="grounded", use_retrieval=True)
            caption = "Sources: " + ", ".join(res.sources) if res.sources else "No relevant sources found."
            return res.response, caption

        render_chat("phase4_chat", _respond, placeholder="How do I get a new card if mine is lost?")

    with tab_search:
        st.markdown(
            f"The knowledge base holds **{len(chunks)} chunks** from **{len(sources)} documents**: "
            + ", ".join(f"`{s}`" for s in sources)
        )
        q = st.text_input("Search the knowledge base", "how do I get a new card if mine is lost")
        if st.button("Search"):
            hits = retrieve(q, k=3)
            if not hits:
                st.warning("No relevant information found (below the relevance threshold).")
            for chunk, score in hits:
                st.markdown(f"**[{chunk.source}]** · match score `{score:.3f}`")
                st.write(chunk.text)
                st.divider()

    with tab_compare:
        st.subheader("Same question, with and without retrieval")
        cq = st.text_input("Question to compare", "How is savings interest paid?")
        if st.button("Compare responses"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Without retrieval**")
                r = smart_agent(cq, strategy="zero_shot", use_retrieval=False)
                st.info(r.response)
            with col2:
                st.markdown("**With retrieval (RAG)**")
                r = smart_agent(cq, strategy="grounded", use_retrieval=True)
                st.success(r.response)
                if r.sources:
                    st.caption("Sources: " + ", ".join(r.sources))

    with tab_missing:
        st.subheader("When the answer isn't in the documents")
        st.markdown(
            "If nothing relevant is found, the agent **says it doesn't have the information** and points "
            "to the secure channel — instead of guessing. This protects the *don't make up customer data* rule."
        )
        mq = st.text_input("Ask something outside the KB", "What is the capital of France?")
        if st.button("Test missing-info behaviour"):
            hits = retrieve(mq, k=3)
            if not hits:
                st.warning("Retrieval found nothing relevant → the agent should decline to answer.")
            r = smart_agent(mq, strategy="grounded", use_retrieval=True)
            st.info(r.response)

