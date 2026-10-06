"""Three-panel coding/precision summary from existing source-free results.

The distribution retains every matched field at all forty locations. Step
curves summarize all four illustrated cities; shaded spans are observed
minima and maxima, not uncertainty estimates. The eight-panel archive is
unchanged. No experiment or decoder is run here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

from paper_plot_style import apply_publication_style, axes_style, save_figure, shared_legend, plt
import reference_grids as grids

BUDGETS = (100, 1000)


def empirical_cdf(values):
    """Return the exact empirical cumulative percentages, retaining ties."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Expected a nonempty finite one-dimensional sample")
    return np.sort(values), 100 * np.arange(1, len(values) + 1) / len(values)


def step_summary(rows, budget, metric):
    """Summarize all cities at every saved divisor without interpolation."""
    if metric not in ("rate", "fine"):
        raise ValueError(f"Unknown step metric: {metric}")
    series = np.array([
        [rows[site, budget, divisor]["packet_bytes"] * 8 / 512**2
         if metric == "rate" else
         rows[site, budget, divisor]["geometry"]["fine_fraction"] * 100
         for divisor in grids.DIVISORS]
        for site in grids.SITES
    ])
    return {"cities": list(grids.SITES), "divisors": list(grids.DIVISORS),
            "series": series.tolist(), "median": np.median(series, axis=0).tolist(),
            "minimum": series.min(axis=0).tolist(), "maximum": series.max(axis=0).tolist()}


def core_mechanism():
    sites, representations = grids.representations()
    steps = grids.step_rows()
    gains = {
        budget: [100 * (1 - representations[site, budget, "split"]["packet_bytes"] /
                        representations[site, budget, "direct"]["packet_bytes"])
                 for site in sites]
        for budget in BUDGETS
    }
    # Include zero and every measured gain, even if later data contain losses.
    lower = min(0, 5 * np.floor(min(min(v) for v in gains.values()) / 5))
    upper = max(5, 5 * np.ceil(max(max(v) for v in gains.values()) / 5))
    fig, axes = plt.subplots(1, 3, figsize=(6, 2.4))
    displayed = {"coding_gain": {}, "step": {}}
    for budget in BUDGETS:
        color = grids.BUDGET_COLORS[budget]
        style = "-" if budget == 100 else "--"
        x, percentage = empirical_cdf(gains[budget])
        axes[0].step([lower, *x, upper], [0, *percentage, 100], where="post",
                     color=color, linestyle=style, linewidth=1.1)
        displayed["coding_gain"][str(budget)] = {
            "sites": sites, "gain_percent": gains[budget], "sample_count": len(sites),
            "sorted_gain_percent": x.tolist(), "cumulative_percent": percentage.tolist(),
        }
        for ax, metric in zip(axes[1:], ("rate", "fine")):
            summary = step_summary(steps, budget, metric)
            xstep = np.arange(len(grids.DIVISORS))
            ax.fill_between(xstep, summary["minimum"], summary["maximum"],
                            color=color, alpha=.16, linewidth=0)
            ax.plot(xstep, summary["median"], color=color, linestyle=style,
                    marker="v", markersize=3.8, markeredgewidth=.4, linewidth=1.1)
            displayed["step"][f"{budget}/{metric}"] = summary
    axes[0].set(xlim=(lower, upper), ylim=(0, 100),
                xlabel="Coding gain (%)", ylabel="Locations (%)")
    axes[0].set_yticks([0, 25, 50, 75, 100])
    axes[0].xaxis.set_major_locator(MaxNLocator(nbins=4))
    for ax, ylabel in zip(axes[1:], ("File size (bits/pixel)", "Fine pixels (%)")):
        ax.set_xticks([0, 2, 4, 7], ["16", "8", "5", "2"])
        ax.set(xlabel="Step divisor", ylabel=ylabel, ylim=(0, None))
        ax.axvline(4, color="#777777", linewidth=.65, linestyle=":")
    for letter, ax in zip("abc", axes):
        axes_style(ax)
        ax.tick_params(labelsize=8.5)
        ax.xaxis.label.set_fontsize(9)
        ax.yaxis.label.set_fontsize(9)
        ax.text(.5, 1.04, f"({letter})", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=9.5)
    handles = [Line2D([], [], color=grids.BUDGET_COLORS[budget], linewidth=1.1,
                      linestyle="-" if budget == 100 else "--",
                      label=f"Budget {budget} m²") for budget in BUDGETS]
    shared_legend(fig, handles, ncol=2, fontsize=9)
    fig.subplots_adjust(left=.085, right=.985, bottom=.245, top=.75, wspace=.55)
    return fig, displayed


def main():
    apply_publication_style()
    figure, displayed = core_mechanism()
    destination = grids.OUT / "core_mechanism"
    save_figure(figure, destination)
    sources = [Path(__file__).resolve(),
               grids.ROOT / "paper/plotting/reference_grids.py",
               grids.ROOT / "paper/plotting/paper_plot_style.py"]
    outputs = [destination.with_suffix(suffix) for suffix in (".pdf", ".png")]
    receipt = {
        "status": "SAVED_DATA_ONLY",
        "layout": {"inches": [6, 2.4], "panels": [1, 3]},
        "inputs": dict(sorted(grids.INPUTS.items())),
        "sources": {str(path.relative_to(grids.ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sources},
        "outputs": {str(path.relative_to(grids.ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in outputs},
        "displayed": displayed,
        "step_summary": "Median and observed minimum--maximum across all four cities",
        "uncertainty_estimate": False,
        "new_experiments": False,
        "previous_eight_panel_figure_and_atlas_unchanged": True,
    }
    (grids.OUT / "provenance_core_mechanism.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
