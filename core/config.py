"""Central configuration and constants for the Banking Advisory Agent capstone."""
from __future__ import annotations

import os
from pathlib import Path

# Use the OS certificate store so SSL works behind corporate proxies/inspection
# (required for LangSmith tracing and other HTTPS calls).
try:
    import truststore

    truststore.inject_into_ssl()
except Exception:
    pass

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
KB_DIR = DATA_DIR / "banking_kb"
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT_DIR / ".env")


def _get(name: str, default: str = "") -> str:
    """Read config from environment first, then Streamlit secrets (cloud)."""
    val = os.getenv(name)
    if val:
        return val
    try:  # st.secrets works only inside a Streamlit runtime
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# LLM provider settings
# ---------------------------------------------------------------------------
OPENAI_API_KEY = _get("OPENAI_API_KEY").strip()
OPENAI_BASE_URL = _get("OPENAI_BASE_URL").strip()
OPENAI_CHAT_MODEL = _get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_EMBED_MODEL = _get("OPENAI_EMBED_MODEL", "text-embedding-3-small")

USE_AZURE = _get("USE_AZURE", "0") == "1"
AZURE_OPENAI_API_KEY = _get("AZURE_OPENAI_API_KEY").strip()
AZURE_OPENAI_ENDPOINT = _get("AZURE_OPENAI_ENDPOINT").strip()
AZURE_OPENAI_API_VERSION = _get("AZURE_OPENAI_API_VERSION", "2024-06-01")
AZURE_OPENAI_CHAT_DEPLOYMENT = _get("AZURE_OPENAI_CHAT_DEPLOYMENT").strip()
AZURE_OPENAI_EMBED_DEPLOYMENT = _get("AZURE_OPENAI_EMBED_DEPLOYMENT").strip()


def llm_available() -> bool:
    """True when a real LLM provider is configured, else app runs in mock mode."""
    if USE_AZURE:
        return bool(AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_CHAT_DEPLOYMENT)
    return bool(OPENAI_API_KEY)


# ---------------------------------------------------------------------------
# LangSmith tracing (enabled automatically when an API key is present)
# ---------------------------------------------------------------------------
LANGSMITH_API_KEY = (_get("LANGSMITH_API_KEY") or _get("LANGCHAIN_API_KEY")).strip()
LANGSMITH_PROJECT = (_get("LANGSMITH_PROJECT") or _get("LANGCHAIN_PROJECT") or "banking-advisory-agent").strip()
LANGSMITH_ENDPOINT = (_get("LANGSMITH_ENDPOINT") or _get("LANGCHAIN_ENDPOINT") or "https://api.smith.langchain.com").strip()


def langsmith_enabled() -> bool:
    return bool(LANGSMITH_API_KEY)


def configure_langsmith() -> bool:
    """Export the env vars LangChain reads to send traces to LangSmith."""
    if not langsmith_enabled():
        return False
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
    return True


configure_langsmith()


# ---------------------------------------------------------------------------
# Scenario metadata (Scenario 2 — Banking Advisory, Non-Transactional)
# ---------------------------------------------------------------------------
APP_TITLE = "AI Banking Support & Advisory Agent"
APP_SUBTITLE = "Track A · LangChain · Scenario 2 (Non-Transactional)"

SAFETY_REQUIREMENTS = [
    "Must refuse money movement, approvals, or legal advice.",
    "Must not hallucinate customer data.",
    "Must escalate ambiguous or high-risk cases.",
    "Must not store PII in logs.",
]
