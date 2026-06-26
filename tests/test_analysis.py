"""analysis analysis pipeline: extract → κ → ordered-logit.

Validates the port wires up (graph compiles, samples, recovers a planted signal)
on synthetic data, plus real extraction from a smoke `.eval` log when present.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from retention.analysis import (
    checker_judge_kappa,
    fit_framing_logit,
    fit_ordered_logit,
    framing_effect,
    load_scores,
    treatment_ranking,
    variance_components,
)
from retention.analysis.kappa import _quadratic_weighted_kappa

SMOKE_LOG = Path(__file__).resolve().parents[1] / "logs" / "smoke-azure"


def test_qwk_perfect_and_random():
    # identical ratings → κ == 1
    assert _quadratic_weighted_kappa([0, 1, 2, 3], [0, 1, 2, 3]) == pytest.approx(1.0)
    # off-by-one is penalised less than off-by-three (ordinal weighting)
    near = _quadratic_weighted_kappa([0, 1, 2, 3, 0], [1, 2, 3, 2, 1])
    far = _quadratic_weighted_kappa([0, 1, 2, 3, 0], [3, 0, 0, 0, 3])
    assert near > far


def _synthetic(seed: int = 0) -> pd.DataFrame:
    """6 decisions, baseline vs treatment; decisions 0-2 respond to treatment,
    3-5 do not. Enough rows for the sampler to recover the split."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(6):
        responds = d < 3
        for cond in ("baseline", "treatment"):
            base = 1
            lift = 2 if (responds and cond == "treatment") else 0
            for rep in range(25):
                s = int(np.clip(round(rng.normal(base + lift, 0.6)), 0, 3))
                # `rep` -> epoch so each (decision,condition) cell has unique keys
                rows.append({"decision": f"dec_{d}", "condition": cond,
                             "score": s, "epoch": rep})
    return pd.DataFrame(rows)


def test_kappa_table_shape():
    det = _synthetic()
    for col in ("model", "codebase", "turn"):
        det[col] = 0
    judge = det.copy()
    judge["judge"] = "judge_1"
    k = checker_judge_kappa(det, judge)
    # one row per judge + panel_median; identical channels → κ ≈ 1
    assert set(k.rater) == {"judge_1", "panel_median"}
    assert k.kappa.min() == pytest.approx(1.0)


@pytest.mark.slow
def test_ordered_logit_recovers_treatment_split():
    df = _synthetic()
    idata, _, coords = fit_ordered_logit(df, draws=300, tune=300, chains=2)
    ranking = treatment_ranking(idata, coords)
    responders = {f"dec_{i}" for i in range(3)}
    top3 = set(ranking.head(3).decision)
    # the three treatment-responsive decisions should rank highest
    assert top3 == responders


def _synthetic_multimodel(seed: int = 2) -> pd.DataFrame:
    """6 decisions x baseline/treatment x 3 models x 2 codebases. Decisions 0-2
    respond to treatment; model ``m2`` is extra-responsive (higher treatment slope).
    Used to check the M4 per-model / per-codebase terms are added and recovered."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(6):
        responds = d < 3
        for model in ("m0", "m1", "m2"):
            model_lift = 1.0 if model == "m2" else 0.0
            for cb in ("cb0", "cb1"):
                for cond in ("baseline", "treatment"):
                    base = 1
                    lift = (2.5 if responds else 0) + (model_lift if cond == "treatment" else 0)
                    for rep in range(12):
                        s = int(np.clip(round(rng.normal(base + lift, 0.6)), 0, 3))
                        rows.append({"decision": f"dec_{d}", "condition": cond, "model": model,
                                     "codebase": cb, "score": s, "epoch": rep})
    return pd.DataFrame(rows)


@pytest.mark.slow
def test_ordered_logit_adds_model_and_codebase_effects():
    df = _synthetic_multimodel()
    idata, _, coords = fit_ordered_logit(df, draws=500, tune=500, chains=2, interaction=False)
    post = idata.posterior
    # M4 structure: per-model + per-codebase intercepts + per-model treatment slope,
    # added because model/codebase columns have >1 level (interaction=False).
    for v in ("g_model", "t_model", "sigma_model", "sigma_tmodel", "g_codebase", "sigma_codebase"):
        assert v in post, f"missing {v}"
    # m2 (extra-responsive) should have the largest treatment slope
    tm = post["t_model"].mean(("chain", "draw")).to_series()
    assert tm.idxmax() == "m2"
    # the treatment-responsive split is recovered: every responder's beta exceeds
    # every non-responder's (robust to ranking noise at the boundary)
    bmean = post["beta"].mean(("chain", "draw")).to_series()
    responders = bmean[[f"dec_{i}" for i in range(3)]]
    non_responders = bmean[[f"dec_{i}" for i in range(3, 6)]]
    assert responders.mean() > non_responders.mean()
    treatment_ranking(idata, coords)  # smoke: ranking summary runs on the M4 idata


@pytest.mark.slow
def test_ordered_logit_interaction_is_m8_default():
    """M8 (the default) adds an identifiable per-(model, decision) treatment
    interaction variance component; interaction=False recovers additive M4."""
    df = _synthetic_multimodel()
    idata, _, _ = fit_ordered_logit(df, draws=400, tune=400, chains=2)
    for v in ("z_int", "sigma_int"):
        assert v in idata.posterior, f"M8 missing {v}"
    assert "sigma_int" in variance_components(idata)["component"].values
    idata0, _, _ = fit_ordered_logit(df, draws=300, tune=300, chains=2, interaction=False)
    assert "z_int" not in idata0.posterior
    assert "sigma_int" not in idata0.posterior


def _synthetic_framing(seed: int = 1) -> pd.DataFrame:
    """6 decisions across the two framing arms; decisions 0-2 are harmed by the
    negation frame (γ < 0), 3-5 are framing-indifferent."""
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(6):
        harmed = d < 3
        for cond in ("treatment_positive", "treatment_negation"):
            base = 2.2
            drop = 1.6 if (harmed and cond == "treatment_negation") else 0
            for rep in range(25):
                s = int(np.clip(round(rng.normal(base - drop, 0.6)), 0, 3))
                rows.append({"decision": f"dec_{d}", "condition": cond,
                             "score": s, "epoch": rep})
    return pd.DataFrame(rows)


def test_framing_logit_rejects_non_framing_conditions():
    df = _synthetic()  # baseline/treatment - wrong arms for the framing fit
    with pytest.raises(ValueError, match="framing fit expects"):
        fit_framing_logit(df)


@pytest.mark.slow
def test_framing_logit_recovers_negation_penalty():
    df = _synthetic_framing()
    idata, _, coords = fit_framing_logit(df, draws=300, tune=300, chains=2)
    effect = framing_effect(idata, coords)
    pooled = effect[effect.decision == "(pooled μ_γ)"].iloc[0]
    assert pooled["mean"] < 0  # negation hurts on average in the synthetic data
    per_dec = effect[effect.decision != "(pooled μ_γ)"].set_index("decision")["mean"]
    harmed = per_dec[[f"dec_{i}" for i in range(3)]]
    safe = per_dec[[f"dec_{i}" for i in range(3, 6)]]
    assert harmed.max() < safe.min()  # the harmed/indifferent split is recovered


@pytest.mark.skipif(not SMOKE_LOG.exists(), reason="no smoke log present")
def test_load_scores_from_real_log():
    det = load_scores(SMOKE_LOG)
    assert not det.empty
    assert set(["model", "codebase", "condition", "decision", "score"]).issubset(det.columns)
    assert det.score.between(0, 3).all()
