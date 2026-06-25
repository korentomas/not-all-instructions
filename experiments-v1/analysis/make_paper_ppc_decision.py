"""FIG 4: per-decision posterior predictive check.

For each of the 12 decisions: observed mean score (black filled circle) and
posterior-predictive mean (mid-gray filled square) with a 90% predictive
interval horizontal error bar.
"""
import arviz as az
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import paper_style as ps
ps.apply()

idata = az.from_netcdf("retention_model.nc")
obs = idata.observed_data["score"].values
pp = idata.posterior_predictive["score"].values.reshape(-1, obs.shape[0])
didx = idata.constant_data["decision_idx"].values
decisions = list(idata.posterior["decision"].values)

obs_means, pp_means, lo, hi = [], [], [], []
for k in range(len(decisions)):
    mask = didx == k
    obs_means.append(obs[mask].mean())
    draw_means = pp[:, mask].mean(axis=1)        # per-draw mean for decision k
    pp_means.append(draw_means.mean())
    l, h = np.percentile(draw_means, [5, 95])    # 90% predictive interval
    lo.append(l); hi.append(h)

obs_means = np.array(obs_means); pp_means = np.array(pp_means)
lo = np.array(lo); hi = np.array(hi)

order = np.argsort(obs_means)                    # ascending -> bottom is lowest
y = np.arange(len(decisions))
labels = [ps.clean_label(decisions[i]) for i in order]

fig, ax = plt.subplots(figsize=(8, 5))
xerr = [pp_means[order] - lo[order], hi[order] - pp_means[order]]
ax.errorbar(pp_means[order], y, xerr=xerr, fmt="s", color=ps.MED,
            markersize=7, markeredgecolor=ps.MED, zorder=2, **ps.ERRORBAR_KW)
ax.scatter(obs_means[order], y, color="black", s=45, zorder=3)
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel("Mean score")
leg = [Line2D([0], [0], marker="o", color="none", markerfacecolor="black",
              markersize=8, label="Observed"),
       Line2D([0], [0], marker="s", color="none", markerfacecolor=ps.MED,
              markersize=8, label="Predicted (90% PI)")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 1.06),
          ncol=2, frameon=False)
ps.style_axes(ax)
fig.tight_layout()
ps.save(fig, "ppc_per_decision")

inside = int(((obs_means >= lo) & (obs_means <= hi)).sum())
print(f"observed means inside 90% PI: {inside} / {len(decisions)}")
