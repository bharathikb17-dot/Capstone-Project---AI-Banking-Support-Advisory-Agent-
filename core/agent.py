"""Agent orchestration: baseline (rules) and smart (LLM + RAG + guardrails).

The smart agent is built from idiomatic LangChain LCEL chains
(`ChatPromptTemplate | chat_model | StrOutputParser`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.llm import get_chat_model
from core.rag import format_context, retrieve
from core.safety import (
    SAFETY_SYSTEM_RULES,
    check_input,
    check_output,
)

# ---------------------------------------------------------------------------
# Baseline rule/template agent (Phase 2)
# ---------------------------------------------------------------------------
BASELINE_RULES = {
    "hours": "Our branches are open Mon–Fri 9am–5pm. The app and 24/7 support line are always available.",
    "card": "For lost or stolen cards, freeze the card in the app under Card Controls, then report it.",
    "savings": "Savings interest is calculated daily and paid monthly. Check the app for your current rate.",
    "fraud": "If you suspect fraud, freeze your card in the app and report it via the 24/7 fraud line.",
    "loan": "Loan rates depend on amount, term, and a credit assessment. Use the in-app calculator to estimate.",
}
BASELINE_FALLBACK = "I'm a basic banking FAQ bot. I can answer questions about cards, savings, loans, hours, and fraud."


def baseline_agent(user_input: str) -> str:
    """Keyword-matching template bot with no understanding — intentionally limited."""
    text = user_input.lower()
    for key, answer in BASELINE_RULES.items():
        if key in text:
            return answer
    return BASELINE_FALLBACK


# ---------------------------------------------------------------------------
# Smart agent (Phases 3–6)
# ---------------------------------------------------------------------------
@dataclass
class AgentResult:
    response: str
    action: str  # allow | refuse | escalate
    categories: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    used_retrieval: bool = False
    prompt_strategy: str = "default"


PROMPT_STRATEGIES = {
    "zero_shot": ChatPromptTemplate.from_messages(
        [
            ("system", SAFETY_SYSTEM_RULES),
            ("human", "Answer the customer's question.\n\nCustomer: {q}"),
        ]
    ),
    "persona": ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SAFETY_SYSTEM_RULES
                + "\n\nYou are 'Ava', a friendly, precise banking support advisor. "
                "Be warm but concise (max 4 sentences).",
            ),
            ("human", "Customer: {q}"),
        ]
    ),
    "grounded": ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SAFETY_SYSTEM_RULES
                + "\n\nUse ONLY the context to answer. If the context is empty or "
                "insufficient, say you don't have that information and name the secure channel.",
            ),
            ("human", "Context:\n{context}\n\nCustomer: {q}\n\nCite sources in [brackets]."),
        ]
    ),
}
DEFAULT_STRATEGY = "grounded"  # chosen in Phase 3 (see phase page for justification)


def _build_chain(strategy: str, temperature: float):
    """Compose an LCEL chain: prompt | chat model | string output parser."""
    prompt = PROMPT_STRATEGIES.get(strategy, PROMPT_STRATEGIES[DEFAULT_STRATEGY])
    model = get_chat_model(temperature=temperature)
    return prompt | model | StrOutputParser()


def smart_agent(
    user_input: str,
    strategy: str = DEFAULT_STRATEGY,
    use_retrieval: bool = True,
    history: Optional[str] = None,
    temperature: float = 0.2,
) -> AgentResult:
    """Full pipeline: input guardrail -> retrieval -> LCEL chain -> output guardrail."""
    gate = check_input(user_input)
    if not gate.allowed:
        return AgentResult(gate.message, gate.action, gate.categories)

    context, sources, used = "", [], False
    if use_retrieval:
        hits = retrieve(user_input, k=3)
        context = format_context(hits)
        sources = sorted({c.source for c, _ in hits})
        used = bool(hits)

    chain = _build_chain(strategy, temperature)
    question = user_input if not history else f"{history}\n\nCustomer: {user_input}"
    answer = chain.invoke({"q": question, "context": context or "(no relevant context found)"})

    out_gate = check_output(answer)
    if not out_gate.allowed:
        return AgentResult(out_gate.message, out_gate.action, out_gate.categories, sources, used, strategy)

    return AgentResult(answer, "allow", [], sources, used, strategy)
