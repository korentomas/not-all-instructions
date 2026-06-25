import arviz as az, numpy as np, matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch
from scipy.special import expit

# Match the original paper figures (fig 1 + fig 4): STIX serif, not DejaVu Sans
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "STIXGeneral"

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

DARK, LIGHT = "#4d4d4d", "#cccccc"
colors, hatches = [], []
for i in order:
    if ghdi[0, i] > 0:   colors.append(DARK);  hatches.append("")
    elif ghdi[1, i] < 0: colors.append(DARK); hatches.append("///")
    else:                colors.append(LIGHT); hatches.append("")

labels = [decisions[i].replace("_", " ") for i in order]
fig, ax = plt.subplots(figsize=(8, 5))
y = np.arange(len(decisions))
xerr = [gmean[order] - ghdi[0, order], ghdi[1, order] - gmean[order]]
bars = ax.barh(y, gmean[order], xerr=xerr, color=colors, alpha=0.9,
               capsize=3, edgecolor="white", height=0.7,
               error_kw=dict(ecolor="black", elinewidth=1.1, capthick=1.1))
for bar, h in zip(bars, hatches):
    if h: bar.set_hatch(h)
ax.axvline(0, color="black", lw=0.8, ls="--")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel(r"$\Delta P(\mathrm{score} \geq 2)$", fontsize=13)
leg = [Patch(facecolor=DARK, edgecolor="white", label="Reinforce"),
       Patch(facecolor=DARK, edgecolor="white", hatch="///", label="Never reinforce"),
       Patch(facecolor=LIGHT, edgecolor="white", label="Uncertain")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 1.08),
          ncol=3, fontsize=9, frameon=False)
plt.tight_layout()
plt.savefig("../../paper/figures/reinforcement_policy.pdf", bbox_inches="tight")
print("gains:", {decisions[i]: round(float(gmean[i]),2) for i in order[:3]}, "| no_new:", round(float(gmean[list(decisions).index("dependencies_no_new")]),2))

import matplotlib.pyplot as _p; _p.savefig("../../paper/figures/reinforcement_policy.png", dpi=150, bbox_inches="tight")
