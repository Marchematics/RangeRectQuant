"""Build the seven-page, four-column figure collection from saved experiments."""
from datetime import datetime, timezone
from matplotlib.backends.backend_pdf import PdfPages

from paper_plot_style import apply_publication_style, save_figure
import reference_grids as grids


PAGES = ["line_grid_fullpage", "coding_city_fullpage", "step_fullpage",
         "closest_fullpage", "water", "scaling", "mechanism"]


def main():
    apply_publication_style()
    destination = grids.OUT / "experiment_atlas.pdf"
    outputs = [destination]
    fixed_date = datetime(2026, 10, 1, tzinfo=timezone.utc)
    with PdfPages(destination, metadata={"Title": "RangeRectQuant: saved-data experimental figures",
                                         "Creator": "RangeRectQuant saved-data plotting",
                                         "CreationDate": fixed_date, "ModDate": fixed_date}) as pdf:
        for name in PAGES:
            figure = getattr(grids, name)()
            stem = grids.OUT / name
            # The individual export performs the fixed-canvas clipping check.
            save_figure(figure, stem)
            pdf.savefig(figure, dpi=300)
            outputs.extend([stem.with_suffix(".pdf"), stem.with_suffix(".png")])
    grids.remember("atlas_pages", PAGES)
    grids.write_provenance(grids.OUT / "provenance_experiment_atlas.json", outputs)


if __name__ == "__main__":
    main()
