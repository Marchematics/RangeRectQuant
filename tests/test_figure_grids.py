"""Guard saved-data fidelity and the user-requested four-column figure design."""
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"paper/plotting"))
import reference_grids as grids
from paper_plot_style import apply_publication_style, plt
from make_compact_review_figure import review_mechanism_compact
from make_coordination_example import coordination_example, bradley_hand_font


class FigureGrids(unittest.TestCase):
    def setUp(self):
        apply_publication_style()

    def tearDown(self):
        plt.close("all")

    def test_opening_example_uses_bradley_hand_without_changing_its_values(self):
        try:
            bradley_hand_font()
        except ValueError as error:
            if 'Failed to find font' not in str(error):
                raise
            self.skipTest('Install Bradley Hand to regenerate Figure 1')
        figure = coordination_example()
        report = json.loads((ROOT/"results/coordination_example_20261007/report.json").read_text())
        self.assertEqual(len(figure.axes), 4)
        np.testing.assert_allclose(figure.get_size_inches(), [6, 1.15])
        for ax, key in zip(figure.axes, ("x", "y", "error", "prefix")):
            values = np.array(report['example'][key]).ravel()
            expected = [f'{int(v):+d}' if key == 'error' else str(int(v)) for v in values]
            self.assertEqual([t.get_text() for t in ax.texts], expected)
            for text in [ax.title, *ax.texts]:
                self.assertEqual(text.get_fontproperties().get_name(), 'Bradley Hand')
                self.assertEqual(text.get_fontproperties().get_file(), bradley_hand_font().get_file())
        self.assertEqual(plt.rcParams['font.family'], ['serif'])

    def test_frontier_preserves_missing_coverage_and_water_crossover(self):
        figure = grids.frontier()
        self.assertEqual(len(figure.axes), 4)
        report = json.loads((ROOT/"results/expanded_frontier_20261002/report.json").read_text())
        for ax, size in zip(figure.axes[:3], [256, 512, 1024]):
            rows = sorted([r for r in report["frontier"] if r["size"] == size], key=lambda r: r["epsilon"])
            for line, method in zip(ax.lines, grids.METHODS):
                expected = [np.nan if r["bpp"][method] is None else r["bpp"][method] for r in rows]
                np.testing.assert_allclose(line.get_ydata(), expected, equal_nan=True)
                self.assertEqual(line.get_marker(), "v")
            self.assertTrue(all(s.get_visible() for s in ax.spines.values()))
        main, reference = figure.axes[3].lines
        self.assertTrue(np.all(main.get_ydata()[:2] > reference.get_ydata()[:2]))
        self.assertGreater(main.get_ydata()[0], main.get_ydata()[-1])

    def test_all_forty_matched_fields_appear_without_reordering_by_result(self):
        sites, rows = grids.representations()
        self.assertEqual(len(sites), 40)
        self.assertEqual(sites, sorted(sites))
        figure = grids.review_mechanism()
        self.assertEqual(len(figure.axes), 8)
        self.assertEqual(sum(len(ax.patches) for ax in figure.axes[:4]), 80)
        for i, ax in enumerate(figure.axes[:4]):
            self.assertEqual(len(ax.get_xticklabels()), 10)
            for bars, e in zip(ax.containers, [100, 1000]):
                expected = [100*(1-rows[s, e, "split"]["packet_bytes"]/rows[s, e, "direct"]["packet_bytes"])
                            for s in sites[i*10:(i+1)*10]]
                np.testing.assert_allclose([bar.get_height() for bar in bars], expected)

    def test_step_curves_show_each_holdout_and_all_eight_divisors(self):
        figure = grids.review_mechanism()
        rows = grids.step_rows()
        self.assertEqual(len(rows), 64)
        for ax in figure.axes[4:]:
            lines = [line for line in ax.lines if line.get_marker() == "v"]
            self.assertEqual(len(lines), 4)
            self.assertTrue(all(len(line.get_ydata()) == 8 for line in lines))

    def test_spatial_maps_match_the_saved_cairo_field(self):
        with np.load(ROOT/"results/closest_mechanism_20261002/mechanism_example.npz", allow_pickle=False) as data:
            x, y, widths, protected = [data[key] for key in ("x", "y", "widths", "protected")]
        prefix = (y-x).cumsum(0).cumsum(1)
        fine = (y % 200 != 0) & ~protected
        self.assertEqual(int(fine.sum()), 572)
        self.assertLessEqual(int(np.abs(prefix).max()), 250)
        self.assertTrue(np.all(widths[fine] < 200))
        figure = grids.mechanism()
        self.assertEqual(len(figure.axes), 8)  # Four maps and four colorbars.
        for ax, expected in zip(figure.axes[:4], [x, prefix, widths, fine.astype(int)]):
            self.assertEqual(len(ax.images), 1)
            np.testing.assert_array_equal(ax.images[0].get_array(), expected)
            self.assertEqual(ax.get_aspect(), 1.0)

    def test_main_text_places_the_spatial_example_after_feasibility(self):
        method = (ROOT/"paper/sections/method.tex").read_text()
        figure = r"\includegraphics[width=\linewidth]{figures/research/mechanism.pdf}"
        self.assertIn(figure, method)
        self.assertIn(r"\label{fig:spatial}", method)
        self.assertIn(r"\ref{fig:spatial}", method)
        self.assertLess(method.index(r"\label{eq:fine-count}"), method.index(figure))
        self.assertLess(method.index(r"\label{eq:finite-code}"), method.index(figure))

    def test_compact_coding_grid_preserves_values_labels_and_font_sizes(self):
        full, compact = grids.review_mechanism(), review_mechanism_compact()
        self.assertEqual(len(compact.axes), 8)
        for before, after in zip(full.axes, compact.axes):
            self.assertEqual(len(before.patches), len(after.patches))
            for old, new in zip(before.patches, after.patches):
                self.assertEqual(old.get_height(), new.get_height())
                self.assertEqual(old.get_x(), new.get_x())
            for old, new in zip(before.lines, after.lines):
                np.testing.assert_array_equal(old.get_xdata(), new.get_xdata())
                np.testing.assert_array_equal(old.get_ydata(), new.get_ydata())
            self.assertEqual([t.get_text() for t in before.get_xticklabels()],
                             [t.get_text() for t in after.get_xticklabels()])
            self.assertEqual(before.title.get_fontsize(), after.title.get_fontsize())
            self.assertEqual(before.get_ylabel(), after.get_ylabel())
            self.assertEqual([t.get_fontsize() for t in before.get_xticklabels()],
                             [t.get_fontsize() for t in after.get_xticklabels()])
        evaluation = (ROOT/"paper/sections/evaluation.tex").read_text()
        self.assertTrue((ROOT/"paper/figures/research/review_mechanism_compact.pdf").is_file())
        self.assertIn("figures/research/review_mechanism_compact.pdf", evaluation)
        self.assertNotIn("figures/research/core_mechanism.pdf", evaluation)
        self.assertIn("(a--d)", evaluation)
        self.assertIn("(e--h)", evaluation)

    def test_coding_gain_label_is_explicit_and_fits_the_fixed_canvas(self):
        figure = review_mechanism_compact()
        figure.canvas.draw()
        label = figure.axes[0].yaxis.label
        self.assertEqual(label.get_text(), 'Quotient–remainder\ncoding gain (%)')
        box = label.get_window_extent(figure.canvas.get_renderer())
        self.assertGreaterEqual(box.x0, 0)
        self.assertGreaterEqual(box.y0, 0)
        self.assertLessEqual(box.x1, figure.bbox.width)
        self.assertLessEqual(box.y1, figure.bbox.height)

    def test_closest_comparison_shows_every_city_method_and_budget(self):
        figure = grids.closest_fullpage()
        self.assertEqual(len(figure.axes), 8)
        self.assertEqual(sum(len(ax.patches) for ax in figure.axes), 112)
        self.assertEqual(sum(len(line.get_xdata()) for ax in figure.axes[:4]
                             for line in ax.lines if line.get_marker() == "x"), 48)
        for ax in figure.axes[:4]:
            for patch in ax.patches:
                self.assertLessEqual(patch.get_height()*1.2, ax.get_ylim()[1])

    def test_scaling_never_invents_timeout_or_unrecorded_core_measurements(self):
        figure = grids.scaling()
        self.assertEqual(len(figure.axes), 8)
        self.assertEqual(len(figure.axes[0].lines), 2)
        for ax in figure.axes[4:]:
            exact = next(line for line in ax.lines if line.get_label() == "Exact row search")
            self.assertEqual(list(exact.get_xdata()), [256, 512, 1024, 2048])

    def test_shared_legend_boxes_do_not_cover_plot_labels(self):
        for build in [grids.frontier, grids.review_mechanism_main, grids.line_grid_fullpage,
                      review_mechanism_compact]:
            with self.subTest(figure=build.__name__):
                figure = build(); figure.canvas.draw(); renderer = figure.canvas.get_renderer()
                for legend in figure.legends:
                    box = legend.get_window_extent(renderer)
                    for ax in figure.axes:
                        # Axis.draw filters out-of-view ticks although their
                        # underlying Text objects still have visible=True.
                        xticks = [t.label1 for t in ax.xaxis.get_major_ticks()
                                  if min(ax.get_xlim()) <= t.get_loc() <= max(ax.get_xlim())]
                        yticks = [t.label1 for t in ax.yaxis.get_major_ticks()
                                  if min(ax.get_ylim()) <= t.get_loc() <= max(ax.get_ylim())]
                        for text in [ax.title, ax.xaxis.label, ax.yaxis.label, *xticks, *yticks]:
                            if text.get_visible() and text.get_text():
                                self.assertFalse(box.overlaps(text.get_window_extent(renderer)), text.get_text())


if __name__ == "__main__":
    unittest.main()
