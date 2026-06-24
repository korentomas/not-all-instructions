"""Generate the report figures (dark editorial palette) from the saved posteriors.
Writes PNGs to report-figures/. v1 = experiments-v1/analysis/retention_model.nc;
v2 (M4) = the validated trace from the model-exploration run.
"""
from pathlib import Path
import numpy as np
import arviz as az
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "report-figures"
FIGS.mkdir(exist_ok=True)
V1 = ROOT / "experiments-v1/analysis/retention_model.nc"
V2 = Path("/private/tmp/claude-501/-Users-tk-Documents-Personal-not-all-instructions/"
          "51c0d338-e015-4a38-8086-9de5344d5f07/scratchpad/bayes_out/M4_validated.nc")

GROUND, PANEL, TEXT, MUTED = "#181B24", "#1E2230", "#E9E6DC", "#9A9789"
ACCENT, TEAL, CLAY, RULE = "#C9A24B", "#57B0A8", "#C0503C", "#2C3140"
plt.rcParams.update({
    "figure.facecolor": GROUND, "axes.facecolor": GROUND, "savefig.facecolor": GROUND,
    "text.color": TEXT, "axes.labelcolor": TEXT, "xtick.color": MUTED, "ytick.color": TEXT,
    "axes.edgecolor": RULE, "grid.color": RULE, "font.size": 11,
    "font.family": "sans-serif", "axes.titlecolor": TEXT,
})


def summ(nc, var, coord):
    idata = az.from_netcdf(nc)
    s = az.summary(idata, var_names=[var], hdi_prob=0.94)
    s.index = list(idata.posterior.coords[coord].values)
    return s[["mean", "hdi_3%", "hdi_97%"]]


def forest(s, title, fname, sort=True, short=None):
    if sort:
        s = s.sort_values("mean")
    labels = [short(i) if short else i for i in s.index]
    y = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(8.4, 0.42 * len(s) + 1.4))
    for yi, (_, r) in zip(y, s.iterrows()):
        lo, hi, m = r["hdi_3%"], r["hdi_97%"], r["mean"]
        col = ACCENT if lo > 0 else (CLAY if hi < 0 else MUTED)
        ax.plot([lo, hi], [yi, yi], color=col, lw=2.2, solid_capstyle="round", alpha=.9)
        ax.plot(m, yi, "o", color=col, ms=7, mec=GROUND, mew=1.2)
    ax.axvline(0, color=MUTED, lw=1, ls=(0, (4, 3)), alpha=.6)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=10.5)
    ax.set_title(title, fontsize=13, loc="left", pad=12, fontweight="bold")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    ax.grid(axis="x", alpha=.25)
    fig.tight_layout()
    fig.savefig(FIGS / fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", fname)


# fig1 — v1 per-decision treatment effects
forest(summ(V1, "beta", "decision"),
       "Per-decision treatment effect β (v1, 94% HDI) — gold: benefits, red: harmed",
       "fig1_treatment_effects.png")

# fig3 — v2 per-model treatment slopes (M4)
forest(summ(V2, "t_model", "model"),
       "Per-model treatment slope (v2 / M4, 94% HDI) — how much each model retains when told",
       "fig3_model_slopes.png", short=lambda s: s.replace("-20260420", ""))

# fig2 — variance components: v1 sigma_beta vs v2 sources
v1s = az.summary(az.from_netcdf(V1), var_names=["sigma_beta"], hdi_prob=0.94)
v2i = az.from_netcdf(V2)
v2s = az.summary(v2i, var_names=["sigma_beta", "sigma_model", "sigma_tmodel", "sigma_codebase"], hdi_prob=0.94)
rows = [("σ_β  (v1: instruction only)", v1s.loc["sigma_beta"], ACCENT)]
lab = {"sigma_beta": "σ_β  instruction", "sigma_model": "σ_model  identity",
       "sigma_tmodel": "σ_tmodel  responsiveness", "sigma_codebase": "σ_codebase"}
for k in ["sigma_beta", "sigma_model", "sigma_tmodel", "sigma_codebase"]:
    rows.append((lab[k] + "  (v2)", v2s.loc[k], TEAL if k != "sigma_codebase" else MUTED))
fig, ax = plt.subplots(figsize=(8.4, 3.4))
for yi, (name, r, col) in enumerate(reversed(rows)):
    ax.plot([r["hdi_3%"], r["hdi_97%"]], [yi, yi], color=col, lw=2.4, solid_capstyle="round")
    ax.plot(r["mean"], yi, "o", color=col, ms=7, mec=GROUND, mew=1.2)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([n for n, _, _ in reversed(rows)], fontsize=10.5)
ax.set_title("Where the variance lives — group-level SDs (94% HDI)", fontsize=13, loc="left", pad=12, fontweight="bold")
ax.set_xlabel("standard deviation (log-odds)")
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(length=0); ax.grid(axis="x", alpha=.25)
fig.tight_layout(); fig.savefig(FIGS / "fig2_variance.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("wrote fig2_variance.png")

# fig4 — the backfire doesn't replicate: deps_no_new beta v1 vs v2
b1 = summ(V1, "beta", "decision").loc["dependencies_no_new"]
b2 = summ(V2, "beta", "decision").loc["dependencies_no_new"]
fig, ax = plt.subplots(figsize=(8.4, 2.3))
for yi, (lab_, r, col) in enumerate([("v2 (fixed checker)", b2, TEAL), ("v1 (published)", b1, CLAY)]):
    ax.plot([r["hdi_3%"], r["hdi_97%"]], [yi, yi], color=col, lw=2.6, solid_capstyle="round")
    ax.plot(r["mean"], yi, "o", color=col, ms=8, mec=GROUND, mew=1.2)
    ax.annotate(f"{r['mean']:+.2f}", (r["mean"], yi + .18), color=col, fontsize=10, ha="center")
ax.axvline(0, color=MUTED, lw=1, ls=(0, (4, 3)), alpha=.6)
ax.set_yticks([0, 1]); ax.set_yticklabels(["v2 (fixed checker)", "v1 (published)"], fontsize=11)
ax.set_ylim(-.5, 1.6)
ax.set_title("The “backfire” does not replicate — dependencies_no_new β", fontsize=13, loc="left", pad=12, fontweight="bold")
ax.set_xlabel("treatment effect β (log-odds)")
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(length=0); ax.grid(axis="x", alpha=.25)
fig.tight_layout(); fig.savefig(FIGS / "fig4_backfire.png", dpi=150, bbox_inches="tight"); plt.close(fig)
print("wrote fig4_backfire.png")
print("DONE -> report-figures/")
