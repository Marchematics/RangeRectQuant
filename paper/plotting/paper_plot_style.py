"""Paper-sized adaptation of Chen Liu's figures4papers plotting conventions.

Reference: https://github.com/ChenLiu-1996/figures4papers
Commit: f0bb7559abe90f5e1828797126d4d133c1bd47d7
Adapted from figure_ImmunoStruct/plot_bars.py,
figure_CellSpliceNet/plot_comparison.py, and
figure_RNAGenScape/plot_comparison.py. Reference license: CC BY-NC 4.0
(https://creativecommons.org/licenses/by-nc/4.0/).
Changes: six-inch four-column grids, native-unit axes, shared legends/colorbars,
zero-based rate bars, and deterministic exports. The user's supplied references
set the serif type, enclosed axes, thin pastel curves and boxed shared legends.
Reference data are not reused.
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

# Matplotlib's Set2 palette matches the supplied seven-series reference.
REFERENCE_COLORS = ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3",
                    "#A6D854", "#FFD92F", "#E5C494"]


def apply_publication_style():
    # Physical font sizes apply at the manuscript's actual six-inch width.
    # The user's enclosed, serif reference overrides the repository's open axes.
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 8,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.linewidth": 0.55,
        "axes.grid": False,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.framealpha": 1,
        "legend.edgecolor": "#BBBBBB",
        "text.usetex": False,
        "mathtext.fontset": "stix",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "hatch.linewidth": 0.45,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.transparent": False,
        "savefig.bbox": None,
    })


def axes_style(ax, *, categorical=False):
    """Enclosed reference axes with light grids, including vertical log grids."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(.55)
    ax.set_axisbelow(True)
    ax.grid(which="major", axis="y" if categorical else "both",
            color="#CACACA", linewidth=.4, linestyle=":")
    if not categorical:
        ax.grid(which="minor", color="#E0E0E0", linewidth=.3, linestyle=":")
    ax.tick_params(which="major", labelsize=7.5, length=2.5, width=.5, pad=2)
    ax.tick_params(which="minor", length=1.5, width=.35)
    ax.xaxis.labelpad = 3
    ax.yaxis.labelpad = 3
    ax.title.set_fontweight("normal")


def shared_legend(fig, handles, labels=None, *, ncol, anchor=(.5, .995), fontsize=8):
    """One thin boxed legend for each scientifically coherent panel group."""
    if labels is None:
        labels = [handle.get_label() for handle in handles]
    legend = fig.legend(handles, labels, loc="upper center", bbox_to_anchor=anchor,
                        ncol=ncol, fontsize=fontsize, handlelength=1.65,
                        handletextpad=.5, columnspacing=1.2, borderpad=.35,
                        labelspacing=.35, frameon=True)
    legend.get_frame().set_linewidth(.45)
    return legend


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
    # Tight-bbox export would silently change printed font sizes. Catch clipped
    # labels on the fixed canvas instead of changing the physical dimensions.
    fig.canvas.draw()
    from matplotlib.text import Text
    renderer = fig.canvas.get_renderer()
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text() or artist.get_clip_on():
            continue
        box = artist.get_window_extent(renderer)
        # Matplotlib keeps out-of-view log/minor tick Text objects visible.
        if artist in [tick.label1 for ax in fig.axes for tick in ax.xaxis.get_major_ticks() + ax.xaxis.get_minor_ticks()] + [tick.label1 for ax in fig.axes for tick in ax.yaxis.get_major_ticks() + ax.yaxis.get_minor_ticks()]:
            if not box.overlaps(fig.bbox):
                continue
        if (box.x0 < -1 or box.y0 < -1 or box.x1 > fig.bbox.width + 1 or
                box.y1 > fig.bbox.height + 1):
            raise ValueError(f"Text outside fixed figure canvas: {artist.get_text()!r}")
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
