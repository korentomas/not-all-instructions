"""Bayesian hierarchical ordered-logistic model - the paper's headline result.

Faithful port of `experiments/analysis/bayesian_analysis.ipynb` (v1). Cumulative
-link model on the 0-3 ordinal compliance score with non-centered hierarchical
per-decision baseline (α) and treatment (β) effects, offset-parameterized
cutpoints. The scientific question: does the treatment effect β vary across
decision types (heterogeneous retention a BKT reinforcer could exploit)?
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Same seed string as v1 so priors/sampling are comparable across versions.
RANDOM_SEED = sum(map(ord, "context-rot-retention"))


def fit_ordered_logit(
    df: pd.DataFrame,
    *,
    draws: int = 2000,
    tune: int = 2000,
    chains: int = 4,
    target_accept: float = 0.95,
):
    """Fit the hierarchical ordered-logit. Returns (idata, model, coords).

    `df` needs columns: decision, condition (baseline/treatment), score (0-3).
    Other columns (model, codebase, turn, epoch) are pooled replicates.
    """
    import pymc as pm
    import pytensor.tensor as pt

    rng = np.random.default_rng(RANDOM_SEED)

    decisions = sorted(df.decision.unique())
    decision_idx = pd.Categorical(df.decision, categories=decisions).codes
    treatment = (df.condition == "treatment").astype(int).values
    y = df.score.values.astype(int)

    coords = {"decision": decisions, "obs": np.arange(len(df))}

    with pm.Model(coords=coords) as retention_model:
        decision_data = pm.Data("decision_idx", decision_idx, dims="obs")
        treatment_data = pm.Data("treatment", treatment, dims="obs")

        # Cutpoints (offset parameterization): c1 < c2 < c3 by construction.
        c1 = pm.Normal("c1", mu=0, sigma=1.5)
        dc = pm.Exponential("dc", lam=1, shape=2)
        cutpoints = pm.Deterministic(
            "cutpoints", pt.stack([c1, c1 + dc[0], c1 + dc[0] + dc[1]])
        )

        # Per-decision baseline intercept (non-centered).
        mu_alpha = pm.Normal("mu_alpha", mu=0, sigma=1.5)
        sigma_alpha = pm.Exponential("sigma_alpha", lam=1)
        alpha_raw = pm.Normal("alpha_raw", mu=0, sigma=1, dims="decision")
        alpha = pm.Deterministic(
            "alpha", mu_alpha + sigma_alpha * alpha_raw, dims="decision"
        )

        # Per-decision treatment effect (non-centered), centered at 0.
        mu_beta = pm.Normal("mu_beta", mu=0, sigma=1)
        sigma_beta = pm.Exponential("sigma_beta", lam=1)
        beta_raw = pm.Normal("beta_raw", mu=0, sigma=1, dims="decision")
        beta = pm.Deterministic(
            "beta", mu_beta + sigma_beta * beta_raw, dims="decision"
        )

        eta = alpha[decision_data] + beta[decision_data] * treatment_data
        pm.OrderedLogistic(
            "score", eta=eta, cutpoints=cutpoints, observed=y, dims="obs"
        )

        idata = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            target_accept=target_accept,
            random_seed=rng,
            progressbar=False,
        )

    return idata, retention_model, coords


def fit_framing_logit(
    df: pd.DataFrame,
    *,
    draws: int = 2000,
    tune: int = 2000,
    chains: int = 4,
    target_accept: float = 0.95,
):
    """framing contrast - same cumulative-link skeleton, different indicator.

    Both arms are treatment; what varies is the polarity of the instruction
    clause. η = α_d + γ_d, negation, with γ hierarchical across decisions:
    μ_γ is the pooled framing effect (negation minus positive, log-odds), γ_d
    the per-decision effect. Returns (idata, model, coords).

    `df` needs columns: decision, condition ∈ {treatment_positive,
    treatment_negation}, score (0-3). Callers must pre-filter to the flippable
    decisions (the excluded three are worded identically in both arms).
    """
    conditions = set(df.condition.unique())
    expected = {"treatment_positive", "treatment_negation"}
    if not conditions <= expected:
        raise ValueError(f"framing fit expects conditions {expected}, got {conditions}")

    import pymc as pm
    import pytensor.tensor as pt

    rng = np.random.default_rng(RANDOM_SEED)

    decisions = sorted(df.decision.unique())
    decision_idx = pd.Categorical(df.decision, categories=decisions).codes
    negation = (df.condition == "treatment_negation").astype(int).values
    y = df.score.values.astype(int)

    coords = {"decision": decisions, "obs": np.arange(len(df))}

    with pm.Model(coords=coords) as framing_model:
        decision_data = pm.Data("decision_idx", decision_idx, dims="obs")
        negation_data = pm.Data("negation", negation, dims="obs")

        c1 = pm.Normal("c1", mu=0, sigma=1.5)
        dc = pm.Exponential("dc", lam=1, shape=2)
        cutpoints = pm.Deterministic(
            "cutpoints", pt.stack([c1, c1 + dc[0], c1 + dc[0] + dc[1]])
        )

        mu_alpha = pm.Normal("mu_alpha", mu=0, sigma=1.5)
        sigma_alpha = pm.Exponential("sigma_alpha", lam=1)
        alpha_raw = pm.Normal("alpha_raw", mu=0, sigma=1, dims="decision")
        alpha = pm.Deterministic(
            "alpha", mu_alpha + sigma_alpha * alpha_raw, dims="decision"
        )

        # Per-decision framing effect (non-centered), centered at 0 - no prior
        # assumption that negation helps or hurts.
        mu_gamma = pm.Normal("mu_gamma", mu=0, sigma=1)
        sigma_gamma = pm.Exponential("sigma_gamma", lam=1)
        gamma_raw = pm.Normal("gamma_raw", mu=0, sigma=1, dims="decision")
        gamma = pm.Deterministic(
            "gamma", mu_gamma + sigma_gamma * gamma_raw, dims="decision"
        )

        eta = alpha[decision_data] + gamma[decision_data] * negation_data
        pm.OrderedLogistic(
            "score", eta=eta, cutpoints=cutpoints, observed=y, dims="obs"
        )

        idata = pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            target_accept=target_accept,
            random_seed=rng,
            progressbar=False,
        )

    return idata, framing_model, coords


def framing_effect(idata, coords) -> pd.DataFrame:
    """Per-decision framing effect γ (negation - positive, log-odds) with 94%
    HDI, plus the pooled μ_γ as the first row. `effective` = HDI excludes 0."""
    import arviz as az

    pooled = az.summary(idata, var_names=["mu_gamma"], hdi_prob=0.94).reset_index(drop=True)
    pooled.insert(0, "decision", "(pooled μ_γ)")
    per_dec = az.summary(idata, var_names=["gamma"], hdi_prob=0.94).reset_index(drop=True)
    per_dec.insert(0, "decision", coords["decision"])
    per_dec = per_dec.sort_values("mean").reset_index(drop=True)

    summ = pd.concat([pooled, per_dec], ignore_index=True)
    summ["effective"] = (summ["hdi_3%"] > 0) | (summ["hdi_97%"] < 0)
    return summ


def treatment_ranking(idata, coords) -> pd.DataFrame:
    """Per-decision treatment effect β with 94% HDI, ranked - the reinforcement
    ranking a BKT system would exploit. `effective` = HDI excludes 0."""
    import arviz as az

    summ = az.summary(idata, var_names=["beta"], hdi_prob=0.94)
    summ = summ.reset_index(drop=True)
    summ.insert(0, "decision", coords["decision"])
    lo, hi = summ["hdi_3%"], summ["hdi_97%"]
    summ["effective"] = (lo > 0) | (hi < 0)
    return summ.sort_values("mean", ascending=False).reset_index(drop=True)
