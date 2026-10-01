# Saved-data manuscript figures

Run from any directory:

```sh
/Users/nathmath/dcc/LinewiseROI/.venv/bin/python \
  /Users/nathmath/dcc/RangeRectQuant/paper/plotting/make_figures.py
```

Use `--figure heldout_rates`, `--figure field_example`, or `--figure precision_rate`
for an individual export. No codec, optimizer, decoder, acquisition, or Git
operation is called. The bundled Python has no Matplotlib; the existing
LinewiseROI environment supplies NumPy and Matplotlib without installation.

`figure_data.json` records exact plotted numbers, definitions, dimensions,
original input SHA256 bindings, complete packet fees, saved-array checks,
script hashes, and PDF/PNG hashes. `../notes/FIGURE_PROVENANCE.md` records
interpretation, attribution, and delegated visual review.

## Attribution and modifications

Plotting style and layout patterns are adapted from **Chen Liu (ChenLiu-1996),
[figures4papers](https://github.com/ChenLiu-1996/figures4papers)**, commit
`f0bb7559abe90f5e1828797126d4d133c1bd47d7`, under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
The adapted conventions are minimal spines, Arial/Helvetica-like sans typography,
the `#0F4D92` proposed-method palette and pink comparator palette, direct bar
annotations, separated legends, and normalized heatmap/colorbar encoding.
Actual inspected scripts are enumerated in the provenance manifest.

Modifications: paper-sized six-inch panels instead of the reference's large
canvases; physical-unit axis labels; complete-byte rates; fine percentage with
an explicit valid-sample denominator; shared physical-value normalization;
symmetric signed prefix normalization; and deterministic PDF/PNG exports.
No reference experiment data or figures are reused. This attribution applies
to the adapted plotting material, not to the scientific source dataset.
