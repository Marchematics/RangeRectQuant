"""Paper-sized adaptation of Chen Liu's figures4papers plotting conventions.

Reference: https://github.com/ChenLiu-1996/figures4papers
Commit: f0bb7559abe90f5e1828797126d4d133c1bd47d7
Adapted from figure_ImmunoStruct/plot_bars.py,
figure_CellSpliceNet/plot_comparison.py, and
figure_RNAGenScape/plot_comparison.py. Reference license: CC BY-NC 4.0
(https://creativecommons.org/licenses/by-nc/4.0/).
Changes: compact six-inch panels, native-unit axes, shared legends/colorbars,
zero-based rate bars, and deterministic exports. Reference data are not reused.
"""

from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Patch

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "red_2": "#E9A6A1",
    "red_strong": "#B64342",
    "neutral": "#CFCECE",
}


def apply_publication_style():
    # Reference scripts use Helvetica; Arial is installed on this host.
    # Sizes/lineweights are reduced with the canvas rather than shrinking a
    # 28-inch reference export to the paper's six-inch text width.
    plt.rcParams.update({
        "font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.1,
        "axes.grid": False,
        "legend.frameon": False,
        "text.usetex": False,
        "mathtext.fontset": "dejavusans",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "hatch.linewidth": 0.45,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.transparent": False,
        "savefig.bbox": None,
    })


def legend_handles(labels):
    return [
        Patch(facecolor=PALETTE["red_2"], edgecolor="black", linewidth=0.7,
              hatch="///", label=labels[0]),
        Patch(facecolor=PALETTE["blue_main"], edgecolor="black", linewidth=0.7,
              label=labels[1]),
    ]


def paired_bars(ax, x, comparator, proposed, width=0.34, fmt="{:.1f}"):
    containers = []
    for shift, values, color, hatch in [
        (-width / 2, comparator, PALETTE["red_2"], "///"),
        (width / 2, proposed, PALETTE["blue_main"], None),
    ]:
        bars = ax.bar(x + shift, values, width=width, color=color,
                      edgecolor="black", linewidth=0.65, hatch=hatch)
        # Put the proposed values inside the blue bars so their labels cannot
        # cross a taller neighboring comparator's edge/hatching.
        ax.bar_label(bars, labels=[fmt.format(v) for v in values],
                     padding=3 if hatch else -12, fontsize=8,
                     color="black" if hatch else "white")
        containers.append(bars)
    ax.tick_params(axis="x", length=0, pad=5)
    ax.tick_params(axis="y", length=3, width=0.8)
    return containers


def save_figure(fig, destination: Path, dpi=300):
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Fixed creation metadata makes regenerated PDFs byte-stable on this runtime.
    fixed_date = datetime(2026, 10, 1, tzinfo=timezone.utc)
    fig.savefig(destination.with_suffix(".pdf"), dpi=dpi, metadata={
        "Creator": "RangeRectQuant saved-data plotting",
        "CreationDate": fixed_date,
        "ModDate": fixed_date,
    })
    fig.savefig(destination.with_suffix(".png"), dpi=dpi,
                metadata={"Software": "RangeRectQuant saved-data plotting"})
    plt.close(fig)
