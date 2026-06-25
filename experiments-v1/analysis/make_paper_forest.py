import arviz as az, numpy as np, matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch

# Match the original paper figures (fig 1 + fig 4): STIX serif, not DejaVu Sans
mpl.rcParams["mathtext.fontset"] = "stix"
mpl.rcParams["font.family"] = "STIXGeneral"

idata = az.from_netcdf("retention_model.nc")
bs = az.summary(idata, var_names=["beta"], hdi_prob=0.94).sort_values("mean")
labels = [i.replace("beta[","").replace("]","").replace("_"," ") for i in bs.index]

DARK, LIGHT = "#4d4d4d", "#cccccc"
colors, hatches = [], []
for _, r in bs.iterrows():
    if r["hdi_3%"] > 0:   colors.append(DARK);  hatches.append("")
    elif r["hdi_97%"] < 0: colors.append(DARK); hatches.append("///")
    else:                 colors.append(LIGHT); hatches.append("")

fig, ax = plt.subplots(figsize=(8,6))
y = np.arange(len(bs))
xerr = [bs["mean"]-bs["hdi_3%"], bs["hdi_97%"]-bs["mean"]]
bars = ax.barh(y, bs["mean"], xerr=xerr, color=colors, alpha=0.9,
               capsize=3, edgecolor="white", height=0.7,
               error_kw=dict(ecolor="black", elinewidth=1.1, capthick=1.1))
for b,h in zip(bars,hatches):
    if h: b.set_hatch(h)
ax.axvline(0, color="black", lw=0.8, ls="--")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10)
ax.set_xlabel(r"Treatment effect ($\beta_d$, log-odds)", fontsize=12)
leg = [Patch(facecolor=DARK, edgecolor="white", label="94% HDI excludes 0"),
       Patch(facecolor=DARK, edgecolor="white", hatch="///", label="Negative effect"),
       Patch(facecolor=LIGHT, edgecolor="white", label="Inconclusive")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5,1.08),
          ncol=3, fontsize=9, frameon=False)
plt.tight_layout()
plt.savefig("../../paper/figures/treatment_effects_forest.pdf", bbox_inches="tight")
print("saved ../../paper/figures/treatment_effects_forest.pdf")

import matplotlib.pyplot as _p; _p.savefig("../../paper/figures/treatment_effects_forest.png", dpi=150, bbox_inches="tight")
