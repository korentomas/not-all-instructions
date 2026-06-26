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
    interaction: bool = True,
    draws: int = 2000,
    tune: int = 2000,
    chains: int = 4,
    target_accept: float = 0.99,
):
    """Fit the hierarchical ordered-logit (M8). Returns (idata, model, coords).

    `df` needs columns: decision, condition (baseline/treatment), score (0-3).

    When ``model`` and/or ``codebase`` columns are present with more than one level,
    the model adds per-model and per-codebase baseline intercepts plus a per-model
    treatment slope (the additive M4 spec), and -- when ``interaction=True`` and a
    ``model`` column is present -- an identifiable per-(model, decision) treatment
    interaction variance component ``z_{m,d} ~ Normal(0, sigma_int)`` (the M8 spec,
    see docs/findings-v6-interaction.md). The clean model comparison shows this
    interaction is the dominant structure: it improves LOO by ~59 ELPD over the
    additive M4, while additive per-model main effects add nothing over the
    per-decision M0. ``interaction=False`` recovers the additive M4. With a single
    (or absent) model/codebase level the model gracefully reduces to the
    per-decision spec (M0).

    Caveat: variance components (sigma_*) are prior-influenced because there are few
    groups (few codebases/models) and are pool-sensitive; the per-decision
    treatment-effect *rankings* and the interaction conclusion are robust.
    """
    import pymc as pm
    import pytensor.tensor as pt

    rng = np.random.default_rng(RANDOM_SEED)

    decisions = sorted(df.decision.unique())
    decision_idx = pd.Categorical(df.decision, categories=decisions).codes
    treatment = (df.condition == "treatment").astype(int).values
    y = df.score.values.astype(int)

    has_model = "model" in df.columns and df.model.nunique() > 1
    has_codebase = "codebase" in df.columns and df.codebase.nunique() > 1

    coords = {"decision": decisions, "obs": np.arange(len(df))}
    if has_model:
        models = sorted(df.model.unique())
        coords["model"] = models
        model_idx = pd.Categorical(df.model, categories=models).codes
    if has_codebase:
        codebases = sorted(df.codebase.unique())
        coords["codebase"] = codebases
        codebase_idx = pd.Categorical(df.codebase, categories=codebases).codes

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

        # M4: per-model baseline intercept + per-model treatment slope.
        if has_model:
            model_data = pm.Data("model_idx", model_idx, dims="obs")
            sigma_model = pm.Exponential("sigma_model", lam=1)
            g_model = pm.Deterministic(
                "g_model", sigma_model * pm.Normal("g_model_raw", 0, 1, dims="model"),
                dims="model",
            )
            sigma_tmodel = pm.Exponential("sigma_tmodel", lam=1)
            t_model = pm.Deterministic(
                "t_model", sigma_tmodel * pm.Normal("t_model_raw", 0, 1, dims="model"),
                dims="model",
            )
            eta = eta + g_model[model_data] + treatment_data * t_model[model_data]

        # M4: per-codebase baseline intercept.
        if has_codebase:
            codebase_data = pm.Data("codebase_idx", codebase_idx, dims="obs")
            sigma_codebase = pm.Exponential("sigma_codebase", lam=1)
            g_codebase = pm.Deterministic(
                "g_codebase",
                sigma_codebase * pm.Normal("g_codebase_raw", 0, 1, dims="codebase"),
                dims="codebase",
            )
            eta = eta + g_codebase[codebase_data]

        # M8: per-(model, decision) treatment interaction. Identifiable variance
        # component (Normal(0, sigma_int)) rather than a rank-1 factor (which is
        # unidentified up to sign/scale). Dominant term: LOO ~59 better than M4.
        if interaction and has_model:
            sigma_int = pm.Exponential("sigma_int", lam=1)
            z_int = pm.Deterministic(
                "z_int",
                sigma_int * pm.Normal("z_int_raw", 0, 1, dims=("model", "decision")),
                dims=("model", "decision"),
            )
            eta = eta + treatment_data * z_int[model_data, decision_data]

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


def variance_components(idata) -> pd.DataFrame:
    """Group-level standard deviations (heterogeneity) with 94% HDI.

    Always includes sigma_beta (treatment-effect spread across instructions) and
    sigma_alpha (baseline spread). When the M4 terms are present, also sigma_model /
    sigma_tmodel (model identity & responsiveness) and sigma_codebase. When the M8
    interaction is present, sigma_int (model x instruction interaction) -- the
    dominant term once admitted. Caveat: with few groups these are prior-influenced.
    """
    import arviz as az

    names = [v for v in ("sigma_int", "sigma_beta", "sigma_alpha", "sigma_model",
                         "sigma_tmodel", "sigma_codebase")
             if v in idata.posterior]
    summ = az.summary(idata, var_names=names, hdi_prob=0.94)[["mean", "hdi_3%", "hdi_97%"]]
    return summ.reset_index().rename(columns={"index": "component"})


def model_treatment_slopes(idata, coords) -> pd.DataFrame:
    """Per-model treatment slope t_model (how much each model retains when told),
    94% HDI, ranked. `effective` = HDI excludes 0. Empty when the fit had a single
    model level (M0 path)."""
    import arviz as az

    if "t_model" not in idata.posterior:
        return pd.DataFrame()
    summ = az.summary(idata, var_names=["t_model"], hdi_prob=0.94).reset_index(drop=True)
    summ.insert(0, "model", coords["model"])
    summ["effective"] = (summ["hdi_3%"] > 0) | (summ["hdi_97%"] < 0)
    return summ.sort_values("mean", ascending=False).reset_index(drop=True)
