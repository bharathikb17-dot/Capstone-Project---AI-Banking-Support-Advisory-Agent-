"""PII-safe logging utilities.

Satisfies the safety requirement: *Must not store PII in logs.* Every message is
passed through the redactor before it is written to disk or shown in a log view.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.config import LOG_DIR
from core.safety import redact_pii

LOG_FILE = LOG_DIR / "interactions.jsonl"


def log_interaction(phase: str, user_input: str, response: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Append a redacted interaction record to the JSONL log and return it."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "user_input": redact_pii(user_input or ""),
        "response": redact_pii(response or ""),
        "meta": meta or {},
    }
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_logs(limit: int = 200) -> List[Dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def clear_logs() -> None:
    if LOG_FILE.exists():
        LOG_FILE.unlink()
