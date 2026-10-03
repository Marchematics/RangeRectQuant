# Saved-data four-column figures

From the repository root:

```sh
../LinewiseROI/.venv/bin/python paper/plotting/make_research_figures.py \
  frontier mechanism closest protected scaling water closest_fullpage line_grid_fullpage
../LinewiseROI/.venv/bin/python paper/plotting/make_review_figure.py
../LinewiseROI/.venv/bin/python paper/plotting/make_compact_review_figure.py
../LinewiseROI/.venv/bin/python paper/plotting/make_experiment_atlas.py
```

The scripts read saved reports, per-file JSONs and one saved field array only.
They never run an experiment, optimizer, acquisition, decoder or GPU.
`reference_grids.py` binds data to panels. Receipts record every input/script/
output hash and exact displayed values. Missing coverage, tight-budget water
losses and the exact-search timeout are retained. No uncertainty is invented.

The ten-page article keeps Figure 1, then shows a 1×4 spatial precision example
at the method/evaluation boundary, a 1×4 closest-construction comparison,
a 1×4 frontier and a 2×4 coding/step grid. The spatial example uses the original
`mechanism.pdf` directly. The coding/step grid uses a 6×3.6-inch canvas with
unchanged font sizes, values and labels; its previous taller version is retained.
Forty city names replace the
former three-object bar axis. Locations are alphabetical, ten per panel, with
both budgets. The seven-page `../figures/research/experiment_atlas.pdf` collects
68 panels in 4×4, 2×4 and 1×4 layouts. Page captions and scope are in
`../notes/EXPERIMENT_ATLAS_GUIDE.md`.

## Reference and modifications

Code/layout conventions adapt Chen Liu (ChenLiu-1996),
[figures4papers](https://github.com/ChenLiu-1996/figures4papers), commit
`f0bb7559abe90f5e1828797126d4d133c1bd47d7`, under CC BY-NC 4.0.
Inspected scripts include `figure_VIGIL/plot_ablation.py`,
`figure_ophthal_review/plot_trend.py`, and the comparison/bar scripts named in
`paper_plot_style.py`. `LICENSE.figures4papers.txt` retains the license.

The supplied references set Times serif type, all four spines, pastel thin
curves, downward triangles, dotted grids and boxed shared legends. Six-inch
canvases preserve printed font sizes. Text, ticks, curves and bars are vector
objects; field maps are raster layers. Modifications include physical units,
complete-file fees, all-location bars, explicit timing scope and fixed-canvas
clipping checks. No reference numerical data are reused.

## Historical plots

`make_figures.py` and `figure_data.json` retain the earlier four-location study.
Use `--figure heldout_rates`, `field_example` or `precision_rate` for an
individual historical view. Image checkpoints and old provenance remain;
they are not the current article/atlas. Re-running historical scripts uses
the shared current style. Existing LinewiseROI Python supplies Matplotlib
and NumPy without installation.
