"""FIG 2: per-decision treatment-effect forest (beta_d, log-odds).

Horizontal forest sorted by mean beta with 94% HDI. Three categories:
HDI excludes 0 (dark), negative effect (dark + hatch), inconclusive (light).
"""
import arviz as az
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import paper_style as ps
ps.apply()

idata = az.from_netcdf("retention_model.nc")
bs = az.summary(idata, var_names=["beta"], hdi_prob=0.94).sort_values("mean")
labels = [ps.clean_label(i.replace("beta[", "").replace("]", ""))
          for i in bs.index]

colors, hatches = [], []
for _, r in bs.iterrows():
    if r["hdi_3%"] > 0:
        colors.append(ps.DARK); hatches.append("")
    elif r["hdi_97%"] < 0:
        colors.append(ps.DARK); hatches.append("///")
    else:
        colors.append(ps.LIGHT); hatches.append("")

fig, ax = plt.subplots(figsize=(5.4, 4.2))
y = np.arange(len(bs))
xerr = [bs["mean"] - bs["hdi_3%"], bs["hdi_97%"] - bs["mean"]]
bars = ax.barh(y, bs["mean"], xerr=xerr, color=colors, alpha=0.9,
               edgecolor="white", height=0.7, error_kw=ps.ERRORBAR_KW)
for b, h in zip(bars, hatches):
    if h:
        b.set_hatch(h)
ax.axvline(0, color="black", lw=ps.AXES_LINEWIDTH, ls="--")
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel(r"Treatment effect ($\beta_d$, log-odds)")
leg = [Patch(facecolor=ps.DARK, edgecolor="white", label="94% HDI excludes 0"),
       Patch(facecolor=ps.DARK, edgecolor="white", hatch="///",
             label="Negative effect"),
       Patch(facecolor=ps.LIGHT, edgecolor="white", label="Inconclusive")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, 1.08),
          ncol=3, frameon=False)
ps.style_axes(ax)
fig.tight_layout()
ps.save(fig, "treatment_effects_forest")

top = bs["mean"].sort_values(ascending=False)
print("top betas:")
for name in ["beta[testing_parametrize]", "beta[dependencies_module_constants]",
             "beta[architecture_standalone]", "beta[dependencies_no_new]"]:
    print(f"  {name:42s} {bs.loc[name, 'mean']:+.2f}")
