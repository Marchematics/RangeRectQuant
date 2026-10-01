#!/usr/bin/env python3
"""Regenerate manuscript figures from immutable saved ledgers/arrays only.

No quantizer, codec, decoder, optimization, or data acquisition is executed.
See paper_plot_style.py and ../notes/FIGURE_PROVENANCE.md for CC BY-NC 4.0
figures4papers adaptation attribution and exact source bindings.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FixedLocator, StrMethodFormatter

from paper_plot_style import (
    PALETTE, apply_publication_style, legend_handles, paired_bars, plt,
    save_figure,
)

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
FIGURES = PAPER / "figures"
PLOTTING = PAPER / "plotting"
REFERENCE = ROOT / ".aris/references/figures4papers"
REFERENCE_COMMIT = "f0bb7559abe90f5e1828797126d4d133c1bd47d7"
HELDOUT = "results/heldout_20261001"
DEVELOPMENT = "results/viable_greedy_20261001"
INPUTS = {}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_file(relative, expected_hash=None):
    path = ROOT / relative
    actual = sha256(path)
    if expected_hash is not None and actual != expected_hash:
        raise ValueError(f"Source binding differs: {relative}")
    INPUTS[relative] = {"sha256": actual, "bytes": path.stat().st_size}
    return path


def read_json(relative):
    return json.loads(checked_file(relative).read_text())


def validate_packet(entry):
    path = checked_file(entry["packet"], entry["packet_sha256"])
    if path.stat().st_size != entry["packet_bytes"]:
        raise ValueError(f"Complete file size differs: {entry['id']}")
    if sum(entry["fees"].values()) != entry["packet_bytes"]:
        raise ValueError(f"Complete fee sum differs: {entry['id']}")
    body = checked_file(entry["body"], entry["body_sha256"])
    if body.stat().st_size != entry["fees"]["body_bytes"]:
        raise ValueError(f"Body size differs: {entry['id']}")


def array_digest(array):
    canonical = np.ascontiguousarray(array, dtype="<i8")
    return hashlib.sha256(canonical.tobytes()).hexdigest()


def heldout_data():
    report = read_json(f"{HELDOUT}/report.json")
    ledger = read_json(f"{HELDOUT}/ledger.json")
    by_id = {entry["id"]: entry for entry in ledger}
    data = []
    site_order = ["cairo", "delhi", "new_york", "jakarta"]
    for epsilon in [100, 1000]:
        rows = []
        for site in site_order:
            comparison = next(v for v in report["comparisons"]
                              if v["epsilon"] == epsilon and v["site"] == site)
            external = by_id[comparison["baseline_id"]]
            legal_external = [v for v in ledger if v["site"] == site
                              and v["configuration"]["family"] not in {"dp", "greedy"}
                              and v["contracts"][str(epsilon)]["status"] == "LEGAL"]
            if external["packet_bytes"] != min(v["packet_bytes"] for v in legal_external):
                raise ValueError("Selected external is not the complete-byte minimum")
            proposed = next(v for v in ledger if v["site"] == site
                            and v["configuration"]["family"] == "greedy"
                            and v["configuration"]["step"] == epsilon // 5)
            for entry in [external, proposed]:
                validate_packet(entry)
                if entry["contracts"][str(epsilon)]["status"] != "LEGAL":
                    raise ValueError("Illegal field in rate figure")
            if external["packet_bytes"] != comparison["baseline_bytes"]:
                raise ValueError("Report external bytes differ")
            if proposed["packet_bytes"] != comparison["main_bytes"]:
                raise ValueError("Report main bytes differ")
            rows.append({
                "site": site, "external_id": external["id"],
                "proposed_id": proposed["id"],
                "external_bytes": external["packet_bytes"],
                "proposed_bytes": proposed["packet_bytes"],
                "external_KiB": external["packet_bytes"] / 1024,
                "proposed_KiB": proposed["packet_bytes"] / 1024,
                "proposed_rectangle_max_m2": proposed["contracts"][str(epsilon)][
                    "all_rectangle_query_error_exact"],
            })
        external_sum = sum(v["external_bytes"] for v in rows)
        proposed_sum = sum(v["proposed_bytes"] for v in rows)
        gate = next(v for v in report["gates"] if v["epsilon"] == epsilon)
        assert external_sum == gate["baseline_bytes"]
        assert proposed_sum == gate["main_bytes"]
        data.append({"epsilon_m2": epsilon, "rows": rows,
                     "external_bytes_total": external_sum,
                     "proposed_bytes_total": proposed_sum,
                     "reduction_percent": 100 * (1 - proposed_sum / external_sum)})
    return data


def plot_heldout_rates(data):
    fig, axes = plt.subplots(1, 2, figsize=(6, 2.8), sharey=True)
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.18, top=0.82, wspace=0.16)
    for panel, ax, group in zip(["a", "b"], axes, data):
        rows = group["rows"]
        paired_bars(ax, np.arange(4), [v["external_KiB"] for v in rows],
                    [v["proposed_KiB"] for v in rows], fmt="{:.0f}")
        ax.set_xticks(np.arange(4), ["Cairo", "Delhi", "New York", "Jakarta"])
        ax.tick_params(axis="x", labelsize=8.5)
        ax.set_ylim(0, 325)
        ax.set_yticks([0, 100, 200, 300])
        ax.text(0.02, 1.03, f"({panel})  " + rf"$\epsilon={group['epsilon_m2']:,}\ \mathrm{{m}}^2$",
                transform=ax.transAxes, ha="left", va="bottom", fontsize=10)
    axes[0].set_ylabel("Complete file size (KiB)")
    fig.legend(handles=legend_handles(["Best external control", "RangeRectQuant"]),
               loc="upper center", bbox_to_anchor=(0.55, 1), ncols=2,
               columnspacing=1.8, handlelength=1.6)
    save_figure(fig, FIGURES / "heldout_rates")


def field_data():
    ledger = read_json(f"{HELDOUT}/ledger.json")
    entry = next(v for v in ledger if v["id"] == "cairo-44-greedy")
    source_path = checked_file(entry["source"], entry["source_sha256"])
    output_path = checked_file(entry["output"], entry["output_sha256"])
    with np.load(source_path, allow_pickle=False) as loaded:
        source = loaded["raw"].astype(np.int64)
        mask = loaded["mask"].astype(bool)
    with np.load(output_path, allow_pickle=False) as loaded:
        floating_output = loaded["y"]
        output_mask = loaded["mask"].astype(bool)
        if not np.isfinite(floating_output).all():
            raise ValueError("Nonfinite saved output")
        output = floating_output.astype(np.int64)
        if not np.array_equal(output, floating_output):
            raise ValueError("Saved output is not integer-valued")
    assert source.shape == output.shape == (512, 512)
    assert np.array_equal(mask, output_mask)
    assert np.count_nonzero(mask) == 0
    assert output.min() >= 0 and output.max() <= 10000
    delta = np.where(mask, 0, output - source)
    prefix = delta.cumsum(axis=0, dtype=np.int64).cumsum(axis=1, dtype=np.int64)
    bound = 250
    assert np.abs(prefix).max() <= bound
    assert np.count_nonzero(output % 200) == entry["fine"]
    stats = {
        "site": "cairo", "entry_id": entry["id"], "epsilon_m2": 1000,
        "coarse_step_m2": 200, "prefix_bound_m2": bound,
        "source": entry["source"], "decoded": entry["output"],
        "shape": list(source.shape), "nodata_count": int(mask.sum()),
        "source_range_m2": [int(source.min()), int(source.max())],
        "decoded_range_m2": [int(output.min()), int(output.max())],
        "source_sum_m2": int(source.sum()), "decoded_sum_m2": int(output.sum()),
        "changed_samples": int(np.count_nonzero(delta)),
        "fine_samples": int(np.count_nonzero(output % 200)),
        "signed_point_error_range_m2": [int(delta.min()), int(delta.max())],
        "signed_prefix_error_range_m2": [int(prefix.min()), int(prefix.max())],
        "normalized_prefix_error_range": [float(prefix.min()/bound), float(prefix.max()/bound)],
        "ledger_exact_rectangle_max_m2": entry["contracts"]["1000"][
            "all_rectangle_query_error_exact"],
        "source_array_int64_sha256": array_digest(source),
        "decoded_array_int64_sha256": array_digest(output),
        "prefix_array_int64_sha256": array_digest(prefix),
        "normalization": "E/B, E=cumsum_rows(cumsum_columns(Y-X)), B=250 m^2",
        "display": "Full 512x512 arrays, upper origin, nearest interpolation; no crop or resampling of input arrays",
    }
    return source, output, prefix / bound, stats


def plot_field_example(source, output, normalized_prefix):
    fig = plt.figure(figsize=(6, 2.95))
    grid = fig.add_gridspec(2, 3, left=0.095, right=0.985, bottom=0.25,
                           top=0.91, height_ratios=[1, 0.055], hspace=0.41, wspace=0.12)
    axes = [fig.add_subplot(grid[0, i]) for i in range(3)]
    value_cmap = plt.get_cmap("Blues")
    error_cmap = LinearSegmentedColormap.from_list(
        "figures4papers_signed", [PALETTE["blue_main"], "white", PALETTE["red_strong"]])
    value_images = []
    for i, array in enumerate([source, output, normalized_prefix]):
        ax = axes[i]
        image = ax.imshow(array, cmap=value_cmap if i < 2 else error_cmap,
                          vmin=0 if i < 2 else -1, vmax=10000 if i < 2 else 1,
                          origin="upper", interpolation="nearest", rasterized=True)
        if i < 2:
            value_images.append(image)
        ax.set_xticks([0, 256, 511])
        ax.set_yticks([0, 256, 511])
        ax.tick_params(length=2.5, pad=2, labelsize=8)
        if i > 0:
            ax.tick_params(labelleft=False)
        ax.set_xlabel("Column (pixels)", fontsize=9, labelpad=2)
        labels = ["(a) Source $X$", "(b) Decoded $Y$", "(c) Prefix error"]
        ax.text(0, 1.04, labels[i], transform=ax.transAxes,
                ha="left", va="bottom", fontsize=9.5)
    axes[0].set_ylabel("Row (pixels)", fontsize=9, labelpad=3)
    value_cbar_ax = fig.add_subplot(grid[1, :2])
    cbar = fig.colorbar(value_images[0], cax=value_cbar_ax, orientation="horizontal",
                        ticks=[0, 5000, 10000])
    cbar.ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    cbar.ax.tick_params(labelsize=8, length=2.5, pad=2)
    cbar.set_label("Built surface per pixel (m$^2$)", fontsize=9, labelpad=2)
    cbar.ax.get_xticklabels()[-1].set_horizontalalignment("right")
    error_cbar_ax = fig.add_subplot(grid[1, 2])
    error_cbar = fig.colorbar(image, cax=error_cbar_ax, orientation="horizontal", ticks=[-1, 0, 1])
    error_cbar.ax.tick_params(labelsize=8, length=2.5, pad=2)
    error_cbar.set_label("Signed $E/B$", fontsize=9, labelpad=2)
    error_cbar.ax.get_xticklabels()[0].set_horizontalalignment("left")
    # At 600 dpi each full-field panel has at least 512 output pixels; axes,
    # labels, and colorbar text remain vector objects in the PDF.
    save_figure(fig, FIGURES / "field_example", dpi=600)


def development_data():
    attribution = read_json(f"{DEVELOPMENT}/attribution.json")
    checked_file(f"{DEVELOPMENT}/report.json", attribution["report_sha256"])
    ledger = read_json(f"{DEVELOPMENT}/ledger.json")
    data = []
    for epsilon, step in [(100, 20), (1000, 200)]:
        matched = next(v for v in attribution["groups"]
                       if v["epsilon"] == epsilon and v["mode"] == "lossy")
        algorithms = {}
        per_site = []
        for algorithm_id, name in [(1, "proposed"), (0, "row_dp")]:
            entries = [v for v in ledger if v["step"] == step and v["mode"] == "lossy"
                       and v["algorithm_id"] == algorithm_id]
            assert {v["site"] for v in entries} == {"paris", "tokyo", "lagos", "sao_paulo"}
            valid_count = 0
            for entry in entries:
                validate_packet(entry)
                source_path = checked_file(entry["source"], entry["source_sha256"])
                output_path = checked_file(entry["output"], entry["output_sha256"])
                with np.load(source_path, allow_pickle=False) as loaded:
                    mask = loaded["mask"]
                    assert mask.shape == (512, 512)
                    valid_count += int(np.count_nonzero(~mask))
                with np.load(output_path, allow_pickle=False) as loaded:
                    y = loaded["y"]
                    assert np.array_equal(loaded["mask"], mask)
                    assert np.array_equal(y, y.astype(np.int64))
                    assert np.count_nonzero(y[~mask].astype(np.int64) % step) == entry["fine"]
                assert entry["contracts"][str(epsilon)]["status"] == "LEGAL"
                assert sum(entry["body_detail"].values()) == entry["fees"]["body_bytes"]
                per_site.append({"site": entry["site"], "algorithm": name,
                                 "entry_id": entry["id"], "fine_samples": entry["fine"],
                                 "complete_bytes": entry["packet_bytes"]})
            fine = sum(v["fine"] for v in entries)
            paid_bytes = sum(v["packet_bytes"] for v in entries)
            assert fine == matched["totals"][str(algorithm_id)]["fine"]
            assert paid_bytes == matched["totals"][str(algorithm_id)]["packet_bytes"]
            assert valid_count == 4 * 512 * 512
            algorithms[name] = {"fine_samples": fine, "valid_samples": valid_count,
                                "fine_percent": 100 * fine / valid_count,
                                "complete_bytes": paid_bytes,
                                "complete_KiB": paid_bytes / 1024}
        data.append({"epsilon_m2": epsilon, "step_m2": step, "carrier": "matched QF01",
                     "mode": "default lossy", "split": "development only",
                     "algorithms": algorithms, "per_site": per_site,
                     "dp_fine_reduction_percent": 100 * matched["dp_fine_reduction_from_greedy"],
                     "dp_complete_rate_reduction_percent": 100 * matched["dp_reduction_from_greedy"]})
    return data


def plot_precision_rate(data):
    fig, axes = plt.subplots(1, 2, figsize=(6, 2.8))
    fig.subplots_adjust(left=0.11, right=0.985, bottom=0.23, top=0.82, wspace=0.38)
    for panel, ax, metric, ylabel, fmt in [
        ("a", axes[0], "fine_percent", "Fine pixels (%)", "{:.3f}"),
        ("b", axes[1], "complete_KiB", "Complete file size (KiB)", "{:.1f}"),
    ]:
        paired_bars(ax, np.arange(2),
                    [v["algorithms"]["row_dp"][metric] for v in data],
                    [v["algorithms"]["proposed"][metric] for v in data],
                    width=0.3, fmt=fmt)
        ax.set_xticks(np.arange(2), [r"$\epsilon=100$", r"$\epsilon=1{,}000$"])
        ax.set_xlabel("Rectangle-sum budget (m$^2$)", fontsize=9)
        ax.set_ylabel(ylabel)
        ax.text(0.02, 1.03, f"({panel})", transform=ax.transAxes, va="bottom")
    axes[0].set_ylim(0, 0.18)
    axes[0].yaxis.set_major_locator(FixedLocator([0, 0.05, 0.1, 0.15]))
    axes[0].yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    axes[1].set_ylim(0, 870)
    axes[1].set_yticks([0, 200, 400, 600, 800])
    fig.legend(handles=legend_handles(["Exact row search", "RangeRectQuant"]), loc="upper center",
               bbox_to_anchor=(0.53, 1), ncols=2, columnspacing=2, handlelength=1.6)
    fig.text(0.53, 0.035, "Four development windows; same representation", fontsize=8.5,
             ha="center", va="bottom")
    save_figure(fig, FIGURES / "precision_rate")


def write_provenance(numeric_data):
    reference_files = [
        "scientific-figure-making/SKILL.md",
        "scientific-figure-making/references/api.md",
        "scientific-figure-making/references/design-theory.md",
        "scientific-figure-making/references/common-patterns.md",
        "scientific-figure-making/references/demos.md",
        "figure_ImmunoStruct/plot_bars.py", "figure_CellSpliceNet/plot_comparison.py",
        "figure_RNAGenScape/plot_comparison.py", "figure_ophthal_review/plot_composition.py",
        "LICENSE",
    ]
    references = {p: sha256(REFERENCE / p) for p in reference_files}
    outputs = {p.relative_to(ROOT).as_posix(): {"sha256": sha256(p), "bytes": p.stat().st_size}
               for name in ["heldout_rates", "field_example", "precision_rate"]
               for suffix in ["pdf", "png"] if (p := FIGURES / f"{name}.{suffix}").exists()}
    scripts = {p.relative_to(ROOT).as_posix(): sha256(p)
               for p in [Path(__file__), PLOTTING / "paper_plot_style.py"]}
    import matplotlib
    manifest = {
        "status": "GENERATED_AND_NUMERICALLY_CHECKED",
        "scope": "Saved-data plotting; no optimization, encoding, decoding, acquisition, or Git operations",
        "review_route": {"requested_skill_model": "gpt-5.5 (unavailable)",
                         "actual": "inherited Codex gpt-6.1-sol xhigh fallback, delegated plotting/quality workflow",
                         "visual_review": "view_image review is recorded in FIGURE_PROVENANCE.md after generation"},
        "runtime": {"python": sys.executable, "numpy": np.__version__, "matplotlib": matplotlib.__version__},
        "reference": {"repository": "https://github.com/ChenLiu-1996/figures4papers",
                      "author": "Chen Liu (ChenLiu-1996)", "commit": REFERENCE_COMMIT,
                      "license": "CC BY-NC 4.0", "files_sha256": references},
        "dimensions_inches": {"heldout_rates": [6, 2.8], "field_example": [6, 2.95],
                              "precision_rate": [6, 2.8]},
        "png_dpi": {"heldout_rates": 300, "field_example": 600, "precision_rate": 300},
        "numeric_data": numeric_data, "inputs": dict(sorted(INPUTS.items())),
        "scripts_sha256": scripts, "outputs": outputs,
    }
    (PLOTTING / "figure_data.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", choices=["all", "heldout_rates", "field_example", "precision_rate"],
                        default="all")
    args = parser.parse_args()
    apply_publication_style()
    # Validate every input group even on a single-figure rebuild, so the exact
    # numerical manifest is complete and not silently replaced with a subset.
    heldout = heldout_data()
    source, output, prefix, field_stats = field_data()
    development = development_data()
    if args.figure in {"all", "heldout_rates"}:
        plot_heldout_rates(heldout)
    if args.figure in {"all", "field_example"}:
        plot_field_example(source, output, prefix)
    if args.figure in {"all", "precision_rate"}:
        plot_precision_rate(development)
    write_provenance({"heldout_rates": heldout, "field_example": field_stats,
                      "precision_rate": development})
    print(json.dumps({"status": "PASS_NUMERIC_CHECKS", "generated": args.figure,
                      "input_files_bound": len(INPUTS), "figure_directory": str(FIGURES)}))


if __name__ == "__main__":
    main()
