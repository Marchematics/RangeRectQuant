"""Matched-field coding and precision grids; every plotted value is saved data."""
from paper_plot_style import apply_publication_style, save_figure
import reference_grids as grids


def main():
    apply_publication_style()
    outputs = []
    for name in ("review_mechanism", "review_mechanism_main", "coding_city_fullpage", "step_fullpage"):
        destination = grids.OUT / name
        save_figure(getattr(grids, name)(), destination)
        outputs.extend([destination.with_suffix(".pdf"), destination.with_suffix(".png")])
    grids.write_provenance(grids.OUT / "provenance_review_mechanism.json", outputs)


if __name__ == "__main__":
    main()
