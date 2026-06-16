"""Checker↔judge agreement (κ) - triangulation of the two scoring channels.

The deterministic checker is the oracle; the LLM judge panel is the scalable
proxy. Quadratic-weighted Cohen's κ on the shared 0-3 ordinal scale measures how
far the proxy can be trusted (weighted, because off-by-one on an ordinal scale is
a near-miss, not a full disagreement). Computed per judge and for the panel
median, over the (decision, turn, sample) cells where both channels scored.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

_KEYS = ["model", "codebase", "condition", "decision", "turn", "epoch"]


def _quadratic_weighted_kappa(a: np.ndarray, b: np.ndarray, n_cls: int = 4) -> float:
    """Cohen's κ with quadratic weights on an ordinal 0..n_cls-1 scale."""
    a = np.asarray(a, dtype=int)
    b = np.asarray(b, dtype=int)
    if len(a) == 0:
        return float("nan")
    obs = np.zeros((n_cls, n_cls), dtype=float)
    for x, y in zip(a, b):
        obs[x, y] += 1
    w = np.zeros((n_cls, n_cls), dtype=float)
    for i in range(n_cls):
        for j in range(n_cls):
            w[i, j] = (i - j) ** 2 / (n_cls - 1) ** 2
    act = obs.sum(axis=1)
    pred = obs.sum(axis=0)
    exp = np.outer(act, pred) / obs.sum()
    denom = (w * exp).sum()
    return 1.0 - (w * obs).sum() / denom if denom > 0 else float("nan")


def checker_judge_kappa(
    det_df: pd.DataFrame, judge_df: pd.DataFrame
) -> pd.DataFrame:
    """Per-judge + panel-median quadratic-weighted κ vs the checker oracle.

    Returns rows: rater, n (paired cells), kappa.
    """
    det = det_df.rename(columns={"score": "checker"})[_KEYS + ["checker"]]
    rows: list[dict] = []

    for judge, g in judge_df.groupby("judge"):
        merged = g.merge(det, on=_KEYS, how="inner")
        rows.append(
            {
                "rater": judge,
                "n": len(merged),
                "kappa": _quadratic_weighted_kappa(
                    merged["checker"], merged["score"]
                ),
            }
        )

    # Panel median (round half-up to an int on the ordinal scale) vs checker.
    panel = (
        judge_df.groupby(_KEYS)["score"]
        .median()
        .apply(lambda v: int(np.floor(v + 0.5)))
        .rename("panel")
        .reset_index()
    )
    merged = panel.merge(det, on=_KEYS, how="inner")
    rows.append(
        {
            "rater": "panel_median",
            "n": len(merged),
            "kappa": _quadratic_weighted_kappa(merged["checker"], merged["panel"]),
        }
    )
    return pd.DataFrame(rows)
