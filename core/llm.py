"""LangChain LLM factory with a deterministic offline fallback.

When a provider key is configured (`core.config.llm_available()`), real LangChain
chat + embedding models are returned. Otherwise a rule-based `MockChatModel` and a
hashing-based `MockEmbeddings` keep every phase fully runnable offline. Both mocks
subclass the LangChain base classes, so they compose in LCEL chains and FAISS just
like the real models.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from core import config


# ---------------------------------------------------------------------------
# Offline mock chat model (a real LangChain BaseChatModel)
# ---------------------------------------------------------------------------
class MockChatModel(BaseChatModel):
    """Deterministic offline chat model that mimics grounded banking answers."""

    temperature: float = 0.2

    @property
    def _llm_type(self) -> str:
        return "mock-banking-chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = "\n".join(str(getattr(m, "content", m)) for m in messages)
        message = AIMessage(content=self._respond(text))
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _respond(self, prompt: str) -> str:
        p = prompt.lower()
        if "context:" in p and "(no relevant context found)" not in p:
            # RAG-style answer: quote a snippet of the retrieved context so the
            # offline demo stays grounded in the actual knowledge base.
            ctx = prompt.split("Context:", 1)[1].split("Customer:", 1)[0].strip()
            snippet = " ".join(ctx.split()[:45])
            return (
                f"Based on the bank's published information: {snippet} "
                "(Offline demo answer — configure an API key for a full LLM "
                "response.) I won't move money, approve actions, or give legal "
                "advice, and I won't guess your personal account details."
            )
        if any(w in p for w in ["hello", "hi", "hey"]):
            return "Hello! I'm your informational banking assistant. How can I help you understand our products or processes today?"
        if "interest" in p or "savings" in p:
            return "Interest on savings accounts is calculated daily and paid monthly. For your exact rate, check the app or product page. (Offline demo answer.)"
        if "card" in p and "lost" in p:
            return "If your card is lost, you can freeze it in the mobile app under Card Controls, then request a replacement. For immediate help call the number on our website. (Offline demo answer.)"
        return (
            "Here is general information to help you. I can't move money, approve "
            "requests, or provide legal advice, and I won't guess personal account "
            "details. (Offline demo answer — set OPENAI_API_KEY for full responses.)"
        )


class MockEmbeddings(Embeddings):
    """Deterministic hashing embeddings so retrieval works without a provider."""

    dim = 256

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        for token in _tokenize(text):
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


def _tokenize(text: str) -> List[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


# ---------------------------------------------------------------------------
# Public factories
# ---------------------------------------------------------------------------
def get_chat_model(temperature: float = 0.2) -> BaseChatModel:
    if not config.llm_available():
        return MockChatModel(temperature=temperature)
    if config.USE_AZURE:
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_deployment=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            temperature=temperature,
        )
    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": config.OPENAI_CHAT_MODEL,
        "api_key": config.OPENAI_API_KEY,
        "temperature": temperature,
    }
    if config.OPENAI_BASE_URL:
        kwargs["base_url"] = config.OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def get_embeddings() -> Embeddings:
    if not config.llm_available():
        return MockEmbeddings()
    if config.USE_AZURE:
        from langchain_openai import AzureOpenAIEmbeddings

        return AzureOpenAIEmbeddings(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_deployment=config.AZURE_OPENAI_EMBED_DEPLOYMENT,
        )
    from langchain_openai import OpenAIEmbeddings

    kwargs = {"model": config.OPENAI_EMBED_MODEL, "api_key": config.OPENAI_API_KEY}
    if config.OPENAI_BASE_URL:
        kwargs["base_url"] = config.OPENAI_BASE_URL
    return OpenAIEmbeddings(**kwargs)


def mode_label() -> str:
    return "🟢 LIVE LLM" if config.llm_available() else "🟡 OFFLINE (mock) mode"
