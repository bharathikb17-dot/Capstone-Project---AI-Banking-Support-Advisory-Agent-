"""Feedback storage and adaptive behaviour (Phase 7).

Feedback is stored (PII-redacted) and turned into simple behaviour adjustments:
tone (concise vs detailed), and topic-level preferences. Demonstrates before/after.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from core.config import LOG_DIR
from core.safety import redact_pii

FEEDBACK_FILE = LOG_DIR / "feedback.jsonl"


@dataclass
class Feedback:
    ts: str
    question: str
    answer: str
    rating: str        # "up" | "down"
    signal: str        # "too_long" | "too_short" | "unclear" | "good" | ""
    note: str = ""


def store_feedback(question: str, answer: str, rating: str, signal: str = "", note: str = "") -> Feedback:
    fb = Feedback(
        ts=datetime.now(timezone.utc).isoformat(),
        question=redact_pii(question),
        answer=redact_pii(answer),
        rating=rating,
        signal=signal,
        note=redact_pii(note),
    )
    with FEEDBACK_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(fb)) + "\n")
    return fb


def load_feedback() -> List[Feedback]:
    if not FEEDBACK_FILE.exists():
        return []
    out = []
    for line in FEEDBACK_FILE.read_text(encoding="utf-8").splitlines():
        try:
            out.append(Feedback(**json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            continue
    return out


@dataclass
class BehaviorProfile:
    verbosity: str = "normal"   # "concise" | "normal" | "detailed"
    notes: List[str] = field(default_factory=list)


def derive_profile() -> BehaviorProfile:
    """Turn accumulated feedback into a behaviour profile the agent adapts to."""
    fbs = load_feedback()
    signals = Counter(f.signal for f in fbs if f.signal)
    profile = BehaviorProfile()
    if signals.get("too_long", 0) > signals.get("too_short", 0):
        profile.verbosity = "concise"
        profile.notes.append("Users found answers too long -> be concise.")
    elif signals.get("too_short", 0) > signals.get("too_long", 0):
        profile.verbosity = "detailed"
        profile.notes.append("Users wanted more detail -> be more thorough.")
    if signals.get("unclear", 0):
        profile.notes.append("Some answers were unclear -> add a short summary line and cite sources.")
    return profile


def profile_instruction(profile: BehaviorProfile) -> str:
    mapping = {
        "concise": "Answer in at most 2 short sentences.",
        "normal": "Answer clearly in 2–4 sentences.",
        "detailed": "Give a thorough, step-by-step answer.",
    }
    extra = " ".join(profile.notes)
    return f"{mapping[profile.verbosity]} {extra}".strip()


def clear_feedback() -> None:
    if FEEDBACK_FILE.exists():
        FEEDBACK_FILE.unlink()
