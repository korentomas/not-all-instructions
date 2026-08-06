"""Regenerate the paper figures with projection styling for the JAIIO talk.

Reads the fitted model from experiments-v1/analysis/retention_model.nc and
writes PNGs (dpi 200) to talk/figures/. Spanish axis labels, sans-serif
fonts sized for a 1280x720 slide, and an accent-plus-muted palette
(validated: deutan dE 13.1 accent vs gray, hatch as secondary encoding).

Run from the talk/ directory: python3 make_slide_figs.py
"""
import arviz as az
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.special import expit

NC = "../experiments-v1/analysis/retention_model.nc"

# Grayscale, following the paper's figure scheme: dark for groups whose HDI
# excludes zero (hatch marks the negative one), light gray for inconclusive.
DARK = "#3a3a3a"     # group in focus / HDI excludes zero
MUTED = "#8f8f8f"    # inconclusive
INK = "#262626"      # text, axes
FADE = "#ececec"     # deemphasized bars in build variants
FADE_ERR = "#d4d4d4"

ERR = dict(ecolor=INK, elinewidth=1.6, capsize=4, capthick=1.6)
ERR_FADE = dict(ecolor=FADE_ERR, elinewidth=1.6, capsize=4, capthick=1.6)

from matplotlib import font_manager
for f in ("Inter-Regular", "Inter-SemiBold", "Inter-Bold", "Inter-Italic"):
    font_manager.fontManager.addfont(f"fonts/{f}.ttf")

mpl.rcParams.update({
    "font.family": "Inter",
    "mathtext.fontset": "stixsans",
    "font.size": 17,
    "axes.labelsize": 20,
    "xtick.labelsize": 17,
    "ytick.labelsize": 17,
    "legend.fontsize": 17,
    "axes.linewidth": 1.2,
    "text.color": INK,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "savefig.facecolor": "white",
})


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def save(fig, stem):
    fig.savefig(f"figures/{stem}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"saved figures/{stem}.png")


def label(name):
    return name.replace("_", " ")


idata = az.from_netcdf(NC)
post = idata.posterior
decisions = list(post["decision"].values)
obs = idata.observed_data["score"].values
treat = idata.constant_data["treatment"].values
didx = idata.constant_data["decision_idx"].values
pp = idata.posterior_predictive["score"].values.reshape(-1, obs.shape[0])

# ---------------------------------------------------------------- forest ----
bs = az.summary(idata, var_names=["beta"], hdi_prob=0.94).sort_values("mean")
fnames = [i.replace("beta[", "").replace("]", "") for i in bs.index]
groups = np.array([
    "pos" if r["hdi_3%"] > 0 else "neg" if r["hdi_97%"] < 0 else "mid"
    for _, r in bs.iterrows()
])

GROUP_COLOR = {"pos": DARK, "mid": MUTED, "neg": DARK}
GROUP_HATCH = {"pos": "", "mid": "", "neg": "///"}


def forest(stem, lit):
    """lit: set of group keys drawn in full color; the rest fade."""
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    y = np.arange(len(bs))
    for g in ("pos", "mid", "neg"):
        m = groups == g
        on = g in lit
        xerr = [bs["mean"][m] - bs["hdi_3%"][m], bs["hdi_97%"][m] - bs["mean"][m]]
        bars = ax.barh(y[m], bs["mean"][m], xerr=xerr,
                       color=GROUP_COLOR[g] if on else FADE,
                       edgecolor="white", linewidth=1.5, height=0.72,
                       error_kw=ERR if on else ERR_FADE, zorder=2)
        if GROUP_HATCH[g] and on:
            for b in bars:
                b.set_hatch(GROUP_HATCH[g])
    ax.axvline(0, color=INK, lw=1.2, ls="--", zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([label(n) for n in fnames])
    ax.set_xlabel(r"Efecto del tratamiento ($\beta_d$, log-odds)")
    handles = []
    if "pos" in lit:
        handles.append(Patch(facecolor=DARK, edgecolor="white",
                             label="HDI 94% excluye 0"))
    if "mid" in lit:
        handles.append(Patch(facecolor=MUTED, edgecolor="white",
                             label="No concluyente"))
    if "neg" in lit:
        handles.append(Patch(facecolor=DARK, edgecolor="white", hatch="///",
                             label="Efecto negativo"))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1.0),
              frameon=False)
    style(ax)
    fig.tight_layout()
    save(fig, stem)


forest("forest_b1", {"pos"})
forest("forest_b2", {"pos", "mid"})
forest("forest_full", {"pos", "mid", "neg"})

# --------------------------------------------------------- raw landscape ----
means = np.full((len(decisions), 2), np.nan)
for k in range(len(decisions)):
    for t in (0, 1):
        m = (didx == k) & (treat == t)
        if m.any():
            means[k, t] = obs[m].mean()
order = np.argsort(-(np.nan_to_num(means[:, 1]) - np.nan_to_num(means[:, 0])))

fig, ax = plt.subplots(figsize=(13.5, 5.6))
x = np.arange(len(decisions))
w = 0.4
ax.bar(x - w / 2, means[order, 0], width=w, color=MUTED,
       edgecolor="white", linewidth=1.5, label="Sin instrucción (baseline)")
ax.bar(x + w / 2, means[order, 1], width=w, color=DARK,
       edgecolor="white", linewidth=1.5, label="Con instrucción (treatment)")
ax.set_xticks(x)
ax.set_xticklabels([label(decisions[i]) for i in order],
                   rotation=38, ha="right")
ax.set_ylabel("Puntaje medio")
ax.set_yticks([0, 1, 2, 3])
ax.set_ylim(0, 3.15)
ax.legend(frameon=False, loc="upper left", ncol=1,
          bbox_to_anchor=(1.02, 1.0))
style(ax)
fig.tight_layout()
save(fig, "raw_landscape")

# ----------------------------------------------------------------- policy ----
a = post["alpha"].values.reshape(-1, len(decisions))
b = post["beta"].values.reshape(-1, len(decisions))
c = post["cutpoints"].values.reshape(-1, 3)[:, 1:2]
gain = (1 - expit(c - (a + b))) - (1 - expit(c - a))
gmean = gain.mean(0)
ghdi = np.percentile(gain, [3, 97], axis=0)
gorder = np.argsort(gmean)[::-1]

fig, ax = plt.subplots(figsize=(9.6, 4.8))
y = np.arange(len(decisions))
for i, k in enumerate(gorder):
    if ghdi[0, k] > 0:
        col, hatch = DARK, ""
    elif ghdi[1, k] < 0:
        col, hatch = DARK, "///"
    else:
        col, hatch = MUTED, ""
    bar = ax.barh(i, gmean[k], xerr=[[gmean[k] - ghdi[0, k]], [ghdi[1, k] - gmean[k]]],
                  color=col, edgecolor="white", linewidth=1.5, height=0.72,
                  error_kw=ERR, zorder=2)
    if hatch:
        bar[0].set_hatch(hatch)
ax.axvline(0, color=INK, lw=1.2, ls="--", zorder=1)
ax.set_yticks(y)
ax.set_yticklabels([label(decisions[k]) for k in gorder])
ax.set_xlabel(r"$\Delta P(\mathrm{score} \geq 2)$ al repetir la instrucción")
leg = [Patch(facecolor=DARK, edgecolor="white", label="Reforzar"),
       Patch(facecolor=MUTED, edgecolor="white", label="Incierto"),
       Patch(facecolor=DARK, edgecolor="white", hatch="///",
             label="Refuerzo dañino")]
ax.legend(handles=leg, loc="upper left", frameon=False,
          bbox_to_anchor=(1.02, 1.0))
style(ax)
fig.tight_layout()
save(fig, "policy")

# ------------------------------------------------------------------- ppc ----
levels = np.array([0, 1, 2, 3])
obs_prop = np.array([(obs == k).mean() for k in levels])
pred_draws = np.stack([(pp == k).mean(axis=1) for k in levels], axis=1)
pred_prop, pred_sd = pred_draws.mean(0), pred_draws.std(0)
base_m, treat_m = treat == 0, treat == 1
ppb, ppt = pp[:, base_m].mean(1), pp[:, treat_m].mean(1)
omb, omt = obs[base_m].mean(), obs[treat_m].mean()

fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.6, 4.2))
w = 0.4
axL.bar(levels - w / 2, obs_prop, width=w, color=DARK,
        edgecolor="white", linewidth=1.5, label="Observado")
axL.bar(levels + w / 2, pred_prop, width=w, color=MUTED, yerr=pred_sd,
        edgecolor="white", linewidth=1.5, label="Predicho", error_kw=ERR)
axL.set_xlabel("Puntaje")
axL.set_ylabel("Proporción")
axL.set_xticks(levels)
axL.set_ylim(0, max(obs_prop.max(), (pred_prop + pred_sd).max()) * 1.3)
axL.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.02))
style(axL)

bins = np.linspace(min(ppb.min(), ppt.min()), max(ppb.max(), ppt.max()), 40)
axR.hist(ppb, bins=bins, density=True, color=MUTED, alpha=0.85)
axR.hist(ppt, bins=bins, density=True, color=DARK, alpha=0.6)
axR.axvline(omb, color=INK, lw=2.2, ls="--", label=f"Baseline ({omb:.2f})")
axR.axvline(omt, color=INK, lw=2.2, label=f"Treatment ({omt:.2f})")
axR.set_xlabel("Puntaje medio")
axR.set_ylabel("Densidad")
axR.set_ylim(top=axR.get_ylim()[1] * 1.2)
axR.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.02))
style(axR)
fig.tight_layout()
save(fig, "ppc")

# -------------------------------------------------------- ppc per decision --
obs_means, pp_means, lo, hi = [], [], [], []
for k in range(len(decisions)):
    m = didx == k
    obs_means.append(obs[m].mean())
    dm = pp[:, m].mean(axis=1)
    pp_means.append(dm.mean())
    l, h = np.percentile(dm, [5, 95])
    lo.append(l), hi.append(h)
obs_means, pp_means = np.array(obs_means), np.array(pp_means)
lo, hi = np.array(lo), np.array(hi)
dorder = np.argsort(obs_means)

fig, ax = plt.subplots(figsize=(9.6, 4.8))
y = np.arange(len(decisions))
ax.errorbar(pp_means[dorder], y,
            xerr=[pp_means[dorder] - lo[dorder], hi[dorder] - pp_means[dorder]],
            fmt="s", color="#7f7f7f", markersize=9, zorder=2, **ERR)
ax.scatter(obs_means[dorder], y, color="black", s=80, zorder=3)
ax.set_yticks(y)
ax.set_yticklabels([label(decisions[i]) for i in dorder])
ax.set_xlabel("Puntaje medio")
ax.set_ylim(-0.7, len(decisions) - 1 + 0.9)
leg = [Line2D([0], [0], marker="o", color="none", markerfacecolor="black",
              markersize=10, label="Observado"),
       Line2D([0], [0], marker="s", color="none", markerfacecolor="#7f7f7f",
              markersize=10, label="Predicho (PI 90%)")]
ax.legend(handles=leg, frameon=False, loc="upper left",
          bbox_to_anchor=(1.02, 1.0))
style(ax)
fig.tight_layout()
save(fig, "ppc_decision")

# ----------------------------------------------------- latent scale ---------
# Why ordered logistic: the score is where eta lands between three cutpoints.
# Uses posterior means: cutpoints and (alpha, beta) for two real decisions.
cmean = post["cutpoints"].values.reshape(-1, 3).mean(0)
amean = post["alpha"].values.reshape(-1, len(decisions)).mean(0)
bmean = post["beta"].values.reshape(-1, len(decisions)).mean(0)
i_par = decisions.index("testing_parametrize")
i_doc = decisions.index("docs_numpy_style")

order12 = np.argsort(-bmean)          # forest order: biggest beta on top
n12 = len(decisions)
XLO, XHI = min(amean.min(), (amean + bmean).min()) - 0.8, \
           max(amean.max(), (amean + bmean).max()) + 0.8
fig, ax = plt.subplots(figsize=(11.5, 6.4))
edges = [XLO, *cmean, XHI]
for k in range(4):
    ax.axvspan(edges[k], edges[k + 1],
               color="#f1efe9" if k % 2 == 0 else "#e4e1da", zorder=0)
    ax.text((edges[k] + edges[k + 1]) / 2, n12 - 0.1, str(k), ha="center",
            fontsize=26, fontweight="bold", color="#6f6f6f")
for cx, name in zip(cmean, ("$c_1$", "$c_2$", "$c_3$")):
    ax.axvline(cx, color=INK, lw=1.4, ls="--", zorder=1)
    ax.text(cx, n12 + 0.75, name, ha="center", fontsize=18, color=INK)

for row, i in enumerate(order12):
    yy = n12 - 1 - row
    x0, x1 = amean[i], amean[i] + bmean[i]
    ax.plot([x0, x1], [yy, yy], color="#7f7f7f", lw=1.6, zorder=2)
    ax.scatter([x0], [yy], s=110, facecolor="white", edgecolor=INK,
               linewidth=2.0, zorder=3)
    ax.scatter([x1], [yy], s=110, color=INK, zorder=3)

ax.set_xlim(XLO, XHI)
ax.set_ylim(-0.7, n12 + 1.3)
ax.set_yticks(range(n12))
ax.set_yticklabels([label(decisions[i]) for i in order12[::-1]])
ax.set_xlabel(r"Cumplimiento latente $\eta$ (log-odds)")
ax.spines[["top", "right", "left"]].set_visible(False)
leg = [Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
              markeredgecolor=INK, markeredgewidth=2, markersize=11,
              label="Sin instrucción ($\\alpha_d$)"),
       Line2D([0], [0], marker="o", color="none", markerfacecolor=INK,
              markersize=11, label="Con instrucción ($\\alpha_d + \\beta_d$)")]
ax.legend(handles=leg, loc="upper left", bbox_to_anchor=(1.02, 1.0),
          frameon=False)
fig.tight_layout()
save(fig, "latent_scale")

print("betas:", {n: round(float(bs.loc[f'beta[{n}]', 'mean']), 2)
                 for n in ("testing_parametrize", "dependencies_no_new")})
