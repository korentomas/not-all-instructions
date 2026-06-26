"""LOO cross-validation, per-decision PPC, and HDI for dependencies_no_new."""

import json
import os
import warnings

import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)

# ── Load data ──────────────────────────────────────────────────────────────────
rows = []
data_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

for phase_dir in ["phase1", "phase3"]:
    data_dir = os.path.join(data_root, phase_dir)
    if not os.path.exists(data_dir):
        continue
    for f in sorted(os.listdir(data_dir)):
        if "v3" not in f or not f.endswith(".json"):
            continue
        with open(os.path.join(data_dir, f)) as fh:
            log = json.load(fh)
        if "turns" not in log:
            continue
        model = log.get("model", log.get("validation_model", {}).get("model", "unknown"))
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
print(f"Loaded {len(df)} observations")

# ── Load fitted model ─────────────────────────────────────────────────────────
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retention_model.nc")
idata = az.from_netcdf(model_path)
print(f"Loaded InferenceData from {model_path}")
print(f"Groups: {list(idata.groups())}")

# ══════════════════════════════════════════════════════════════════════════════
# 1. LOO-CV
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("1. LOO CROSS-VALIDATION")
print("=" * 70)

loo_result = az.loo(idata, pointwise=True)
print(loo_result)

khat = loo_result.pareto_k.values
n_high_khat = (khat > 0.7).sum()
n_total = len(khat)
print(f"\nPareto k-hat summary:")
print(f"  Total observations: {n_total}")
print(f"  k-hat > 0.7 (problematic): {n_high_khat}")
print(f"  k-hat > 0.5 (marginal):    {(khat > 0.5).sum()}")
print(f"  k-hat range: [{khat.min():.3f}, {khat.max():.3f}]")
print(f"  ELPD LOO: {loo_result.elpd_loo:.2f} ± {loo_result.se:.2f}")
print(f"  p_loo (effective parameters): {loo_result.p_loo:.2f}")

# ══════════════════════════════════════════════════════════════════════════════
# 2. Per-decision PPC
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("2. PER-DECISION POSTERIOR PREDICTIVE CHECK")
print("=" * 70)

decisions = sorted(df.decision.unique())
y = df.score.values

# Posterior predictive samples: (chains, draws, obs)
pp_scores = idata.posterior_predictive["score"].values
# Flatten chains: (chains*draws, obs)
pp_flat = pp_scores.reshape(-1, pp_scores.shape[-1])

print(f"\n{'Decision':<35} {'Obs Mean':>10} {'PP Mean':>10} {'PP 5%':>10} {'PP 95%':>10}")
print("-" * 80)

obs_means = []
pp_means_list = []

for dec in decisions:
    mask = (df.decision == dec).values
    obs_mean = y[mask].mean()
    # Mean score across observations for this decision, per posterior draw
    pp_dec = pp_flat[:, mask].mean(axis=1)
    pp_mean = pp_dec.mean()
    pp_lo, pp_hi = np.percentile(pp_dec, [5, 95])
    obs_means.append(obs_mean)
    pp_means_list.append(pp_mean)
    flag = " ***" if (obs_mean < pp_lo or obs_mean > pp_hi) else ""
    print(f"{dec:<35} {obs_mean:>10.3f} {pp_mean:>10.3f} {pp_lo:>10.3f} {pp_hi:>10.3f}{flag}")

# ── Figure: observed vs predicted per decision ────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(decisions))
width = 0.35

# Compute HDI for each decision's PP mean
pp_hdi_lo = []
pp_hdi_hi = []
for dec in decisions:
    mask = (df.decision == dec).values
    pp_dec = pp_flat[:, mask].mean(axis=1)
    lo, hi = np.percentile(pp_dec, [2.5, 97.5])
    pp_hdi_lo.append(lo)
    pp_hdi_hi.append(hi)

pp_hdi_lo = np.array(pp_hdi_lo)
pp_hdi_hi = np.array(pp_hdi_hi)
pp_means_arr = np.array(pp_means_list)
obs_means_arr = np.array(obs_means)

ax.bar(x - width / 2, obs_means_arr, width, label="Observed", color="#e07b53", alpha=0.85,
       edgecolor="white")
ax.bar(x + width / 2, pp_means_arr, width, label="Posterior Predictive", color="#4a90d9", alpha=0.85,
       edgecolor="white")
ax.errorbar(x + width / 2, pp_means_arr,
            yerr=[pp_means_arr - pp_hdi_lo, pp_hdi_hi - pp_means_arr],
            fmt="none", color="black", capsize=3, lw=1.2)

ax.set_xticks(x)
ax.set_xticklabels(decisions, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Mean compliance score (0-3)")
ax.set_title("Posterior Predictive Check: Observed vs Predicted per Decision Type")
ax.legend(loc="upper left")
ax.set_ylim(0, 3.3)

plt.tight_layout()
fig_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures", "ppc_per_decision.png")
os.makedirs(os.path.dirname(fig_path), exist_ok=True)
plt.savefig(fig_path, dpi=150, bbox_inches="tight")
print(f"\nFigure saved to {fig_path}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. 95% HDI for beta[dependencies_no_new]
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("3. 95% HDI FOR beta[dependencies_no_new]")
print("=" * 70)

# Get the decision index
decision_coords = list(idata.posterior.coords["decision"].values)
dep_idx = decision_coords.index("dependencies_no_new")

beta_dep = idata.posterior["beta"].values[:, :, dep_idx].flatten()
hdi_95 = az.hdi(beta_dep, hdi_prob=0.95)
mean_val = beta_dep.mean()
median_val = np.median(beta_dep)

print(f"\nbeta[dependencies_no_new]:")
print(f"  Mean:   {mean_val:.3f}")
print(f"  Median: {median_val:.3f}")
print(f"  SD:     {beta_dep.std():.3f}")
print(f"  95% HDI: [{hdi_95[0]:.3f}, {hdi_95[1]:.3f}]")

if hdi_95[0] > 0:
    print(f"  --> HDI is entirely ABOVE zero: telling helps for this decision")
elif hdi_95[1] < 0:
    print(f"  --> HDI is entirely BELOW zero: telling HURTS for this decision")
else:
    print(f"  --> HDI CROSSES zero: effect is uncertain for this decision")

print(f"  P(beta > 0): {(beta_dep > 0).mean():.3f}")
print(f"  P(beta < 0): {(beta_dep < 0).mean():.3f}")

print("\nDone.")
