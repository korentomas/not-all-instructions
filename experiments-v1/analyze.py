"""Analyze experiment results: fit decay curves, compute AUCC, generate figures."""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import wilcoxon
from pathlib import Path

BASE_DIR = Path(__file__).parent
INSTRUCTION_TYPES = ["format", "constraint", "persona", "safety", "tool_use"]
COLORS = {
    "format": "#2196F3",
    "constraint": "#4CAF50",
    "persona": "#FF9800",
    "safety": "#F44336",
    "tool_use": "#9C27B0",
}


def load_phase_data(phase: int) -> list[dict]:
    data_dir = BASE_DIR / "data" / f"phase{phase}"
    logs = []
    for f in sorted(data_dir.glob("*.json")):
        with open(f) as fh:
            logs.append(json.load(fh))
    return logs


def extract_scores(logs: list[dict]) -> pd.DataFrame:
    """Extract per-turn compliance scores into a DataFrame."""
    rows = []
    for log in logs:
        for turn in log["turns"]:
            for itype in INSTRUCTION_TYPES:
                rows.append({
                    "conversation_id": log.get("conversation_id", 0),
                    "pool_id": log.get("pool_id", 0),
                    "condition": log.get("condition", "none"),
                    "model": log.get("provider", "unknown"),
                    "turn": turn["turn"],
                    "instruction_type": itype,
                    "score": turn["compliance"][itype]["score"],
                    "temptation_type": turn.get("temptation_type"),
                })
    return pd.DataFrame(rows)


def exponential_decay(t, s0, gamma):
    """S(t) = S0 * gamma^t"""
    return s0 * gamma**t


def fit_decay_curves(df: pd.DataFrame) -> dict[str, dict]:
    """Fit exponential decay per instruction type. Returns {itype: {s0, gamma, r2}}."""
    results = {}
    for itype in INSTRUCTION_TYPES:
        subset = df[df["instruction_type"] == itype]
        means = subset.groupby("turn")["score"].mean()

        try:
            popt, _ = curve_fit(
                exponential_decay,
                means.index.values,
                means.values,
                p0=[3.0, 0.95],
                bounds=([0, 0.5], [3.5, 1.0]),
                maxfev=5000,
            )
            predicted = exponential_decay(means.index.values, *popt)
            ss_res = np.sum((means.values - predicted) ** 2)
            ss_tot = np.sum((means.values - means.values.mean()) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            results[itype] = {"s0": popt[0], "gamma": popt[1], "r2": r2}
        except RuntimeError:
            results[itype] = {"s0": None, "gamma": None, "r2": None}

    return results


def compute_aucc(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Area Under the Compliance Curve per conversation per instruction type."""
    rows = []
    for (conv_id, condition, itype), group in df.groupby(
        ["conversation_id", "condition", "instruction_type"]
    ):
        sorted_group = group.sort_values("turn")
        aucc = np.trapz(sorted_group["score"].values, sorted_group["turn"].values)
        rows.append({
            "conversation_id": conv_id,
            "condition": condition,
            "instruction_type": itype,
            "aucc": aucc,
        })
    return pd.DataFrame(rows)


def plot_decay_curves(df: pd.DataFrame, decay_fits: dict, output_path: Path):
    """Plot forgetting curves per instruction type."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for itype in INSTRUCTION_TYPES:
        subset = df[df["instruction_type"] == itype]
        means = subset.groupby("turn")["score"].mean()
        sems = subset.groupby("turn")["score"].sem()

        ax.plot(means.index, means.values, color=COLORS[itype], label=itype, linewidth=2)
        ax.fill_between(
            means.index,
            means.values - sems.values,
            means.values + sems.values,
            color=COLORS[itype],
            alpha=0.15,
        )

        # Plot fitted curve
        fit = decay_fits.get(itype, {})
        if fit.get("gamma") is not None:
            t = np.linspace(0, means.index.max(), 100)
            ax.plot(
                t,
                exponential_decay(t, fit["s0"], fit["gamma"]),
                color=COLORS[itype],
                linestyle="--",
                alpha=0.7,
            )

    ax.set_xlabel("Turn", fontsize=12)
    ax.set_ylabel("Mean Compliance Score (0-3)", fontsize=12)
    ax.set_title("Instruction Compliance Decay by Type", fontsize=14)
    ax.legend(loc="lower left")
    ax.set_ylim(-0.1, 3.2)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_intervention_comparison(aucc_df: pd.DataFrame, output_path: Path):
    """Plot AUCC comparison across conditions."""
    fig, axes = plt.subplots(1, 5, figsize=(18, 5), sharey=True)

    for idx, itype in enumerate(INSTRUCTION_TYPES):
        ax = axes[idx]
        subset = aucc_df[aucc_df["instruction_type"] == itype]

        conditions = ["control", "uniform", "selective"]
        means = [subset[subset["condition"] == c]["aucc"].mean() for c in conditions]
        stds = [subset[subset["condition"] == c]["aucc"].std() for c in conditions]

        bars = ax.bar(conditions, means, yerr=stds, capsize=5, color=COLORS[itype], alpha=0.8)
        ax.set_title(itype, fontsize=11)
        ax.set_ylabel("AUCC" if idx == 0 else "")

    plt.suptitle("Intervention Comparison: AUCC by Instruction Type", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def main():
    fig_dir = BASE_DIR / "analysis" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Phase 1: Decay curves
    print("=== Phase 1 Analysis ===")
    p1_logs = load_phase_data(1)
    if p1_logs:
        p1_df = extract_scores(p1_logs)
        decay_fits = fit_decay_curves(p1_df)

        print("\nDecay rates (gamma) by instruction type:")
        for itype, fit in decay_fits.items():
            if fit["gamma"] is not None:
                print(f"  {itype}: gamma={fit['gamma']:.4f}, S0={fit['s0']:.2f}, R²={fit['r2']:.3f}")

        # Save decay rates for Phase 2
        with open(BASE_DIR / "data" / "phase1_decay_rates.json", "w") as f:
            json.dump({k: v["gamma"] for k, v in decay_fits.items() if v["gamma"]}, f, indent=2)

        plot_decay_curves(p1_df, decay_fits, fig_dir / "phase1_decay_curves.png")

    # Phase 2: Intervention comparison
    print("\n=== Phase 2 Analysis ===")
    p2_logs = load_phase_data(2)
    if p2_logs:
        p2_df = extract_scores(p2_logs)
        aucc_df = compute_aucc(p2_df)

        print("\nMean AUCC by condition × instruction type:")
        pivot = aucc_df.pivot_table(values="aucc", index="instruction_type", columns="condition", aggfunc="mean")
        print(pivot.to_string())

        # Wilcoxon test: selective vs uniform
        for itype in INSTRUCTION_TYPES:
            sel = aucc_df[(aucc_df["condition"] == "selective") & (aucc_df["instruction_type"] == itype)]["aucc"]
            uni = aucc_df[(aucc_df["condition"] == "uniform") & (aucc_df["instruction_type"] == itype)]["aucc"]
            if len(sel) > 1 and len(uni) > 1:
                stat, p = wilcoxon(sel.values[: min(len(sel), len(uni))], uni.values[: min(len(sel), len(uni))])
                sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"
                print(f"  {itype}: selective vs uniform p={p:.4f} {sig}")

        plot_intervention_comparison(aucc_df, fig_dir / "phase2_intervention_comparison.png")

    # Phase 3: Multi-model validation
    print("\n=== Phase 3 Analysis ===")
    p3_logs = load_phase_data(3)
    if p3_logs:
        p3_df = extract_scores(p3_logs)
        for model in p3_df["model"].unique():
            model_df = p3_df[p3_df["model"] == model]
            fits = fit_decay_curves(model_df)
            print(f"\n{model}:")
            for itype, fit in fits.items():
                if fit["gamma"] is not None:
                    print(f"  {itype}: gamma={fit['gamma']:.4f}")


if __name__ == "__main__":
    main()
