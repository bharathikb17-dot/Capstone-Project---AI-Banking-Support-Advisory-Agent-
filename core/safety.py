"""Safety guardrails for the Banking Advisory Agent.

Implements the four hard requirements for Scenario 2:
  1. Refuse money movement, approvals, or legal advice.
  2. Do not hallucinate customer data.
  3. Escalate ambiguous or high-risk cases.
  4. Do not store PII in logs (redaction helpers).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# 1) Refusal triggers — money movement, approvals, legal advice
# ---------------------------------------------------------------------------
MONEY_MOVEMENT_PATTERNS = [
    r"\btransfer\b", r"\bsend money\b", r"\bwire\b", r"\bpay(ee|ment)?\b",
    r"\bwithdraw\b", r"\bmove (my )?funds?\b", r"\btop ?up\b", r"\bremit\b",
    r"\bstanding order\b", r"\bdirect debit\b", r"\bloan disburs", r"\bcash out\b",
]
APPROVAL_PATTERNS = [
    r"\bapprove\b", r"\bauthorize|authorise\b", r"\bsign off\b",
    r"\boverride\b", r"\bwaive\b", r"\bincrease (my )?(credit )?limit\b",
    r"\bunblock\b", r"\breset (my )?password\b", r"\bactivate (my )?card\b",
]
LEGAL_ADVICE_PATTERNS = [
    r"\bsue\b", r"\blawsuit\b", r"\blegal(ly)? (advice|obligation|liable)\b",
    r"\bshould i (sign|accept)\b.*\bcontract\b", r"\bis (this|it) (legally )?binding\b",
    r"\btax (advice|return) should i\b", r"\bpower of attorney\b",
]

# ---------------------------------------------------------------------------
# 3) Escalation triggers — ambiguity and high risk
# ---------------------------------------------------------------------------
HIGH_RISK_PATTERNS = [
    r"\bfraud\b", r"\bscam\b", r"\bstolen\b", r"\bunauthori[sz]ed\b",
    r"\bhack(ed)?\b", r"\bidentity theft\b", r"\bdispute\b", r"\bcomplaint\b",
    r"\bemergency\b", r"\burgent\b", r"\bthreat", r"\bharm",
]
AMBIGUITY_PATTERNS = [
    r"\bnot sure\b", r"\bmaybe\b", r"\bi think\b", r"\bwhatever you\b",
    r"\bdo whatever\b", r"\bany(thing)? (is )?(fine|okay)\b",
]

# ---------------------------------------------------------------------------
# 4) PII patterns used only for REDACTION before logging
# ---------------------------------------------------------------------------
PII_PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "CARD": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
    "PHONE": re.compile(r"\b(?:\+?\d[\d ()-]{7,}\d)\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "ACCOUNT": re.compile(r"\bacc(?:t|ount)?\s*(?:no|number|#)?\s*[-:#]?\s*\d{6,}\b", re.I),
    "PIN": re.compile(r"\bpin\b\s*(?:is|=|:)?\s*\d{3,6}\b", re.I),
}

REFUSAL_MESSAGE = (
    "I'm an informational banking assistant and can't help move money, approve or "
    "authorise actions, or provide legal advice. I can explain how these processes "
    "work and point you to the right secure channel. For this request please use the "
    "official banking app, call the number on the back of your card, or visit a branch."
)

ESCALATION_MESSAGE = (
    "This looks like it may be sensitive, high-risk, or unclear, so I'm routing you to "
    "a human specialist to make sure it's handled correctly and securely."
)


@dataclass
class SafetyResult:
    allowed: bool
    action: str  # "allow" | "refuse" | "escalate"
    categories: List[str] = field(default_factory=list)
    message: str = ""


def _matches(text: str, patterns: List[str]) -> List[str]:
    hits = []
    for p in patterns:
        if re.search(p, text, flags=re.I):
            hits.append(p)
    return hits


def redact_pii(text: str) -> str:
    """Replace any detected PII with typed placeholders. Used before logging."""
    if not text:
        return text
    redacted = text
    for label, pattern in PII_PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label}]", redacted)
    return redacted


def check_input(text: str) -> SafetyResult:
    """Pre-flight guardrail applied to every user message."""
    categories: List[str] = []

    if _matches(text, MONEY_MOVEMENT_PATTERNS):
        categories.append("money_movement")
    if _matches(text, APPROVAL_PATTERNS):
        categories.append("approval")
    if _matches(text, LEGAL_ADVICE_PATTERNS):
        categories.append("legal_advice")

    if categories:
        return SafetyResult(False, "refuse", categories, REFUSAL_MESSAGE)

    risk = _matches(text, HIGH_RISK_PATTERNS)
    ambiguous = _matches(text, AMBIGUITY_PATTERNS)
    if risk or ambiguous:
        cats = (["high_risk"] if risk else []) + (["ambiguous"] if ambiguous else [])
        return SafetyResult(False, "escalate", cats, ESCALATION_MESSAGE)

    return SafetyResult(True, "allow", [], "")


def check_output(text: str) -> SafetyResult:
    """Post-flight guardrail. Catches fabricated customer-specific data leaks."""
    # If the model volunteers concrete account/balance numbers we didn't retrieve,
    # treat it as a potential hallucination and escalate.
    fabricated = re.search(r"\byour (balance|account) (is|number)\b.*\d", text, re.I)
    if fabricated:
        return SafetyResult(
            False, "escalate", ["possible_hallucinated_customer_data"],
            ESCALATION_MESSAGE,
        )
    return SafetyResult(True, "allow", [], "")


SAFETY_SYSTEM_RULES = """You are a NON-TRANSACTIONAL AI banking support and advisory assistant.
Hard rules you must never break:
1. NEVER perform or promise to perform money movement (transfers, payments, withdrawals).
2. NEVER approve, authorise, override, waive, or unblock anything.
3. NEVER give legal or binding tax advice; give general educational information only.
4. NEVER invent customer-specific data (balances, account numbers, transactions). If you
   don't have it from retrieved context, say you don't have access and explain the secure
   channel to obtain it.
5. If a request is ambiguous, high-risk, or involves fraud/disputes, escalate to a human.
Always be concise, factual, and cite the knowledge-base source when you use one."""
