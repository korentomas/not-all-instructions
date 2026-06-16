"""analysis offline analysis over the Inspect `.eval` logs.

Usage:
    python analyze.py logs/retention-v2          # full factorial
    python analyze.py logs/smoke-azure --no-fit  # extract + κ only (skip MCMC)

Produces:
    - a tidy scores CSV (the model's input matrix)
    - per-decision treatment-effect ranking with 94% HDI (the paper result)
    - checker↔judge quadratic-weighted κ (channel triangulation)
    - the qwen-self-judge ablation κ, if a `judge_qwen_self` channel is present
    - the saved posterior trace (`retention_v2.nc`) for figures/diagnostics
    - the framing effect (γ, negation - positive) if framing-arm logs are
      present (`framing_effect.csv` + `retention_v2_framing.nc`)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from retention.analysis import (
    checker_judge_kappa,
    fit_framing_logit,
    fit_ordered_logit,
    framing_effect,
    load_judge_scores,
    load_scores,
    treatment_ranking,
)
from retention.dataset import CONDITIONS, FRAMING_CONDITIONS
from retention.framing import flippable_decisions

# The v1 candidate set (provider-/case-agnostic keys). Passing `--models v1`
# restricts the fit to exactly these, so a stray/archive model living in a
# merged log dir can't leak into the pooled posterior.
V1_MODELS = [
    "qwen3.5-27b",
    "nemotron-3-super-120b-a12b",
    "gemma-4-26b-a4b-it",
    "gemini-3.1-flash-lite",
    "gpt-5.4-nano",
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log_dir", nargs="+",
                    help="one or more Inspect log dirs (e.g. logs/retention-v2 logs/retention-v2-fill)")
    ap.add_argument("--out", default="analysis-out", help="output directory")
    ap.add_argument("--no-fit", action="store_true", help="skip the MCMC fit")
    ap.add_argument("--models", default="all",
                    help="candidate-model allowlist: 'all' (default), 'v1' (the 5 "
                         "v1 models), or a comma-separated list of model keys. "
                         "Stray/archive models outside the set are dropped before the fit.")
    args = ap.parse_args()

    if args.models == "all":
        models = None
    elif args.models == "v1":
        models = V1_MODELS
    else:
        models = [m.strip() for m in args.models.split(",") if m.strip()]

    out = Path(args.out)
    out.mkdir(exist_ok=True)

    det = load_scores(args.log_dir, models=models)
    print(f"deterministic obs: {len(det)} rows, "
          f"{det.decision.nunique()} decisions, {det.model.nunique()} models")
    det.to_csv(out / "scores.csv", index=False)

    judge = load_judge_scores(args.log_dir, models=models)
    if not judge.empty:
        kappa = checker_judge_kappa(det, judge)
        print("\nchecker↔judge quadratic-weighted κ:")
        print(kappa.to_string(index=False))
        kappa.to_csv(out / "kappa.csv", index=False)

    if args.no_fit or det.empty:
        print("\n[--no-fit] skipping MCMC.")
        return

    # The main fit sees ONLY {baseline, treatment}: framing-arm rows would
    # otherwise enter as treatment=0 and contaminate the baseline intercepts.
    main = det[det.condition.isin(CONDITIONS)]
    if not main.empty:
        print("\nfitting hierarchical ordered-logit…")
        idata, _, coords = fit_ordered_logit(main)
        ranking = treatment_ranking(idata, coords)
        print("\nper-decision treatment effect β (ranked, 94% HDI):")
        print(ranking.to_string(index=False))
        ranking.to_csv(out / "treatment_ranking.csv", index=False)
        idata.to_netcdf(out / "retention_v2.nc")
        print(f"\nsaved trace → {out / 'retention_v2.nc'}")

    # framing contrast - only the flippable decisions (the excluded three
    # are worded identically in both arms and carry no framing signal).
    # testing_parametrize is additionally excluded: its corrected checker scores
    # parametrize USAGE (v1-faithful), which is not polarity-symmetric - the
    # positive arm (parametrize) and negation arm (distinct tests) score
    # differently for the SAME behavior, so its γ would be a checker artifact,
    # not a framing effect. (See tests/test_cleanflip.py.)
    FRAMING_EXCLUDE = {"testing_parametrize"}
    framing_decisions = [d for d in flippable_decisions() if d not in FRAMING_EXCLUDE]
    framing = det[
        det.condition.isin(FRAMING_CONDITIONS)
        & det.decision.isin(framing_decisions)
    ]
    if not framing.empty:
        print("\nfitting framing (negation vs positive) ordered-logit…")
        fidata, _, fcoords = fit_framing_logit(framing)
        effect = framing_effect(fidata, fcoords)
        print("\nframing effect γ (negation - positive, log-odds, 94% HDI):")
        print(effect.to_string(index=False))
        effect.to_csv(out / "framing_effect.csv", index=False)
        fidata.to_netcdf(out / "retention_v2_framing.nc")
        print(f"\nsaved framing trace → {out / 'retention_v2_framing.nc'}")


if __name__ == "__main__":
    main()
