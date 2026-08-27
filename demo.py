"""Forced demo script — runs the whole agent pipeline end-to-end (offline-safe).

Run:  python demo.py

Produces a deterministic, scripted walkthrough of every capstone phase with
evidence printed to the console, and writes redacted traces to
logs/interactions.jsonl. Works fully offline (mock mode) and with a live LLM.
"""
from __future__ import annotations

from core.agent import baseline_agent, smart_agent
from core.evaluation import (
    PROMPT_EVAL_QUESTIONS,
    compare_prompts,
    failure_case_before_after,
    prompt_metrics,
    run_suite,
)
from core.feedback import (
    clear_feedback,
    derive_profile,
    profile_instruction,
    store_feedback,
)
from core.llm import mode_label
from core.logging_utils import log_interaction, read_logs
from core.memory import ConversationMemory
from core.safety import redact_pii
from core.tools import run_with_tools


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    print(f"AI Banking Support & Advisory Agent — forced demo  ({mode_label()})")

    section("Phase 2 · Baseline agent (rules/templates)")
    for q in ["How is savings interest calculated?", "Please transfer money to my friend"]:
        print(f"Q: {q}\n   -> {baseline_agent(q)}")

    section("Phase 3 · Prompt comparison (same test set, 3 variants)")
    print(f"Test set: {PROMPT_EVAL_QUESTIONS}")
    for m in prompt_metrics():
        print(f"  {m['prompt']:<10} cites={m['cites_sources_rate']}  "
              f"avg_len={m['avg_length_chars']}  | {m['what improved / worsened']}")
    print("\n  Prompt -> Output on 'How is interest on my savings calculated?':")
    for r in compare_prompts("How is interest on my savings calculated?"):
        print(f"   [{r['strategy']:<9}] ({r['action']}) {r['response'][:90]}...")

    section("Phase 4 · Retrieval (RAG): with vs without")
    q = "How is savings interest paid?"
    print(f"Q: {q}")
    print("  Without retrieval:", smart_agent(q, strategy="zero_shot", use_retrieval=False).response[:110])
    r = smart_agent(q, strategy="grounded", use_retrieval=True)
    print("  With retrieval   :", r.response[:110])
    print("  Sources:", r.sources)

    section("Phase 5 · Tool usage (correct selection + blocked misuse)")
    for q in [
        "Estimate a loan of 10000 at 8% over 24 months",
        "What are your branch opening hours?",
        "transfer $500 and approve my overdraft",
    ]:
        res = run_with_tools(q)
        tag = "BLOCKED" if res["blocked"] else f"tool={res['tool']}"
        print(f"Q: {q}\n   -> [{tag}] {res.get('output') or res['reason']}")

    section("Phase 6 · Memory (multi-turn conversation)")
    mem = ConversationMemory(short_term_window=4)
    for msg in ["How does a standing order work?", "And can I cancel it later?"]:
        mem.add("user", msg)
        res = smart_agent(msg, history=mem.full_context())
        mem.add("assistant", res.response)
        print(f"User: {msg}\n   -> {res.response[:100]}")
    print(f"  Turns kept: {len(mem.turns)} | long-term summary: {mem.long_term_summary[:60] or '(empty)'}")

    section("Phase 7 · Adaptation (feedback changes behaviour)")
    clear_feedback()
    q = "Explain how credit card interest works"
    answer = smart_agent(q).response
    for _ in range(3):
        store_feedback(q, answer, "down", "too_long")
    prof = derive_profile()
    print(f"  After 3x 'too_long' feedback -> verbosity={prof.verbosity}")
    print(f"  New style instruction: {profile_instruction(prof)}")

    section("Phase 8 · Safety: PII-safe logging & graceful failure")
    pii = "email me at john.doe@example.com or use card 4111 1111 1111 1111"
    print("  Redaction:", redact_pii(pii))
    log_interaction("demo", pii, "ok", {"demo": True})
    print("  Logged (redacted). Last log input:", read_logs(1)[-1]["user_input"])

    section("Phase 9 · Evaluation suite + failure case fix")
    rep = run_suite()
    print(f"  Overall pass: {rep['passed']}/{rep['total']}  |  "
          f"Safety pass: {rep['safety_passed']}/{rep['safety_total']}")
    fc = failure_case_before_after()
    print(f"  Failure case: '{fc['question']}'")
    print(f"    before fix -> {fc['before_action']} (miss)   "
          f"after fix -> {fc['after_action']}   fixed={fc['fixed']}")

    print("\nDemo complete. Safety actions are deterministic; all logs are redacted.\n")


if __name__ == "__main__":
    main()
