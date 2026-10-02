"""Render saved-data research plots as reference-faithful four-column grids.

All computations and source bindings live in reference_grids.py. The method
illustration (Figure 1) is independent and is never regenerated here.
"""
import argparse
from paper_plot_style import apply_publication_style, save_figure
import reference_grids as grids

CHOICES = ["frontier", "closest", "mechanism", "protected", "scaling", "water",
           "closest_fullpage", "line_grid_fullpage"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("figures", nargs="+", choices=CHOICES)
    args = parser.parse_args()
    apply_publication_style()
    outputs = []
    for name in args.figures:
        destination = grids.OUT / name
        save_figure(getattr(grids, name)(), destination)
        outputs.extend([destination.with_suffix(".pdf"), destination.with_suffix(".png")])
    grids.write_provenance(grids.OUT / ("provenance_" + "_".join(args.figures) + ".json"), outputs)


if __name__ == "__main__":
    main()
