"""Bind the reader-facing three-panel summary to every saved measurement."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper/plotting"))
import reference_grids as grids
from make_core_mechanism_figure import core_mechanism, empirical_cdf, step_summary
from paper_plot_style import apply_publication_style, plt


class CoreMechanismFigure(unittest.TestCase):
    def setUp(self):
        apply_publication_style()

    def tearDown(self):
        plt.close("all")

    def test_empirical_distribution_retains_losses_and_ties(self):
        x, percentage = empirical_cdf([3, -2, 3, 1])
        np.testing.assert_array_equal(x, [-2, 1, 3, 3])
        np.testing.assert_array_equal(percentage, [25, 50, 75, 100])
        for invalid in ([], [float("nan")], [float("inf")], [[1, 2]]):
            with self.subTest(sample=invalid), self.assertRaises(ValueError):
                empirical_cdf(invalid)

    def test_distribution_contains_all_forty_identical_field_comparisons(self):
        figure, displayed = core_mechanism()
        self.assertEqual(len(figure.axes), 3)
        sites, rows = grids.representations()
        for line, budget in zip(figure.axes[0].lines, (100, 1000)):
            expected = [100 * (1 - rows[site, budget, "split"]["packet_bytes"] /
                              rows[site, budget, "direct"]["packet_bytes"])
                        for site in sites]
            sample = displayed["coding_gain"][str(budget)]
            self.assertEqual(sample["sites"], sites)
            self.assertEqual(sample["sample_count"], 40)
            np.testing.assert_allclose(sample["gain_percent"], expected)
            np.testing.assert_allclose(line.get_xdata()[1:-1], np.sort(expected))
            np.testing.assert_array_equal(line.get_ydata()[1:-1], np.arange(1, 41) * 2.5)
            self.assertEqual(line.get_drawstyle(), "steps-post")

    def test_step_medians_and_observed_ranges_use_all_cities_and_divisors(self):
        rows = grids.step_rows()
        figure, displayed = core_mechanism()
        for ax, metric in zip(figure.axes[1:], ("rate", "fine")):
            curves = [line for line in ax.lines if line.get_marker() == "v"]
            self.assertEqual(len(curves), 2)
            for curve, budget in zip(curves, (100, 1000)):
                summary = step_summary(rows, budget, metric)
                self.assertEqual(summary, displayed["step"][f"{budget}/{metric}"])
                expected = np.array([
                    [rows[site, budget, divisor]["packet_bytes"] * 8 / 512**2
                     if metric == "rate" else
                     rows[site, budget, divisor]["geometry"]["fine_fraction"] * 100
                     for divisor in grids.DIVISORS] for site in grids.SITES])
                self.assertEqual(expected.shape, (4, 8))
                np.testing.assert_allclose(summary["series"], expected)
                np.testing.assert_allclose(summary["median"], np.median(expected, axis=0))
                np.testing.assert_allclose(summary["minimum"], expected.min(axis=0))
                np.testing.assert_allclose(summary["maximum"], expected.max(axis=0))
                np.testing.assert_allclose(curve.get_ydata(), summary["median"])
            self.assertEqual(len(ax.collections), 2)
        with self.assertRaises(ValueError):
            step_summary(rows, 100, "unknown")

    def test_shared_legend_enclosed_axes_and_readable_fonts(self):
        figure, _ = core_mechanism()
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        self.assertEqual(len(figure.legends), 1)
        legend = figure.legends[0]
        self.assertEqual([t.get_text() for t in legend.texts], ["Budget 100 m²", "Budget 1000 m²"])
        self.assertTrue(legend.get_frame_on())
        box = legend.get_window_extent(renderer)
        for ax in figure.axes:
            self.assertTrue(all(spine.get_visible() for spine in ax.spines.values()))
            self.assertGreaterEqual(ax.xaxis.label.get_fontsize(), 9)
            self.assertGreaterEqual(ax.yaxis.label.get_fontsize(), 9)
            for label in [ax.xaxis.label, ax.yaxis.label, *ax.texts,
                          *ax.get_xticklabels(), *ax.get_yticklabels()]:
                if label.get_visible() and label.get_text():
                    self.assertFalse(box.overlaps(label.get_window_extent(renderer)), label.get_text())

    def test_provenance_matches_sources_outputs_and_exact_displayed_values(self):
        receipt = json.loads((ROOT / "paper/figures/research/provenance_core_mechanism.json").read_text())
        for group in ("inputs", "sources", "outputs"):
            for name, digest in receipt[group].items():
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        _, displayed = core_mechanism()
        self.assertEqual(receipt["displayed"], displayed)
        self.assertEqual(receipt["layout"]["panels"], [1, 3])
        self.assertFalse(receipt["new_experiments"])
        self.assertFalse(receipt["uncertainty_estimate"])


if __name__ == "__main__":
    unittest.main()
