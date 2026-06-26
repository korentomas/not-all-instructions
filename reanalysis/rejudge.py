"""Offline re-judge: re-run the cross-family judge panel over the CORRECTED
per-turn text (completion + write_file content), parsing 0-3 exactly as the live
`judge_panel` scorer does.

The judge scores saved in the existing logs rated the buggy empty `out.completion`
text (the write_file content was never shown to them) — that is the source of the
checker↔judge κ≈0.1 artifact. Judges only ever see `instruction + code snippet`
(a ~1-2K-token prompt), never the 200K conversation, so re-judging is cheap and
free of the long-context throttling the candidates hit.

    python rejudge.py logs/retention-v2-final -o rejudged.csv
    # then: join with the deterministic re-score for corrected κ.
"""

from __future__ import annotations

import argparse
import asyncio
import glob
import os

import pandas as pd
from dotenv import load_dotenv

from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    GenerateConfig,
    get_model,
)

from retention.analysis.extract import _model_key
from retention.prompts import INSTRUCTION_TEXT, JUDGE_SYSTEM, judge_prompt
from retention.scorer import _parse_judge_score, build_scored_text

load_dotenv()
from rescore import _per_turn  # reuse the exact per-turn reconstruction

# Same cross-family panel as run.py / run_framing.py.
JUDGES = {
    "judge_1": "openrouter/anthropic/claude-haiku-4.5",
    "judge_2": "azureai/Mistral-Large-3",
    "judge_3": "azureai/grok-4.3",
}

_SEM = asyncio.Semaphore(16)  # concurrent judge calls; retries (below) absorb 429s

# Judges retry rate-limits internally so higher concurrency doesn't drop calls to
# -1; only a terminal failure after retries becomes -1.
_JUDGE_CFG = GenerateConfig(max_retries=5, timeout=120, max_connections=16)


async def _one(judge, meta, instruction, text):
    messages = [ChatMessageSystem(content=JUDGE_SYSTEM),
                ChatMessageUser(content=judge_prompt(instruction, text))]
    async with _SEM:
        try:
            out = await judge.generate(messages)
            return meta, _parse_judge_score(out.completion)
        except BaseException:
            return meta, -1


async def rejudge_dirs(dirs: list[str], out_path: str) -> pd.DataFrame:
    from inspect_ai.log import read_eval_log
    judges = {r: get_model(m, config=_JUDGE_CFG) for r, m in JUDGES.items()}
    tasks = []
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.eval")):
            log = read_eval_log(f)
            model = _model_key(log.eval.model)
            for s in log.samples or []:
                md = s.metadata or {}
                codebase, condition = md.get("codebase"), md.get("condition")
                epoch = getattr(s, "epoch", 1)
                test_turns = md.get("test_turns") or {}
                pt = _per_turn(s)
                for turn_str, decisions in test_turns.items():
                    turn = int(turn_str)
                    completion, ws = pt.get(turn, ("", []))
                    text = build_scored_text(completion, ws)
                    if not text.strip():
                        continue
                    for decision in decisions:
                        instr = INSTRUCTION_TEXT[decision]
                        for role, judge in judges.items():
                            meta = (model, codebase, condition, decision,
                                    turn, epoch, role)
                            tasks.append(_one(judge, meta, instr, text))
    total = len(tasks)
    print(f"dispatching {total} judge calls (3 judges × obs)…", flush=True)
    rows, done, fails = [], 0, 0
    # as_completed yields in finish order -> live progress without losing the
    # semaphore's full concurrency; flush a partial csv every 500 for durability.
    for coro in asyncio.as_completed(tasks):
        (m, c, co, de, t, e, r), sc = await coro
        rows.append(dict(model=m, codebase=c, condition=co, decision=de,
                         turn=t, epoch=e, judge=r, score=sc))
        done += 1
        if sc == -1:
            fails += 1
        if done % 250 == 0 or done == total:
            print(f"  {done}/{total} done ({fails} failed so far)", flush=True)
        if done % 500 == 0:
            pd.DataFrame(rows).to_csv(out_path, index=False)  # durable checkpoint
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir", nargs="+")
    ap.add_argument("-o", "--out", default="rejudged.csv")
    args = ap.parse_args()
    df = asyncio.run(rejudge_dirs(args.log_dir, args.out))
    df.to_csv(args.out, index=False)
    n_ok = (df.score != -1).sum()
    print(f"re-judged {len(df)} calls ({n_ok} parsed, {len(df)-n_ok} unparseable) "
          f"| {df.judge.nunique()} judges | wrote {args.out}")


if __name__ == "__main__":
    main()
