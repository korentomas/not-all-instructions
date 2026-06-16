"""Deterministic compliance scorer - wraps `checkers.check_decision` (verbatim).

Methodological fidelity: scores the FINAL assistant text at each
test turn with the same 12 checkers, same 0-3 scale, same procedure as the
reference harness. The numbers differ across models by design; the METHOD is
preserved. The scoring loop is a pure function so it can be unit-tested against
`check_decision` directly.
"""

from __future__ import annotations

import asyncio
import re

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, get_model
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    ScoreReducer,
    Scorer,
    Target,
    metric,
    score_reducer,
    scorer,
)
from inspect_ai.solver import TaskState

from retention.checkers import check_decision
from retention.prompts import INSTRUCTION_TEXT, JUDGE_SYSTEM, judge_prompt

JUDGE_ROLES = ("judge_1", "judge_2", "judge_3")


def build_scored_text(completion: str, writes: list[dict]) -> str:
    """Build the text scored for one test turn: the union of the assistant's
    completion text and the content of any ``write_file`` tool calls on that turn.

    Models often route their code through the ``write_file`` TOOL CALL rather than
    the assistant text. That tool content used to be read by nothing, so a turn
    whose code lived only in the tool call scored as if it had no code (the checker
    gate returned a flat score). Here we fold each written file's content back into
    the scored text, wrapped in a fenced ```python block so the checker's
    fenced-code extraction sees it.

    Genuinely-empty handling (M1): if there is no completion text AND no write_file
    content, return "" so the checker gate abstains (the no-code path returns -1) - 
    we never fabricate text. ``writes`` must already be filtered to THIS turn.

    This is the single source of truth: the live solver and the offline re-scorer
    both call this, so they score byte-identical text.
    """
    parts: list[str] = []
    completion = completion or ""
    if completion.strip():
        parts.append(completion)
    for w in writes:
        content = (w.get("content") or "").strip()
        if content:
            parts.append(f"```python\n{content}\n```")
    return "\n".join(parts)


def score_turn_outputs(
    turn_outputs: dict[int, str],
    test_turns: dict[int, list[str]],
) -> tuple[dict[str, int], dict[str, str]]:
    """Pure scoring: run check_decision per (decision, test_turn) over the text.

    Returns (value, reasons) keyed by ``{decision_id}@{turn}``. Same logic the
    reference runner applied to ``response.content`` on test turns.
    """
    value: dict[str, int] = {}
    reasons: dict[str, str] = {}
    for turn, text in turn_outputs.items():
        for decision_id in test_turns.get(turn, []):
            r = check_decision(decision_id, text)
            key = f"{decision_id}@{turn}"
            value[key] = r.score
            reasons[key] = r.reason
    return value, reasons


@metric
def compliance_mean() -> Metric:
    """Mean ordinal compliance (0-3) across all (decision, turn) keys and samples.

    Custom metric because built-in mean()/stderr() don't reduce dict-valued
    Score.value (AISI BEST_PRACTICES). Per-decision / per-turn breakdowns come later.
    """

    def m(scores: list[SampleScore]) -> float:
        vals: list[float] = []
        for s in scores:
            v = s.score.value
            if isinstance(v, dict):
                # only valid ordinal scores 0-3 (excludes the -1 unparseable sentinel)
                vals.extend(
                    float(x) for x in v.values()
                    if isinstance(x, (int, float)) and 0 <= x <= 3
                )
        return sum(vals) / len(vals) if vals else 0.0

    return m


@score_reducer(name="retention_mean")
def retention_mean() -> ScoreReducer:
    """Reduce a sample's per-epoch dict scores into one dict, mean per key.

    The built-in "mean" reducer (a) assumes every epoch produces the identical key
    set and (b) averages the -1 unparseable sentinel into the per-key mean - which
    contradicts ``compliance_mean`` (that excludes -1). This reducer is dict-aware,
    takes the union of keys across epochs, and excludes -1 (and any out-of-range
    value) before averaging; a key with no valid value reduces to -1.
    """

    def reduce(scores: list[Score]) -> Score:
        keys: set[str] = set()
        for s in scores:
            if isinstance(s.value, dict):
                keys.update(s.value.keys())
        merged: dict[str, float] = {}
        for k in keys:
            vals = [
                float(s.value[k])
                for s in scores
                if isinstance(s.value, dict)
                and isinstance(s.value.get(k), (int, float))
                and 0 <= s.value[k] <= 3
            ]
            merged[k] = sum(vals) / len(vals) if vals else -1.0
        return Score(value=merged)

    return reduce


@scorer(metrics=[compliance_mean()])
def deterministic_compliance() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        turn_outputs = state.store.get("turn_outputs", {})
        test_turns = state.metadata["test_turns"]
        value, reasons = score_turn_outputs(turn_outputs, test_turns)
        explanation = "\n".join(f"{k}: {v} ({reasons[k]})" for k, v in value.items())
        return Score(value=value, explanation=explanation)

    return score


# judges are told to reply with ONLY the number. Accept a lone 0-3 token (optional
# surrounding whitespace/quotes/period); anything else - prose, multi-digit like "10",
# years like "2024", "5/10" - is UNPARSEABLE (-1), never silently mis-scored.
_JUDGE_SCORE_RE = re.compile(r"[\s'\"]*([0-3])[\s.'\"]*")
# A 0-3 that LEADS the reply, then a boundary (whitespace / punctuation / markdown
# bold / end). Judges sometimes answer "0\n\n<explanation>" or "**3**" - the score
# is unambiguous there. The trailing boundary keeps multi-digit ("10", "2024") and
# fractions ("5/10") UNPARSEABLE, so we never grab a mid-number digit.
_JUDGE_LEAD_RE = re.compile(r"[\s'\"*]*([0-3])(?:\b|[\s.:)\"'*])")


def _parse_judge_score(text: str) -> int:
    """Parse a strict 0-3 ordinal from the judge reply. -1 = unparseable (excluded).

    Accepts a bare digit (the requested format) or a digit that leads the reply
    followed by an explanation. Mid-text digits and multi-digit numbers stay -1.
    """
    text = (text or "").strip()
    m = _JUDGE_SCORE_RE.fullmatch(text)
    if m:
        return int(m.group(1))
    m = _JUDGE_LEAD_RE.match(text)
    return int(m.group(1)) if m else -1


@scorer(metrics=[compliance_mean()])
def judge_panel() -> Scorer:
    """Secondary channel (v2 bias fix #2/#3): 3 cross-family judges rate the same
    (decision, test_turn) compliance the deterministic checker measures → enables
    checker-judge and inter-judge agreement (computed offline in analysis/).

    Judges are blind to condition/model/checker-verdict; they see only instruction
    + code (they must see the instruction to rate compliance). Per-judge scores go
    in Score.value (AISI: reducible values belong in value, not metadata).
    """

    async def score(state: TaskState, target: Target) -> Score:
        turn_outputs = state.store.get("turn_outputs", {})
        test_turns = state.metadata["test_turns"]
        judges = {r: get_model(role=r, default=get_model()) for r in JUDGE_ROLES}

        calls = []
        keys: list[str] = []
        for turn, text in turn_outputs.items():
            for decision_id in test_turns.get(turn, []):
                prompt = judge_prompt(INSTRUCTION_TEXT[decision_id], text)
                messages = [
                    ChatMessageSystem(content=JUDGE_SYSTEM),
                    ChatMessageUser(content=prompt),
                ]
                for role in JUDGE_ROLES:
                    calls.append(judges[role].generate(messages))
                    keys.append(f"{role}:{decision_id}@{turn}")

        # return_exceptions=True: one judge failing (rate-limit / content-filter after
        # retries on long contexts) must NOT discard the whole panel - that judge's key
        # gets -1, the rest survive. gather preserves order, so zip(keys, outputs) aligns.
        outputs = await asyncio.gather(*calls, return_exceptions=True)
        value = {
            k: (-1 if isinstance(o, BaseException) else _parse_judge_score(o.completion))
            for k, o in zip(keys, outputs)
        }
        return Score(value=value)

    return score
