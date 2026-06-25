"""FIG 3: reinforcement policy.

Per-decision reinforcement gain = dP(score>=2 | told) - P(score>=2 | not told),
sorted by gain descending, with 94% HDI. Categories: reinforce (dark),
never reinforce (dark + hatch), uncertain (light).
"""
import arviz as az
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy.special import expit

import paper_style as ps
ps.apply()

idata = az.from_netcdf("retention_model.nc")
post = idata.posterior
decisions = list(post["beta"].coords[post["beta"].dims[-1]].values)
a = post["alpha"].values.reshape(-1, len(decisions))
b = post["beta"].values.reshape(-1, len(decisions))
c = post["cutpoints"].values.reshape(-1, 3)
c2 = c[:, 1:2]
p_t = 1 - expit(c2 - (a + b))
p_b = 1 - expit(c2 - a)
gain = p_t - p_b
gmean = gain.mean(0)
ghdi = np.percentile(gain, [3, 97], axis=0)
order = np.argsort(gmean)[::-1]              # highest first -> bottom

colors, hatches = [], []
for i in order:
    if ghdi[0, i] > 0:
        colors.append(ps.DARK); hatches.append("")
    elif ghdi[1, i] < 0:
        colors.append(ps.DARK); hatches.append("///")
    else:
        colors.append(ps.LIGHT); hatches.append("")

labels = [ps.clean_label(decisions[i]) for i in order]
fig, ax = plt.subplots(figsize=(6.4, 4.0))
y = np.arange(len(decisions))
xerr = [gmean[order] - ghdi[0, order], ghdi[1, order] - gmean[order]]
bars = ax.barh(y, gmean[order], xerr=xerr, color=colors, alpha=0.9,
               edgecolor="white", height=0.7, error_kw=ps.ERRORBAR_KW)
for bar, h in zip(bars, hatches):
    if h:
        bar.set_hatch(h)
ax.axvline(0, color="black", lw=ps.AXES_LINEWIDTH, ls="--")
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel(r"$\Delta P(\mathrm{score} \geq 2)$")
leg = [Patch(facecolor=ps.DARK, edgecolor="white", label="Reinforce"),
       Patch(facecolor=ps.DARK, edgecolor="white", hatch="///",
             label="Never reinforce"),
       Patch(facecolor=ps.LIGHT, edgecolor="white", label="Uncertain")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 1.14),
          ncol=3, frameon=False)
ps.style_axes(ax)
fig.tight_layout()
fig.subplots_adjust(top=0.90)
ps.save(fig, "reinforcement_policy")

idx = {d: i for i, d in enumerate(decisions)}
print("gains:")
for d in ["testing_parametrize", "dependencies_module_constants",
          "architecture_standalone", "dependencies_no_new"]:
    print(f"  {d:32s} {gmean[idx[d]]:+.2f}")
