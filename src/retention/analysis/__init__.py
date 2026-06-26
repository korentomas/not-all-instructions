"""Offline analysis over Inspect `.eval` logs .

The paper's headline result is a **Bayesian hierarchical ordered-logistic**
(cumulative-link) model with per-decision baseline (α) and treatment (β) effects
 - NOT BKT, NOT the decay-curve fit. This package ports that model (faithful to
`experiments/analysis/bayesian_analysis.ipynb`) so it runs on the v2 Inspect
logs, plus checker↔judge agreement (κ) and the qwen-self-judge ablation.
"""

from retention.analysis.extract import load_scores, load_judge_scores
from retention.analysis.kappa import checker_judge_kappa
from retention.analysis.model import (
    fit_framing_logit,
    fit_ordered_logit,
    framing_effect,
    model_treatment_slopes,
    treatment_ranking,
    variance_components,
)

__all__ = [
    "load_scores",
    "load_judge_scores",
    "checker_judge_kappa",
    "fit_framing_logit",
    "fit_ordered_logit",
    "framing_effect",
    "treatment_ranking",
    "variance_components",
    "model_treatment_slopes",
]
