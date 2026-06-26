"""One-off: recover the handful of judge obs still -1 in rejudged_main.csv.

Only ever a few rows (transient grok-4.3 throttling). Reads just the texts it
needs, hits grok serially (it's fast when healthy), patches the csv. Stage-timed
so it's obvious where time goes.
"""
import asyncio
import glob
import time

import pandas as pd
from dotenv import load_dotenv

from inspect_ai.log import read_eval_log
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
from rejudge import JUDGES
from rescore import _per_turn

CSV = "rejudged_main.csv"
t0 = time.time()


def _log(m):
    print(f"[{time.time()-t0:5.1f}s] {m}", flush=True)


def main():
    df = pd.read_csv(CSV)
    fail = df[df.score == -1].copy()
    _log(f"{len(fail)} rows to recover | judges {dict(fail.judge.value_counts())}")
    need = {(r.model, r.codebase, r.condition, r.epoch, r.turn, r.decision)
            for r in fail.itertuples()}
    texts = {}
    for f in sorted(glob.glob("logs/retention-v2-final/*.eval")):
        if len(texts) == len(need):
            break
        log = read_eval_log(f)
        mk = _model_key(log.eval.model)
        for s in log.samples or []:
            md = s.metadata or {}
            base = (mk, md.get("codebase"), md.get("condition"), getattr(s, "epoch", 1))
            pt = None
            for turn_str, decs in (md.get("test_turns") or {}).items():
                turn = int(turn_str)
                for d in decs:
                    key = base + (turn, d)
                    if key in need and key not in texts:
                        if pt is None:
                            pt = _per_turn(s)
                        comp, ws = pt.get(turn, ("", []))
                        texts[key] = build_scored_text(comp, ws)
    _log(f"resolved {len(texts)}/{len(need)} texts")

    grok = get_model(JUDGES["judge_3"], config=GenerateConfig(max_retries=2, timeout=160))

    async def run():
        rec = 0
        for i, row in fail.iterrows():
            key = (row.model, row.codebase, row.condition, row.epoch, row.turn, row.decision)
            text = texts.get(key)
            sc = -1
            if text:
                msgs = [ChatMessageSystem(content=JUDGE_SYSTEM),
                        ChatMessageUser(content=judge_prompt(INSTRUCTION_TEXT[row.decision], text))]
                try:
                    out = await asyncio.wait_for(grok.generate(msgs), timeout=170)
                    sc = _parse_judge_score(out.completion)
                except BaseException:
                    sc = -1
            df.loc[i, "score"] = sc
            rec += (sc != -1)
            _log(f"  {row.judge} {row.decision}@{row.turn} ({row.codebase}/{row.condition}) -> {sc}")
            df.to_csv(CSV, index=False)
        _log(f"recovered {rec}/{len(fail)} | TOTAL parsed "
             f"{(pd.read_csv(CSV).score != -1).sum()}/{len(df)}")

    asyncio.run(run())


if __name__ == "__main__":
    main()
