"""FIG 1: posterior predictive check (two panels).

LEFT  : observed vs posterior-predictive proportions over the 0-3 ordinal
        score, error bars on the predictive bars.
RIGHT : posterior-predictive mean-score distributions for baseline vs
        treatment, with observed-mean vertical lines.
"""
import arviz as az
import numpy as np
import matplotlib.pyplot as plt

import paper_style as ps
ps.apply()

idata = az.from_netcdf("retention_model.nc")

obs = idata.observed_data["score"].values            # (244,)
pp = idata.posterior_predictive["score"].values      # (chain, draw, 244)
treat = idata.constant_data["treatment"].values      # (244,) 0/1
pp_flat = pp.reshape(-1, pp.shape[-1])               # (n_draws, 244)

levels = np.array([0, 1, 2, 3])

# -- LEFT: proportion at each ordinal level ---------------------------------
obs_prop = np.array([(obs == k).mean() for k in levels])
# predicted proportion per draw, then mean and sd across draws
pred_prop_draws = np.stack(
    [(pp_flat == k).mean(axis=1) for k in levels], axis=1)   # (n_draws, 4)
pred_prop = pred_prop_draws.mean(axis=0)
pred_prop_sd = pred_prop_draws.std(axis=0)

# -- RIGHT: posterior-predictive mean score, baseline vs treatment ----------
base_mask = treat == 0
treat_mask = treat == 1
pp_mean_base = pp_flat[:, base_mask].mean(axis=1)
pp_mean_treat = pp_flat[:, treat_mask].mean(axis=1)
obs_mean_base = obs[base_mask].mean()
obs_mean_treat = obs[treat_mask].mean()

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9, 3.4))

# ---- LEFT panel ----
w = 0.4
x = levels.astype(float)
axL.bar(x - w / 2, obs_prop, width=w, color=ps.DARK, label="Observed",
        edgecolor="white")
axL.bar(x + w / 2, pred_prop, width=w, color=ps.LIGHT, label="Predicted",
        edgecolor="white", yerr=pred_prop_sd, error_kw=ps.ERRORBAR_KW)
axL.set_xlabel("Score")
axL.set_ylabel("Proportion")
axL.set_xticks(levels)
axL.legend(frameon=False, loc="upper left")
ps.style_axes(axL)

# ---- RIGHT panel ----
bins = np.linspace(
    min(pp_mean_base.min(), pp_mean_treat.min()),
    max(pp_mean_base.max(), pp_mean_treat.max()), 40)
axR.hist(pp_mean_base, bins=bins, density=True, color=ps.LIGHT, alpha=0.85)
axR.hist(pp_mean_treat, bins=bins, density=True, color=ps.DARK, alpha=0.6)
axR.axvline(obs_mean_base, color=ps.LIGHT, lw=2.0, ls="--",
            label=f"Baseline ({obs_mean_base:.2f})")
axR.axvline(obs_mean_treat, color=ps.DARK, lw=2.0, ls="-",
            label=f"Treatment ({obs_mean_treat:.2f})")
axR.set_xlabel("Mean score")
axR.set_ylabel("Density")
axR.legend(frameon=False, loc="upper left")
ps.style_axes(axR)

fig.tight_layout()
ps.save(fig, "posterior_predictive_check")

print(f"baseline observed mean : {obs_mean_base:.3f}")
print(f"treatment observed mean: {obs_mean_treat:.3f}")
print("obs proportions :", np.round(obs_prop, 3))
print("pred proportions:", np.round(pred_prop, 3))
