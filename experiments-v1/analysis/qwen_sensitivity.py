"""
Qwen-Only Sensitivity Analysis
===============================
Addresses reviewer concern: "baseline data comes only from Qwen — is the treatment
effect confounded with model identity?"

This script fits the same ordered logistic model as the main analysis but uses ONLY
Qwen v3 data (both baseline and treatment). If treatment effects are similar to the
full-model analysis, the confound is ruled out.
"""

import json
import os
import warnings

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt

warnings.filterwarnings("ignore", category=FutureWarning)

RANDOM_SEED = sum(map(ord, "qwen-sensitivity"))
rng = np.random.default_rng(RANDOM_SEED)

ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(os.path.dirname(ANALYSIS_DIR), "data")

# ── 1. Load only Qwen v3 data from phase1 ──────────────────────────────────
rows = []
phase1_dir = os.path.join(DATA_ROOT, "phase1")
for f in sorted(os.listdir(phase1_dir)):
    if "v3" not in f or not f.endswith(".json"):
        continue
    with open(os.path.join(phase1_dir, f)) as fh:
        log = json.load(fh)
    if "turns" not in log:
        continue
    model = log.get("model", "unknown")
    # Only keep Qwen
    if "qwen" not in model.lower():
        continue
    for t in log["turns"]:
        if t["turn"] < 20:
            continue
        for k, v in t["compliance"].items():
            if k.startswith("decision:"):
                rows.append({
                    "model": model.split("/")[-1],
                    "condition": log.get("condition", "treatment"),
                    "codebase": log.get("codebase"),
                    "turn": t["turn"],
                    "decision": k.split(":")[1],
                    "score": v["score"],
                })

df = pd.DataFrame(rows)
print("=" * 70)
print("QWEN-ONLY SENSITIVITY ANALYSIS")
print("=" * 70)
print(f"\nLoaded {len(df)} observations (Qwen only)")
print(f"Models: {sorted(df.model.unique())}")
print(f"Conditions: {sorted(df.condition.unique())}")
print(f"Codebases: {sorted(df.codebase.unique())}")
print(f"Decisions: {sorted(df.decision.unique())}")
print(f"\nScore distribution:\n{df.score.value_counts().sort_index()}")
print(f"\nBy condition:")
print(df.groupby("condition").size())

# ── 2. Data preparation ────────────────────────────────────────────────────
decisions = sorted(df.decision.unique())
decision_idx = pd.Categorical(df.decision, categories=decisions).codes
treatment = (df.condition == "treatment").astype(int).values
y = df.score.values

coords = {
    "decision": decisions,
    "obs": np.arange(len(df)),
}

print(f"\nTreatment: {treatment.sum()} treated, {(1-treatment).sum()} baseline")

# ── 3. Model specification (identical to main analysis) ─────────────────────
with pm.Model(coords=coords) as qwen_model:
    decision_data = pm.Data("decision_idx", decision_idx, dims="obs")
    treatment_data = pm.Data("treatment", treatment, dims="obs")

    # Cutpoints (offset parameterization)
    c1 = pm.Normal("c1", mu=0, sigma=1.5)
    dc = pm.Exponential("dc", lam=1, shape=2)
    cutpoints = pm.Deterministic("cutpoints", pt.stack([c1, c1 + dc[0], c1 + dc[0] + dc[1]]))

    # Baseline intercepts per decision (non-centered)
    mu_alpha = pm.Normal("mu_alpha", mu=0, sigma=1.5)
    sigma_alpha = pm.Exponential("sigma_alpha", lam=1)
    alpha_raw = pm.Normal("alpha_raw", mu=0, sigma=1, dims="decision")
    alpha = pm.Deterministic("alpha", mu_alpha + sigma_alpha * alpha_raw, dims="decision")

    # Treatment effects per decision (non-centered)
    mu_beta = pm.Normal("mu_beta", mu=0, sigma=1)
    sigma_beta = pm.Exponential("sigma_beta", lam=1)
    beta_raw = pm.Normal("beta_raw", mu=0, sigma=1, dims="decision")
    beta = pm.Deterministic("beta", mu_beta + sigma_beta * beta_raw, dims="decision")

    # Linear predictor
    eta = alpha[decision_data] + beta[decision_data] * treatment_data

    # Likelihood
    pm.OrderedLogistic("score", eta=eta, cutpoints=cutpoints, observed=y, dims="obs")

# ── 4. Sample with nutpie ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SAMPLING")
print("=" * 70)

with qwen_model:
    idata = pm.sample(nuts_sampler="nutpie", random_seed=rng)

# ── 5. Save results ────────────────────────────────────────────────────────
output_path = os.path.join(ANALYSIS_DIR, "qwen_sensitivity.nc")
idata.to_netcdf(output_path)
print(f"\nSaved to {output_path}")

# ── 6. Diagnostics ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("CONVERGENCE DIAGNOSTICS")
print("=" * 70)

n_divs = int(idata.sample_stats["diverging"].sum().values)
n_draws = idata.sample_stats["diverging"].size
print(f"Divergences: {n_divs} / {n_draws} ({n_divs/n_draws*100:.1f}%)")

summary = az.summary(idata, var_names=["mu_alpha", "mu_beta", "sigma_alpha", "sigma_beta",
                                         "cutpoints", "alpha", "beta"])
rhat_max = summary["r_hat"].max()
ess_min = summary["ess_bulk"].min()
print(f"Worst R-hat: {rhat_max:.4f} (target: < 1.01)")
print(f"Lowest ESS:  {ess_min:.0f} (target: > 400)")
print(f"All R-hat < 1.01: {(summary['r_hat'] < 1.01).all()}")
print(f"All ESS > 400:    {(summary['ess_bulk'] > 400).all()}")

# ── 6b. Beta summary table ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("QWEN-ONLY TREATMENT EFFECTS (beta)")
print("=" * 70)

beta_summary = az.summary(idata, var_names=["beta"], hdi_prob=0.94)
beta_summary = beta_summary.sort_values("mean")
print(beta_summary[["mean", "sd", "hdi_3%", "hdi_97%", "r_hat", "ess_bulk"]].round(3).to_string())

# ── 7. Comparison with full model ──────────────────────────────────────────
print("\n" + "=" * 70)
print("COMPARISON: FULL MODEL vs QWEN-ONLY")
print("=" * 70)

full_model_path = os.path.join(ANALYSIS_DIR, "retention_model.nc")
if os.path.exists(full_model_path):
    idata_full = az.from_netcdf(full_model_path)
    full_beta = az.summary(idata_full, var_names=["beta"], hdi_prob=0.94)
    qwen_beta = az.summary(idata, var_names=["beta"], hdi_prob=0.94)

    # Build comparison table
    comparison_rows = []
    for dec in decisions:
        label = f"beta[{dec}]"
        full_row = full_beta.loc[label] if label in full_beta.index else None
        qwen_row = qwen_beta.loc[label] if label in qwen_beta.index else None

        if full_row is not None and qwen_row is not None:
            comparison_rows.append({
                "decision": dec,
                "full_mean": full_row["mean"],
                "full_hdi_3%": full_row["hdi_3%"],
                "full_hdi_97%": full_row["hdi_97%"],
                "qwen_mean": qwen_row["mean"],
                "qwen_hdi_3%": qwen_row["hdi_3%"],
                "qwen_hdi_97%": qwen_row["hdi_97%"],
                "delta": qwen_row["mean"] - full_row["mean"],
            })

    comp_df = pd.DataFrame(comparison_rows).set_index("decision")
    comp_df = comp_df.sort_values("full_mean")

    print(f"\n{'Decision':<30} {'Full β':>8} {'Full 94% HDI':>20} {'Qwen β':>8} {'Qwen 94% HDI':>20} {'Δ':>8}")
    print("-" * 100)
    for _, row in comp_df.iterrows():
        print(f"{row.name:<30} {row['full_mean']:>8.2f} [{row['full_hdi_3%']:>7.2f}, {row['full_hdi_97%']:>7.2f}] "
              f"{row['qwen_mean']:>8.2f} [{row['qwen_hdi_3%']:>7.2f}, {row['qwen_hdi_97%']:>7.2f}] {row['delta']:>8.2f}")

    # Overall summary
    print(f"\nMean absolute difference (Δ): {comp_df['delta'].abs().mean():.3f}")
    print(f"Max absolute difference:       {comp_df['delta'].abs().max():.3f}")
    print(f"Correlation (full vs qwen):    {comp_df['full_mean'].corr(comp_df['qwen_mean']):.3f}")

    # Check sign agreement
    sign_agree = ((comp_df['full_mean'] > 0) == (comp_df['qwen_mean'] > 0)).sum()
    print(f"Sign agreement:                {sign_agree}/{len(comp_df)} decisions")

    # Hyperparameter comparison
    print("\n" + "-" * 70)
    print("HYPERPARAMETER COMPARISON")
    print("-" * 70)
    for var in ["mu_alpha", "mu_beta", "sigma_alpha", "sigma_beta"]:
        full_s = az.summary(idata_full, var_names=[var], hdi_prob=0.94)
        qwen_s = az.summary(idata, var_names=[var], hdi_prob=0.94)
        print(f"{var:<15} Full: {full_s['mean'].values[0]:>7.3f} [{full_s['hdi_3%'].values[0]:>7.3f}, {full_s['hdi_97%'].values[0]:>7.3f}]"
              f"   Qwen: {qwen_s['mean'].values[0]:>7.3f} [{qwen_s['hdi_3%'].values[0]:>7.3f}, {qwen_s['hdi_97%'].values[0]:>7.3f}]")
else:
    print(f"Full model not found at {full_model_path} — skipping comparison.")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
if os.path.exists(full_model_path):
    corr = comp_df['full_mean'].corr(comp_df['qwen_mean'])
    mad = comp_df['delta'].abs().mean()
    if corr > 0.8 and mad < 1.0:
        print("Treatment effects are CONSISTENT between full and Qwen-only models.")
        print("The baseline-only-from-Qwen confound does NOT explain the treatment effects.")
    elif corr > 0.5:
        print("Treatment effects show MODERATE consistency — some differences worth investigating.")
    else:
        print("Treatment effects DIFFER substantially — the confound concern may be valid.")
