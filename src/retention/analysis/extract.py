"""Inspect `.eval` logs → tidy long DataFrames for the ordered-logit + κ.

Each *epoch sample* carries INTEGER ordinal scores (0-3); the epoch reducer's
float means are for reporting, not for the cumulative-link likelihood. So we
iterate over every sample (all epochs) and emit one row per (decision, turn).
Sentinel -1 (unparseable judge / missing) is dropped - never modelled.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

# score keys look like "code_style_broadcasting@20" (det) or
# "judge_1:code_style_broadcasting@20" (panel). Split decision from test turn.


def _split_key(key: str) -> tuple[str, int]:
    name, _, turn = key.rpartition("@")
    return name, int(turn)


def _model_short(model: str) -> str:
    """`openrouter/qwen/qwen3.5-27b` -> `qwen3.5-27b` (provider-agnostic label).

    Display label only - readable, case-preserved. Use `_model_key` for grouping
    so that case- / provider-variants of the SAME model collapse for dedup.
    """
    return model.split("/")[-1]


def _model_key(model: str) -> str:
    """Canonical grouping key for a model, provider- and case-agnostic.

    `azureai/DeepSeek-V3.2` and `openrouter/deepseek/deepseek-v3.2` both map to
    `deepseek-v3.2`, so the SAME (codebase, condition, decision, turn, epoch) cell
    served by two providers dedups to one observation instead of two.

    Only the casing is folded - distinct slugs stay distinct, so genuinely
    different models (`llama-3.3-70b` vs `llama-3.3-70b-instruct`) are preserved.
    """
    return _model_short(model).casefold()


def _iter_logs(log_dir: str | Path | list[str | Path]) -> list[EvalLog]:
    """Accept one dir or several - the heavy candidates are often finished in an
    isolated run (separate log_dir) and merged at analysis time (dedup downstream)."""
    dirs = [log_dir] if isinstance(log_dir, (str, Path)) else list(log_dir)
    logs: list[EvalLog] = []
    for d in dirs:
        for i in list_eval_logs(str(d)):
            logs.append(read_eval_log(i.name))
    return logs


def load_scores(
    log_dir: str | Path | list[str | Path],
    models: list[str] | None = None,
) -> pd.DataFrame:
    """Deterministic-checker channel → long DataFrame (the model's input).

    Columns: model, codebase, condition, decision, turn, epoch, score (int 0-3).

    Harvests every *scored* sample regardless of the log's overall status - a
    run killed/reset mid-sweep leaves valid completed samples in an `error` log,
    and eval_set won't resume them. Duplicate logs (retries) are de-duplicated on
    the natural key (model, codebase, condition, decision, turn, epoch).

    `models` (optional): restrict to an explicit candidate set so stray/archive
    models in a merged log dir don't contaminate the pooled fit. Matched on the
    canonical key (provider-/case-agnostic), so `openrouter/qwen/qwen3.5-27b`,
    `qwen3.5-27b`, and `Qwen3.5-27B` all select the same model. None = all.
    """
    allow = {_model_key(m) for m in models} if models is not None else None
    rows: list[dict] = []
    for log in _iter_logs(log_dir):
        if not log.samples:
            continue
        model = _model_key(log.eval.model)
        if allow is not None and model not in allow:
            continue
        for s in log.samples:
            if not s.scores:
                continue
            det = s.scores.get("deterministic_compliance")
            if det is None:
                continue
            for key, val in det.value.items():
                if val == -1:
                    continue
                decision, turn = _split_key(key)
                rows.append(
                    {
                        "model": model,
                        "codebase": s.metadata.get("codebase", "unknown"),
                        "condition": s.metadata.get("condition", "unknown"),
                        "decision": decision,
                        "turn": turn,
                        "epoch": s.epoch,
                        "score": int(val),
                    }
                )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(
            subset=["model", "codebase", "condition", "decision", "turn", "epoch"]
        ).reset_index(drop=True)
    return df


def load_judge_scores(
    log_dir: str | Path | list[str | Path],
    models: list[str] | None = None,
) -> pd.DataFrame:
    """Judge-panel channel → long DataFrame, aligned to the checker channel for κ.

    Columns: model, codebase, condition, decision, turn, epoch, judge, score.

    `models` (optional): same canonical-key allowlist as `load_scores`, so the κ
    channel stays aligned with a restricted checker channel. None = all.
    """
    allow = {_model_key(m) for m in models} if models is not None else None
    rows: list[dict] = []
    for log in _iter_logs(log_dir):
        if not log.samples:
            continue
        model = _model_key(log.eval.model)
        if allow is not None and model not in allow:
            continue
        for s in log.samples:
            if not s.scores:
                continue
            panel = s.scores.get("judge_panel")
            if panel is None:
                continue
            for key, val in panel.value.items():
                if val == -1:
                    continue
                judge, _, dt = key.partition(":")
                decision, turn = _split_key(dt)
                rows.append(
                    {
                        "model": model,
                        "codebase": s.metadata.get("codebase", "unknown"),
                        "condition": s.metadata.get("condition", "unknown"),
                        "decision": decision,
                        "turn": turn,
                        "epoch": s.epoch,
                        "judge": judge,
                        "score": int(val),
                    }
                )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(
            subset=["model", "codebase", "condition", "decision", "turn", "epoch", "judge"]
        ).reset_index(drop=True)
    return df
