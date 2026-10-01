# RangeRectQuant DCC manuscript

`main.tex` and `sections/` are the canonical, editable article. `main.pdf` is its
compiled draft. The official DCC class and bibliography style are retained
unchanged. Figures are derived from saved experimental outputs, using the
requested figures4papers style and figure types. There is no separate
supplement required to read or compile the article.

## Build

From this directory, with an existing LaTeX installation:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The saved figure PDFs and verified bibliography are included. Plot regeneration
requires NumPy/Matplotlib and the corresponding repository evidence files, not
new experiments; see `plotting/README.md`. `make figures PYTHON=/path/to/python`
selects an existing environment. The textual/evidence check is
`python3 notes/check_manuscript.py` from this directory, inside the full research
repository. A paper-only source archive compiles without the repository data;
its evidence checker and plot regeneration need the full repository.

## Draft status

DCC author instructions require visible author names and affiliations. These
have been requested and are not fabricated. Fill the `\author{}` block in
`main.tex` before submission. This is a complete-body research draft, not a
submitted or author-complete manuscript. The repository remains private.

The article reports the specified complete-size comparison and geographic
holdout result. It does not claim a best-paper award or field-wide codec SOTA.
Scientific evidence and verification: `notes/PAPER_HANDOFF.md`,
`notes/LITERATURE_NOTES.md`, `notes/FIGURE_PROVENANCE.md`, and the research
repository's saved reports. No unpublished supplemental dependency or public
code-release promise is added to the manuscript.

## Plotting attribution

Chen Liu, figures4papers, commit f0bb7559abe90f5e1828797126d4d133c1bd47d7:
https://github.com/ChenLiu-1996/figures4papers . Adapted plotting material retains
CC BY-NC4.0 attribution; the license is preserved in
`plotting/LICENSE.figures4papers.txt`. Source-data and scientific-code rights
are not relicensed by this attribution. The official template provenance is
recorded in `template/PROVENANCE.md`.
