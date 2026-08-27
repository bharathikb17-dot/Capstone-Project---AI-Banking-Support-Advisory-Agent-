"""Tools the agent may call (Phase 5), with schemas, routing, and safeguards.

All tools are READ-ONLY and non-transactional. There is deliberately no
"transfer_money" tool — the agent must refuse such requests, not execute them.
Tools are LangChain `StructuredTool`s created via the `@tool` decorator.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from langchain_core.tools import BaseTool, tool

from core.rag import format_context, retrieve


# ---------------------------------------------------------------------------
# Tool implementations (LangChain StructuredTools)
# ---------------------------------------------------------------------------
@tool
def kb_search(query: str) -> str:
    """Look up factual banking information from the knowledge base."""
    hits = retrieve(query, k=3)
    if not hits:
        return "No relevant knowledge-base article found."
    return format_context(hits)


@tool
def loan_calculator(amount: float, annual_rate_pct: float, months: int) -> str:
    """Estimate monthly loan repayments from amount, annual rate %, and months.

    Educational only — not an offer of credit.
    """
    if amount <= 0 or months <= 0:
        return "Please provide a positive loan amount and term."
    r = (annual_rate_pct / 100) / 12
    if r == 0:
        payment = amount / months
    else:
        payment = amount * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = payment * months
    return (
        f"Estimated monthly repayment: {payment:,.2f} for {months} months "
        f"(total ~{total:,.2f}, interest ~{total - amount:,.2f}). "
        "This is a general estimate, not a credit offer or approval."
    )


@tool
def branch_hours(query: str = "") -> str:
    """Get general branch opening hours (static, non-personal)."""
    today = date.today().strftime("%A")
    return f"Today is {today}. Branches: Mon–Fri 9am–5pm, Sat 9am–1pm. App & 24/7 line always open."


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------
TOOLS: Dict[str, BaseTool] = {t.name: t for t in (kb_search, loan_calculator, branch_hours)}

# Requests that must NOT be served by any tool — safeguard against misuse.
BLOCKED_TOOL_INTENTS = [
    r"\btransfer\b", r"\bpay\b", r"\bwithdraw\b", r"\bapprove\b", r"\bauthori",
]


@dataclass
class ToolDecision:
    tool: str | None
    args: Dict
    reason: str
    blocked: bool = False


def route(user_input: str) -> ToolDecision:
    """Lightweight rule-based router with loop/misuse safeguards."""
    text = user_input.lower()

    for pat in BLOCKED_TOOL_INTENTS:
        if re.search(pat, text):
            return ToolDecision(None, {}, "Transactional/approval intent — no tool may act.", blocked=True)

    m = re.search(r"(\d[\d,]*)\D+(\d+(?:\.\d+)?)\s*%?\D+(\d+)\s*month", text)
    if ("loan" in text or "repay" in text or "calculat" in text) and m:
        amount = float(m.group(1).replace(",", ""))
        rate = float(m.group(2))
        months = int(m.group(3))
        return ToolDecision("loan_calculator", {"amount": amount, "annual_rate_pct": rate, "months": months}, "Loan math request with parameters.")

    if "hour" in text or "open" in text or "branch" in text:
        return ToolDecision("branch_hours", {}, "Asking about opening hours.")

    return ToolDecision("kb_search", {"query": user_input}, "General informational question -> knowledge base.")


MAX_TOOL_CALLS = 3  # loop-prevention guard


def run_with_tools(user_input: str, call_log: List[str] | None = None) -> Dict:
    """Route to a single tool, execute with safeguards, and return a trace."""
    call_log = call_log if call_log is not None else []
    decision = route(user_input)

    if decision.blocked:
        return {"blocked": True, "tool": None, "reason": decision.reason, "output": None, "trace": call_log}

    if len(call_log) >= MAX_TOOL_CALLS:
        return {"blocked": True, "tool": None, "reason": "Max tool calls reached (loop guard).", "output": None, "trace": call_log}

    tool = TOOLS[decision.tool]
    call_log.append(f"{tool.name}({decision.args})")
    try:
        output = tool.invoke(decision.args)
    except Exception as exc:
        output = f"Tool argument error: {exc}"
    return {"blocked": False, "tool": tool.name, "reason": decision.reason, "output": output, "trace": call_log}
