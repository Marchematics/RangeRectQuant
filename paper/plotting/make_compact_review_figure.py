"""Keep all coding/step panels at their original font size on a shorter canvas."""
import hashlib
import json
from pathlib import Path

from paper_plot_style import apply_publication_style, save_figure, shared_legend, plt
import reference_grids as grids


def review_mechanism_compact():
    fig = plt.figure(figsize=(6, 3.6))
    # City names and the two shared legends retain separate physical bands.
    top = [fig.add_axes([.085 + .233*i, .66, .20, .225]) for i in range(4)]
    bottom = [fig.add_axes([.085 + .233*i, .13, .19, .23]) for i in range(4)]
    shared_legend(fig, grids.gain_panels(top), ncol=2, anchor=(.5, .995))
    shared_legend(fig, grids.step_panels(bottom), ncol=4, anchor=(.5, .50))
    return fig


def main():
    apply_publication_style()
    destination = grids.OUT / "review_mechanism_compact"
    save_figure(review_mechanism_compact(), destination)
    receipt = grids.OUT / "provenance_review_mechanism_compact.json"
    grids.write_provenance(receipt, [destination.with_suffix(s) for s in (".pdf", ".png")])
    data = json.loads(receipt.read_text())
    source = Path(__file__).resolve()
    data["sources"][str(source.relative_to(grids.ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    data["layout"] = {"inches": [6, 3.6], "panels": [2, 4], "font_sizes_unchanged": True}
    receipt.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
