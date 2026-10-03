# RangeRectQuant

RangeRectQuant compresses bounded integer fields while preserving designated
samples and one absolute error budget for every rectangular sum. The repository
contains the implementation, processed data, saved results, figures, and DCC paper.

## Paper and artifacts

- **Paper:** [PDF](paper/main.pdf) · [LaTeX source](paper/main.tex).
- **Figure 1:** method overview in `paper/figures/`.
- **Figure 2:** Cairo spatial example — [PDF](paper/figures/research/mechanism.pdf),
  [PNG](paper/figures/research/mechanism.png), and
  [source arrays](results/closest_mechanism_20261002/mechanism_example.npz).
  The arrays contain source `x`, reconstruction `y`, allowed-state counts
  `widths`, and the `protected` mask; budget 1000 m², step 200 m².
- **Experimental plot collection:** [experiment_atlas.pdf](paper/figures/research/experiment_atlas.pdf).
- **Figures 3–5:** `paper/figures/research/`; plotting code and
  input/output checksums are in `paper/plotting/` and the figure provenance files.
- **Method code:** `src/`; experiment and control code: `experiments/`, `controls/`.
- **Data and results:** `data/`, `results/`. Acquisition and reproduction details:
  [guide](docs/EXPANDED_REPRODUCIBILITY_20261002.md).
- **Complete paid files and acquisition snapshots:**
  [expanded release](https://github.com/Marchematics/RangeRectQuant/releases/tag/expanded-study-20261002-af0b24f).

## Reproduce Figure 2

From the repository root, with Python 3.12 and the research dependencies:

```sh
python -m pip install -r requirements-research.txt
python paper/plotting/make_research_figures.py mechanism
```

This reads the saved arrays without running an experiment. Detailed figure
commands are in [the plotting README](paper/plotting/README.md).
The article has ten pages, five figures, twenty experimental panels, and 22
references. All 51 unit tests pass; dated checks are in `paper/notes/`.

The repository and release currently require authorized GitHub access.
Upstream data rights are retained in the acquisition records. Plot styling
adapts [figures4papers](https://github.com/ChenLiu-1996/figures4papers);
its CC BY-NC 4.0 license and attribution are in `paper/plotting/`.
