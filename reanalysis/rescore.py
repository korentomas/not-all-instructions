"""Offline re-score: re-run the FIXED checkers over already-saved responses.

The model generations are persisted in the `.eval` logs (assistant text AND the
`write_file` tool-call content). The original scoring had two bugs (checker
leniency; write_file content never scored). This script re-derives the per-turn
scored text the corrected way — `build_scored_text(completion, writes)` over the
union of the last assistant completion and that turn's write_file content — and
re-runs the fixed `check_decision`. No model calls, no API cost.

Writes attribution is reconstructed from the message stream: each `user` message
starts a new turn (turns 0..25), and any `write_file` tool call is attributed to
the current turn (validated: turn 22 carries the test file). This works for old
logs that pre-date the turn-tagged `store["writes"]`.

    python rescore.py logs/retention-v2-final [more dirs...] -o rescored_scores.csv
"""

from __future__ import annotations

import argparse
import glob
import os
import re

import pandas as pd

from inspect_ai.log import read_eval_log

from retention.analysis.extract import _model_key
from retention.checkers import check_decision
from retention.scorer import build_scored_text


def _per_turn(sample):
    """-> {turn:int -> (completion_text:str, [write_dict,...])} from the messages."""
    turn = -1
    completions: dict[int, str] = {}
    writes: dict[int, list] = {}
    for m in sample.messages or []:
        role = getattr(m, "role", None)
        if role == "user":
            turn += 1
        elif role == "assistant":
            # last assistant text in the turn wins (== out.completion)
            txt = getattr(m, "text", "") or ""
            if txt.strip():
                completions[turn] = txt
            for tc in getattr(m, "tool_calls", None) or []:
                if tc.function != "write_file":
                    continue
                content = (tc.arguments or {}).get("content", "")
                if not content:
                    # Truncated/malformed call (max_tokens cut the JSON mid-string).
                    # Salvage the partial content from the parse error so a cut-off
                    # file still scores on what was written — graceful degradation,
                    # matching v1's text-based scoring. Else the whole turn is lost.
                    content = _salvage_truncated_content(tc)
                if content:
                    writes.setdefault(turn, []).append({"content": content})
    turns = set(completions) | set(writes)
    return {t: (completions.get(t, ""), writes.get(t, [])) for t in turns}


def _json_unescape(s: str) -> str:
    """Unescape a JSON string body that may be truncated mid-escape."""
    out, i, n = [], 0, len(s)
    table = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/"}
    while i < n:
        c = s[i]
        if c == "\\":
            if i + 1 < n:
                out.append(table.get(s[i + 1], s[i + 1]))
                i += 2
            else:
                break  # trailing backslash from truncation
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _salvage_truncated_content(tc) -> str:
    """Recover the partial `content` of a truncated write_file tool call from its
    parse error (the raw malformed JSON), or '' if nothing recoverable."""
    raw = getattr(tc, "parse_error", None)
    if not isinstance(raw, str) or '"content"' not in raw:
        return ""
    m = re.search(r'"content"\s*:\s*"', raw)
    if not m:
        return ""
    # everything after the opening quote of content, up to (missing) close quote
    return _json_unescape(raw[m.end():])


def rescore_dirs(dirs: list[str]) -> pd.DataFrame:
    rows = []
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.eval")):
            log = read_eval_log(f)
            if log.status not in ("success", "started", "error", "cancelled"):
                continue
            model = _model_key(log.eval.model)
            for s in log.samples or []:
                # Only re-score samples the live run COMPLETED (have a score dict).
                # Errored/overflowed samples (e.g. qwen3.5-27b on pymc) have partial,
                # truncated conversations — their fragments must not enter the fit.
                if not s.scores:
                    continue
                md = s.metadata or {}
                codebase = md.get("codebase")
                condition = md.get("condition")
                epoch = getattr(s, "epoch", 1)
                test_turns = md.get("test_turns") or {}
                pt = _per_turn(s)
                for turn_str, decisions in test_turns.items():
                    turn = int(turn_str)
                    completion, ws = pt.get(turn, ("", []))
                    text = build_scored_text(completion, ws)
                    for decision in decisions:
                        score = check_decision(decision, text).score
                        if score == -1:
                            continue
                        rows.append(dict(
                            model=model, codebase=codebase, condition=condition,
                            decision=decision, turn=turn, epoch=epoch, score=score,
                        ))
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir", nargs="+")
    ap.add_argument("-o", "--out", default="rescored_scores.csv")
    args = ap.parse_args()
    df = rescore_dirs(args.log_dir)
    df.to_csv(args.out, index=False)
    print(f"re-scored {len(df)} obs | {df.decision.nunique()} decisions | "
          f"{df.model.nunique()} models | conditions {sorted(df.condition.unique())}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
