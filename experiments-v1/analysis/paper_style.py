"""Shared plotting style for the four camera-ready paper figures.

Import this module first in every figure script:

    import paper_style as ps
    ps.apply()

It sets STIX serif rcParams (text + math), grayscale palette, and a few
small helpers so all four figures share one unified aesthetic.
"""
import matplotlib as mpl

# -- Grayscale palette (shared across all four figures) ----------------------
DARK = "#4d4d4d"    # primary / "significant" category, observed markers
LIGHT = "#cccccc"   # secondary / "inconclusive" category, predicted bars
MED = "#808080"     # mid gray (fig 4 predicted markers)

# -- Consistent element styling ---------------------------------------------
LABEL_FONTSIZE = 13     # axis labels  (~9.5pt on page at 0.75 scale)
TICK_FONTSIZE = 11      # tick labels  (~8pt on page)
LEGEND_FONTSIZE = 11    # legends      (~8pt on page)
AXES_LINEWIDTH = 0.8    # spine + zero-line width

# One error-bar style used by every figure that has error bars.
ERRORBAR_KW = dict(ecolor="black", elinewidth=1.1, capsize=3, capthick=1.1)


def apply():
    """Set global rcParams for the unified paper aesthetic."""
    mpl.rcParams.update({
        # STIX serif for text AND math; no DejaVu Sans anywhere.
        "mathtext.fontset": "stix",
        "font.family": "STIXGeneral",
        "font.size": 11,
        "axes.labelsize": LABEL_FONTSIZE,
        "axes.titlesize": LABEL_FONTSIZE,
        "xtick.labelsize": TICK_FONTSIZE,
        "ytick.labelsize": TICK_FONTSIZE,
        "legend.fontsize": LEGEND_FONTSIZE,
        "axes.linewidth": AXES_LINEWIDTH,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "figure.dpi": 150,
        "savefig.dpi": 150,
    })


def style_axes(ax):
    """Full 4-spine box with the shared linewidth on a single Axes."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(AXES_LINEWIDTH)


def clean_label(name):
    """Decision label: underscores -> spaces."""
    return name.replace("_", " ")


def save(fig, stem):
    """Write both ../../paper/figures/<stem>.pdf and .png (dpi 150, tight)."""
    base = f"../../paper/figures/{stem}"
    fig.savefig(f"{base}.pdf", bbox_inches="tight")
    fig.savefig(f"{base}.png", dpi=150, bbox_inches="tight")
    print(f"saved {base}.pdf and {base}.png")
