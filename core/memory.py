"""Conversation memory: short-term (window) and long-term (summary) with reset rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from core.safety import redact_pii


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class ConversationMemory:
    short_term_window: int = 6          # keep last N turns verbatim
    turns: List[Turn] = field(default_factory=list)
    long_term_summary: str = ""         # rolling condensed summary
    facts: Dict[str, str] = field(default_factory=dict)  # non-PII preferences only

    def add(self, role: str, content: str) -> None:
        self.turns.append(Turn(role, content))
        if len(self.turns) > self.short_term_window:
            self._condense_oldest()

    def _condense_oldest(self) -> None:
        old = self.turns.pop(0)
        # Long-term memory stores only REDACTED gist — never raw PII.
        snippet = redact_pii(old.content)[:120]
        self.long_term_summary = (self.long_term_summary + f" | {old.role}: {snippet}").strip(" |")

    def remember_preference(self, key: str, value: str) -> None:
        """Store a small non-PII preference (e.g. preferred language, topic)."""
        self.facts[redact_pii(key)] = redact_pii(value)

    def short_term_context(self) -> str:
        return "\n".join(f"{t.role}: {t.content}" for t in self.turns)

    def full_context(self) -> str:
        parts = []
        if self.long_term_summary:
            parts.append(f"[Earlier summary] {self.long_term_summary}")
        if self.facts:
            parts.append("[Preferences] " + ", ".join(f"{k}={v}" for k, v in self.facts.items()))
        parts.append(self.short_term_context())
        return "\n".join(parts)

    def reset(self, keep_preferences: bool = False) -> None:
        """Retention/reset rule: clear conversation; optionally keep preferences."""
        self.turns.clear()
        self.long_term_summary = ""
        if not keep_preferences:
            self.facts.clear()
