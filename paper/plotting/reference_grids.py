"""Four-column experimental grids from immutable, source-free saved results.

The supplied reference figures determine visual layout only. Code conventions
adapt Chen Liu's figures4papers (pinned attribution in paper_plot_style.py).
No experiment is launched, and no uncertainty or missing measurement is filled.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator

from paper_plot_style import (REFERENCE_COLORS, axes_style, plt, shared_legend)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper/figures/research"
INPUTS = {}
PLOTTED = {}
COLORS = dict(zip(("fixed-margin", "RangeRectQuant", "sz3", "mgard", "qpet",
                       "external-best", "lossless"), REFERENCE_COLORS))
LABELS = {"RangeRectQuant": "RangeRectQuant", "fixed-margin": "Fixed margin",
          "sz3": "SZ3", "mgard": "MGARD", "qpet": "QPET",
          "lossless": "Exact reconstruction", "external-best": "Best external (water)"}
METHODS = ["RangeRectQuant", "fixed-margin", "sz3", "mgard", "qpet", "lossless"]
BUDGET_COLORS = {100: REFERENCE_COLORS[0], 1000: REFERENCE_COLORS[1]}
SITES = ["cairo", "delhi", "new_york", "jakarta"]
SITE_COLORS = dict(zip(SITES, REFERENCE_COLORS[:4]))
DIVISORS = [16, 12, 8, 6, 5, 4, 3, 2]
CONSTRUCTIONS = ["sigma-delta", "sigma-delta-clip", "sigma-delta-clip-integer",
                 "sigma-delta-project", "prefix-round", "prefix-round-clip", "RangeRectQuant"]
CONSTRUCTION_KEY = ("1: Stable sigma–delta   2: + clipping   3: + clipping + integer rounding\n"
                    "4: Projected sigma–delta   5: Prefix rounding   6: + clipping   7: RangeRectQuant")


def read(path):
    path = ROOT / path
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text())


def city(site):
    return site.replace("_", " ").title().replace(" De ", " de ")


def remember(key, value):
    """Export exact displayed numbers alongside input/output hashes."""
    PLOTTED[key] = value


def curve(ax, x, y, color, label=None, *, dashed=False):
    return ax.plot(x, y, color=color, label=label, marker="v", markersize=3.4,
                   markeredgewidth=.35, markeredgecolor=color, linewidth=.95,
                   linestyle="--" if dashed else "-")[0]


def line_key(labels, colors):
    return [Line2D([], [], color=c, marker="v", markersize=3.4, linewidth=.95, label=n)
            for n, c in zip(labels, colors)]


def rate_panels(axes):
    data = read("results/expanded_frontier_20261002/report.json")
    water = read("results/water_frontier_20261002/report.json")
    assert data["status"] == "COMPLETE_FIXED_40_LOCATION_MATRIX"
    assert water["sourcefree_decodes"] == 392 and water["exceptions"] == 0
    for ax, size, letter in zip(axes[:3], (256, 512, 1024), "abc"):
        rows = sorted((r for r in data["frontier"] if r["size"] == size), key=lambda r: r["epsilon"])
        assert len(rows) == 8 and all(r["qualifying_locations"]["RangeRectQuant"] == 40 for r in rows)
        for method in METHODS:
            values = [r["bpp"][method] for r in rows]
            curve(ax, [r["epsilon"] for r in rows],
                  [np.nan if v is None else v for v in values], COLORS[method], LABELS[method],
                  dashed=method == "lossless")
            remember(f"frontier/{size}/{method}", values)
        ax.set_xscale("log"); ax.set_ylim(0, 18)
        ax.set_xticks([25, 100, 1000, 5000], ["25", "100", "1000", "5000"])
        ax.set_xlabel("Sum budget (m²)")
        ax.set_title(f"({letter}) Built area, {size}²", pad=5)
        axes_style(ax)
        if ax is not axes[0]: ax.tick_params(labelleft=False)
    axes[0].set_ylabel("Complete size (bits/pixel)")
    ax = axes[3]; rows = water["comparisons"]
    for method, field in (("RangeRectQuant", "main_bytes"), ("external-best", "baseline_bytes")):
        values = [r[field] * 8 / (8 * 512**2) for r in rows]
        curve(ax, [r["epsilon"] for r in rows], values, COLORS[method], LABELS[method],
              dashed=method == "external-best")
        remember(f"frontier/water/{method}", values)
    ax.set_xscale("log"); ax.set_ylim(0, .6)
    ax.set_xticks([5, 25, 100, 1000], ["5", "25", "100", "1000"])
    ax.set_yticks([0, .2, .4, .6])
    ax.set_title("(d) Water, 512²", pad=5)
    ax.set_xlabel("Sum budget (pct. points)"); axes_style(ax)
    return line_key([LABELS[m] for m in METHODS + ["external-best"]],
                    [COLORS[m] for m in METHODS + ["external-best"]])


def frontier():
    fig, axes = plt.subplots(1, 4, figsize=(6, 2.2))
    handles = rate_panels(axes)
    shared_legend(fig, handles, ncol=4, fontsize=8)
    fig.subplots_adjust(left=.085, right=.985, bottom=.235, top=.70, wspace=.19)
    return fig


def representations():
    report = read("results/review_revision_20261002/report.json")
    assert report["blocks"]["representation"]["decodes"] == 1280
    manifest = read("integration/expanded_assets_20261002.json")
    sites = sorted(r["site"] for r in manifest["sites"])
    assert len(set(sites)) == 40
    rows = {}
    for site in sites:
        for e in (100, 1000):
            for layout in ("direct", "shuffled", "split"):
                r = read(f"results/review_revision_20261002/representation/{site}/e{e}-{layout}.json")
                assert r["status"] == "DECODED_AND_AUDITED"
                assert r["audit"]["legal_at"][str(e)] and r["audit"]["range_ok"]
                assert r["decoder"]["source_provided"] is False
                rows[site, e, layout] = r
            assert len({rows[site, e, layout]["decoder"]["numerator_sha256"]
                        for layout in ("direct", "shuffled", "split")}) == 1
    return sites, rows


def gain_panels(axes):
    sites, rows = representations()
    for col, ax in enumerate(axes):
        group = sites[col*10:(col+1)*10]; x = np.arange(10)
        for e, shift, hatch in ((100, -.19, "///"), (1000, .19, None)):
            values = [100 * (1 - rows[s, e, "split"]["packet_bytes"] /
                                rows[s, e, "direct"]["packet_bytes"]) for s in group]
            ax.bar(x+shift, values, width=.36, color=BUDGET_COLORS[e],
                   edgecolor="#555555", linewidth=.35, hatch=hatch)
            remember(f"coding_gain/{col}/{e}", dict(zip(group, values)))
        ax.set_ylim(0, 26); ax.set_yticks([0, 10, 20])
        ax.set_xticks(x, [city(s) for s in group], rotation=65, ha="right")
        axes_style(ax, categorical=True); ax.tick_params(axis="x", labelsize=6.7, pad=2)
        ax.set_title(f"({chr(97+col)}) Locations {col*10+1}–{col*10+10}", pad=5)
        if col: ax.tick_params(labelleft=False)
    axes[0].set_ylabel("Quotient–remainder\ncoding gain (%)")
    return [Patch(facecolor=BUDGET_COLORS[e], edgecolor="#555555", linewidth=.35,
                  hatch="///" if e == 100 else None, label=f"Budget {e} m²") for e in (100, 1000)]


def step_rows():
    report = read("results/review_revision_20261002/report.json")
    assert report["blocks"]["step"]["decodes"] == 128
    rows = {}
    for site in SITES:
        for e in (100, 1000):
            for divisor in DIVISORS:
                r = read(f"results/review_revision_20261002/step/{site}/e{e}-d{divisor}.json")
                assert r["audit"]["legal_at"][str(e)] and r["audit"]["range_ok"]
                assert r["decoder"]["source_provided"] is False
                rows[site, e, divisor] = r
    return rows


def step_panels(axes):
    rows = step_rows()
    for ax, (e, metric, label, letter) in zip(axes, (
            (100, "rate", "Size, 100 m²", "e"), (100, "fine", "Fine (%), 100 m²", "f"),
            (1000, "rate", "Size, 1000 m²", "g"), (1000, "fine", "Fine (%), 1000 m²", "h"))):
        for site in SITES:
            values = [(rows[site, e, d]["packet_bytes"] * 8 / 512**2 if metric == "rate" else
                       rows[site, e, d]["geometry"]["fine_fraction"] * 100) for d in DIVISORS]
            curve(ax, np.arange(8), values, SITE_COLORS[site], city(site))
            remember(f"step/{e}/{metric}/{site}", values)
        ax.set_xticks([0, 2, 4, 7], ["16", "8", "5", "2"])
        ax.set_xlabel("Step divisor"); ax.set_title(f"({letter}) {label}", pad=5)
        ax.axvline(4, color="#777777", linewidth=.65, linestyle=":")
        ax.set_ylim(bottom=0); axes_style(ax)
    axes[0].set_ylabel("Complete bits/pixel")
    return line_key([city(s) for s in SITES], [SITE_COLORS[s] for s in SITES])


def review_mechanism():
    fig = plt.figure(figsize=(6, 4.15))
    # Separate bands allow rotated city names and one legend for each row.
    top = [fig.add_axes([.085 + .233*i, .65, .20, .24]) for i in range(4)]
    bottom = [fig.add_axes([.085 + .233*i, .12, .19, .27]) for i in range(4)]
    shared_legend(fig, gain_panels(top), ncol=2, anchor=(.5, .995))
    shared_legend(fig, step_panels(bottom), ncol=4, anchor=(.5, .50))
    return fig


def review_mechanism_main():
    """A twelve-panel mechanism plate replaces two separate article floats."""
    fig = plt.figure(figsize=(6, 5.05))
    top = [fig.add_axes([.085 + .233*i, .74, .20, .175]) for i in range(4)]
    middle = [fig.add_axes([.085 + .233*i, .335, .19, .18]) for i in range(4)]
    shared_legend(fig, gain_panels(top), ncol=2, anchor=(.5, .995))
    shared_legend(fig, step_panels(middle), ncol=4, anchor=(.5, .61))
    maps = [fig.add_axes([.085 + .233*i, .075, .19, .15]) for i in range(4)]
    colorbars = [fig.add_axes([.085 + .233*i, .06, .19, .009]) for i in range(4)]
    mechanism_panels(fig, maps, colorbars, letters="ijkl", small=True)
    return fig


def coding_city_fullpage():
    sites, rows = representations()
    fig, axes = plt.subplots(2, 4, figsize=(6, 5.8))
    colors = {"direct": REFERENCE_COLORS[0], "shuffled": REFERENCE_COLORS[2], "split": REFERENCE_COLORS[1]}
    names = {"direct": "Direct 16-bit", "shuffled": "Byte-shuffled", "split": "Split streams"}
    for row, e in enumerate((100, 1000)):
        for col, ax in enumerate(axes[row]):
            group = sites[col*10:(col+1)*10]; x = np.arange(10)
            for shift, layout, hatch in ((-.26, "direct", "///"), (0, "shuffled", ".."), (.26, "split", None)):
                values = [rows[s, e, layout]["packet_bytes"] * 8 / 512**2 for s in group]
                ax.bar(x+shift, values, width=.25, color=colors[layout], edgecolor="#555555",
                       linewidth=.25, hatch=hatch)
                remember(f"city_coding/{e}/{col}/{layout}", dict(zip(group, values)))
            ax.set_ylim(0, 10); ax.set_yticks([0, 2, 4, 6, 8, 10])
            ax.set_xticks(x, [city(s) for s in group], rotation=65, ha="right")
            axes_style(ax, categorical=True); ax.tick_params(axis="x", labelsize=6.7)
            ax.set_title(f"({chr(97+row*4+col)}) Budget {e} m²", pad=5)
            if col: ax.tick_params(labelleft=False)
            else: ax.set_ylabel("Complete size (bits/pixel)")
    handles = [Patch(facecolor=colors[k], edgecolor="#555555", hatch=h, label=names[k])
               for k, h in (("direct", "///"), ("shuffled", ".."), ("split", None))]
    shared_legend(fig, handles, ncol=3)
    fig.text(.085, .013, "Forty 512² locations, alphabetical order; each triplet encodes exactly the same field.", fontsize=8)
    fig.subplots_adjust(left=.085, right=.985, bottom=.18, top=.89, wspace=.19, hspace=.9)
    return fig


def closest_panels(axes, *, metric="error", letters="abcd"):
    report = read("results/closest_mechanism_20261002/report.json")
    rows = read("results/closest_mechanism_20261002/ledger.json")["rows"]
    assert report["sourcefree_decodes"] == 56 and report["exceptions"] == 0
    x = np.arange(7)
    index = {(r["site"], r["configuration"]["epsilon"], r["configuration"]["family"]): r for r in rows}
    assert len(index) == 56
    for col, (ax, site) in enumerate(zip(axes, SITES)):
        for e, shift, hatch in ((100, -.18, "///"), (1000, .18, None)):
            group = [index[site, e, m] for m in CONSTRUCTIONS]
            values = [(r["audit"]["max_rectangle_error"] / e if metric == "error" else
                       r["packet_bytes"] * 8 / 512**2) for r in group]
            assert all(v > 0 for v in values)
            ax.bar(x+shift, values, width=.33, color=BUDGET_COLORS[e],
                   edgecolor="#555555", linewidth=.3, hatch=hatch)
            invalid = [i for i, r in enumerate(group) if not r["legal_at"][str(e)]]
            ax.plot(x[invalid]+shift, [values[i] * (1.2 if metric == "error" else 1) for i in invalid],
                    "x", color="#333333", markersize=3.2, markeredgewidth=.65, linestyle="none")
            remember(f"closest/{site}/{e}/{metric}", dict(zip(CONSTRUCTIONS, values)))
        ax.set_xticks(x, [str(i) for i in range(1, 8)])
        ax.set_xlabel("Construction"); ax.set_title(f"({letters[col]}) {city(site)}", pad=5)
        if metric == "error":
            ax.axhline(1, color="#555555", linestyle="--", linewidth=.65)
            ax.set_yscale("log"); ax.set_ylim(.1, 1e4); ax.set_yticks([.1, 1, 100, 10000])
        else: ax.set_ylim(0, 12)
        axes_style(ax, categorical=True)
        if col: ax.tick_params(labelleft=False)
    axes[0].set_ylabel("Regional error / budget" if metric == "error" else "Complete bits/pixel")
    return [Patch(facecolor=BUDGET_COLORS[e], edgecolor="#555555", hatch="///" if e == 100 else None,
                  label=f"Budget {e} m²") for e in (100, 1000)]


def closest():
    fig, axes = plt.subplots(1, 4, figsize=(6, 2.2))
    shared_legend(fig, closest_panels(axes), ncol=2)
    fig.text(.085, .01, CONSTRUCTION_KEY, fontsize=7.4, linespacing=1.35)
    fig.subplots_adjust(left=.085, right=.985, bottom=.34, top=.77, wspace=.19)
    return fig


def closest_fullpage():
    fig, axes = plt.subplots(2, 4, figsize=(6, 4.9))
    handles = closest_panels(axes[0]); closest_panels(axes[1], metric="rate", letters="efgh")
    shared_legend(fig, handles, ncol=2)
    fig.text(.085, .055, CONSTRUCTION_KEY, fontsize=7.4, linespacing=1.35)
    fig.text(.085, .012, "×: integer, range or regional violation. Dashed line: regional budget. All 56 decoded files shown.", fontsize=7.8)
    fig.subplots_adjust(left=.085, right=.985, bottom=.22, top=.90, wspace=.19, hspace=.52)
    return fig


def mechanism_panels(fig, axes, colorbars=None, *, letters="abcd", small=False):
    path = ROOT / "results/closest_mechanism_20261002/mechanism_example.npz"
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with np.load(path, allow_pickle=False) as z:
        x, y, widths, p = (z[k] for k in ("x", "y", "widths", "protected"))
    fine = (y % 200 != 0) & ~p
    assert x.shape == y.shape == widths.shape == p.shape == (512, 512)
    assert np.all(widths[fine] < 200)
    arrays = [x, (y-x).cumsum(0).cumsum(1), widths, fine.astype(int)]
    titles = [f"({letter}) {name}" for letter, name in zip(letters, ("Built area", "Prefix error", "Allowed states", "Fine pixels"))]
    settings = [("viridis", 0, 10000, [0, 10000], "m²"),
                ("RdBu_r", -250, 250, [-250, 0, 250], "m²"),
                ("Greys_r", 0, 501, [0, 250, 501], "Integer states"),
                ("Reds", 0, 1, [0, 1], "Coarse / fine")]
    for i, (ax, a, title, (cmap, lo, hi, ticks, label)) in enumerate(zip(axes, arrays, titles, settings)):
        artist = ax.imshow(a, cmap=cmap, vmin=lo, vmax=hi, rasterized=True, interpolation="nearest")
        ax.set_title(title, pad=4); ax.set_xticks([]); ax.set_yticks([])
        if colorbars is None:
            bar = fig.colorbar(artist, ax=ax, orientation="horizontal", fraction=.07, pad=.055, ticks=ticks)
        else:
            bar = fig.colorbar(artist, cax=colorbars[i], orientation="horizontal", ticks=ticks)
        bar.ax.tick_params(labelsize=6.5 if small else 7, length=2, width=.4, pad=1)
        bar.set_label(label, fontsize=6.8 if small else 7.5, labelpad=1.5)
        if label == "Coarse / fine": bar.ax.set_xticklabels(["Coarse", "Fine"])
    remember("mechanism", dict(shape=list(x.shape), fine_pixels=int(fine.sum()), step=200, budget=1000))


def mechanism():
    fig, axes = plt.subplots(1, 4, figsize=(6, 1.85))
    mechanism_panels(fig, axes)
    fig.subplots_adjust(left=.035, right=.975, bottom=.22, top=.88, wspace=.22)
    return fig


def protected_panels(axes):
    report = read("results/protected_sweep_20261002/report.json")
    rows = read("results/protected_sweep_20261002/ledger.json")["rows"]
    timing = read("results/protected_timing_20261002/report.json")
    assert report["joint_valid"] == 40 and report["exceptions"] == 0
    times = {r["id"]: r["median_seconds"] for r in timing["rows"]}
    fractions = [0, .001, .01, .05, .1]
    metrics = [("Complete bits/pixel", lambda r: 8*r["packet_bytes"]/512**2),
               ("Fine pixels (%)", lambda r: 100*r["mechanism"]["off_lattice"]/512**2),
               ("Construction + audit (ms)", lambda r: 1000*times[r["id"]]),
               ("Exact-value streams (bits/pixel)", lambda r: 8*r["fees"]["protected_bytes"]/512**2)]
    for e in (100, 1000):
        groups = [[r for r in rows if r["configuration"]["epsilon"] == e and
                   r["configuration"]["protected_fraction"] == f] for f in fractions]
        assert all(len(group) == 4 for group in groups)
        for ax, (label, metric) in zip(axes, metrics):
            values = [float(np.mean([metric(r) for r in group])) for group in groups]
            curve(ax, np.array(fractions)*100, values, BUDGET_COLORS[e], f"Budget {e} m²")
            remember(f"protected/{e}/{label}", values)
    for col, (ax, (label, _)) in enumerate(zip(axes, metrics)):
        ax.set_xlabel("Protected samples (%)"); ax.set_xticks([0, 1, 5, 10])
        ax.set_title(f"({chr(97+col)}) " + ["Complete size", "Fine pixels", "Warm time", "Exact-value cost"][col], pad=5)
        ax.set_ylabel(label); ax.set_ylim(bottom=0); axes_style(ax)
    return line_key([f"Budget {e} m²" for e in (100, 1000)], [BUDGET_COLORS[e] for e in (100, 1000)])


def protected():
    fig, axes = plt.subplots(1, 4, figsize=(6, 2.5))
    shared_legend(fig, protected_panels(axes), ncol=2)
    fig.subplots_adjust(left=.085, right=.985, bottom=.22, top=.77, wspace=.6)
    return fig


def scaling_panels(axes, *, epsilon=100, letters="abcd"):
    report = read("results/runtime_scaling_20261002/report.json")
    assert report["status"] == "COMPLETE_ATTEMPTED_SCALING" and report["exceptions"] == 0
    methods = ["RangeRectQuant", "Exact row search", "Fixed margin"]
    colors = [COLORS["RangeRectQuant"], REFERENCE_COLORS[2], COLORS["fixed-margin"]]
    metrics = [("Construction (s)", "core_seconds"), ("Complete encoding (s)", "encode_seconds"),
               ("Decoding (s)", "decode_seconds"), ("Peak process memory (MiB)", "process_peak_rss_bytes")]
    for method, color in zip(methods, colors):
        rows = sorted((r for r in report["rows"] if r["method"] == method and r["epsilon"] == epsilon
                       and r["status"] == "MEASURED"), key=lambda r: r["size"])
        for ax, (label, key) in zip(axes, metrics):
            selected = [r for r in rows if r.get(key) is not None and
                        (not key.endswith("seconds") or all(v is not None for v in r[key]))]
            values = [float(np.median(r[key])) if key.endswith("seconds") else r[key]/2**20 for r in selected]
            if selected: curve(ax, [r["size"] for r in selected], values, color, method)
            remember(f"scaling/{epsilon}/{method}/{key}", dict(zip([r["size"] for r in selected], values)))
    for col, (ax, (label, _)) in enumerate(zip(axes, metrics)):
        ax.set_xscale("log", base=2); ax.set_xticks([256, 1024, 4096], ["256", "1024", "4096"])
        ax.set_xlabel("Field width (pixels)"); ax.set_ylabel(label)
        ax.set_title(f"({letters[col]}) " + ["Construction", "Encoding", "Decoding", "Memory"][col], pad=5)
        if col < 3:
            ax.set_yscale("log")
            ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
            ax.yaxis.set_major_locator(LogLocator(numticks=4))
        else:
            ax.set_ylim(bottom=0); ax.yaxis.set_major_locator(MaxNLocator(4))
        axes_style(ax)
    return line_key(methods, colors)


def scaling():
    fig, axes = plt.subplots(2, 4, figsize=(6, 4.7))
    handles = scaling_panels(axes[0]); scaling_panels(axes[1], epsilon=1000, letters="efgh")
    shared_legend(fig, handles, ncol=3)
    fig.text(.085, .905, "A) Budget 100 m²", fontsize=9)
    fig.text(.085, .49, "B) Budget 1000 m²", fontsize=9)
    fig.text(.085, .027, "Three warm repetitions; whole-process memory. Exact search: 4096², 1000 m² worker timeout at 180 s.", fontsize=7.5)
    fig.text(.085, .008, "Construction measurements cover RangeRectQuant and exact row search.", fontsize=7.5)
    fig.subplots_adjust(left=.085, right=.985, bottom=.12, top=.84, wspace=.72, hspace=.74)
    return fig


def water():
    data = read("results/water_frontier_20261002/report.json")
    assert data["sourcefree_decodes"] == 392 and data["exceptions"] == 0
    rows = data["comparisons"]; sites = [p["site"] for p in rows[0]["pairs"]]
    assert len(set(sites)) == 8
    fig, axes = plt.subplots(2, 4, figsize=(6, 4.6))
    for letter, ax, site in zip("abcdefgh", axes.flat, sites):
        for method, key in (("RangeRectQuant", "main_bytes"), ("external-best", "baseline_bytes")):
            values = [next(p for p in r["pairs"] if p["site"] == site)[key]*8/512**2 for r in rows]
            curve(ax, [r["epsilon"] for r in rows], values, COLORS[method], LABELS[method],
                  dashed=method == "external-best")
            remember(f"water/{site}/{method}", values)
        ax.set_xscale("log"); ax.set_xticks([5, 25, 100, 1000], ["5", "25", "100", "1000"])
        ax.set_ylim(bottom=0); ax.set_xlabel("Sum budget (pct. points)")
        ax.set_title(f"({letter}) {city(site)}", pad=5); axes_style(ax)
        ax.yaxis.set_major_locator(MaxNLocator(4))
    axes[0, 0].set_ylabel("Complete bits/pixel"); axes[1, 0].set_ylabel("Complete bits/pixel")
    shared_legend(fig, line_key([LABELS[m] for m in ("RangeRectQuant", "external-best")],
                              [COLORS[m] for m in ("RangeRectQuant", "external-best")]), ncol=2)
    fig.text(.085, .028, "Eight native 512² water-occurrence fields; all eight budgets. Each panel has an independent y-axis.", fontsize=7.5)
    fig.text(.085, .008, "Complete-file rates include masks and metadata. Budgets are percentage-point sums.", fontsize=7.5)
    fig.subplots_adjust(left=.085, right=.985, bottom=.13, top=.88, wspace=.35, hspace=.54)
    return fig


def line_grid_fullpage():
    fig = plt.figure(figsize=(6, 9))
    # Each row has its own shared, boxed legend. Metrics never share scales
    # across different physical units, and no city/budget is discarded.
    positions = [(.75, .13), (.505, .13), (.265, .135), (.045, .11)]
    groups = []
    for bottom, height in positions:
        groups.append([fig.add_axes([.085 + .237*i, bottom, .18, height]) for i in range(4)])
    legends = [shared_legend(fig, rate_panels(groups[0]), ncol=4, anchor=(.5, .995), fontsize=7.7),
               shared_legend(fig, step_panels(groups[1]), ncol=4, anchor=(.5, .713)),
               shared_legend(fig, protected_panels(groups[2]), ncol=2, anchor=(.5, .467)),
               shared_legend(fig, scaling_panels(groups[3]), ncol=3, anchor=(.5, .228))]
    for legend, title in zip(legends, ("A) Rate across budgets", "B) Step sensitivity",
                                      "C) Protected samples", "D) Scaling, budget 100 m²")):
        legend.set_title(title, prop={"size": 8})
    for row, axes in zip("ABCD", groups):
        for i, ax in enumerate(axes):
            ax.set_title(f"({row}{i+1}) " + ax.get_title().split(") ", 1)[1], pad=5)
    # Long row labels move to the margin; titles carry each panel's metric.
    for row in groups[2:]:
        for ax in row:
            ax.set_ylabel("")
    for ax, unit in zip(groups[2], ["bits/pixel", "%", "ms", "bits/pixel"]):
        if unit == "ms":
            ax.set_title(ax.get_title() + " (ms)", pad=5)
        else:
            ax.text(.04, .94, unit, transform=ax.transAxes, ha="left", va="top", fontsize=7.3)
    for ax, unit in zip(groups[3], ["s", "s", "s", "MiB"]):
        ax.text(.04, .94, unit, transform=ax.transAxes, ha="left", va="top", fontsize=7.3)
    return fig


def step_fullpage():
    rows = step_rows()
    fig, axes = plt.subplots(4, 4, figsize=(6, 7.8))
    metrics = [("Complete size (bits/pixel)", lambda r: 8*r["packet_bytes"]/512**2),
               ("Fine pixels (%)", lambda r: 100*r["geometry"]["fine_fraction"]),
               ("Remainders (bits/pixel)", lambda r: 8*r["fees"]["remainder_bytes"]/512**2),
               ("Narrow intervals (%)", lambda r: 100*r["geometry"]["width_bound_fraction"])]
    for row, (label, metric) in enumerate(metrics):
        for col, site in enumerate(SITES):
            ax = axes[row, col]
            for e in (100, 1000):
                values = [metric(rows[site, e, d]) for d in DIVISORS]
                curve(ax, np.arange(8), values, BUDGET_COLORS[e], f"Budget {e} m²")
                remember(f"step_detail/{label}/{site}/{e}", values)
            ax.axvline(4, color="#777777", linewidth=.65, linestyle=":")
            ax.set_xticks([0, 2, 4, 7], ["16", "8", "5", "2"])
            ax.set_ylim(bottom=0); ax.set_xlabel("Step divisor")
            ax.set_title(f"({chr(97+row*4+col)}) {city(site)}", pad=5); axes_style(ax)
            ax.yaxis.set_major_locator(MaxNLocator(4))
            if col == 0: ax.set_ylabel(label)
        upper = max(line.get_ydata().max() for ax in axes[row] for line in ax.lines if line.get_marker() == "v") * 1.08
        for ax in axes[row]: ax.set_ylim(0, upper)
    shared_legend(fig, line_key([f"Budget {e} m²" for e in (100, 1000)],
                              [BUDGET_COLORS[e] for e in (100, 1000)]), ncol=2)
    fig.text(.085, .008, "Four earlier holdouts. Dotted lines: default divisor five. Narrow intervals bound the possible fine pixels.", fontsize=7.8)
    fig.subplots_adjust(left=.10, right=.985, bottom=.075, top=.92, wspace=.38, hspace=.7)
    return fig


def write_provenance(path, outputs):
    sources = [Path(__file__), ROOT/"paper/plotting/paper_plot_style.py",
               ROOT/"paper/plotting/make_research_figures.py", ROOT/"paper/plotting/make_review_figure.py",
               ROOT/"paper/plotting/make_experiment_atlas.py"]
    payload = dict(status="PASS_SAVED_DATA_FOUR_COLUMN_GRIDS", inputs=INPUTS, plotted=PLOTTED,
                   sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                   outputs={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},
                   reference_repo="https://github.com/ChenLiu-1996/figures4papers",
                   reference_commit="f0bb7559abe90f5e1828797126d4d133c1bd47d7",
                   reference_license="CC-BY-NC-4.0", columns=4,
                   user_visual_reference="Serif type, enclosed axes, dotted grids, thin curves, triangle-down markers, boxed shared legends",
                   experimental_files_modified=False, fabricated_results=False,
                   missing_measurements_imputed=False, uncertainty_bands_invented=False)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False)+"\n")
