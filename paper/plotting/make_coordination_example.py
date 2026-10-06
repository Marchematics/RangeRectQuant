"""Vector 1x4 analytical illustration with Bradley Hand labels and cell values."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Rectangle

from paper_plot_style import apply_publication_style, plt, save_figure


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'results/coordination_example_20261007/report.json'
OUT = ROOT / 'paper/figures/research/coordination_example'


def bradley_hand_font():
    # Resolve the requested font explicitly; a silent serif fallback changes the figure.
    override = os.environ.get('BRADLEY_HAND_FONT')
    path = Path(override) if override else Path(font_manager.findfont(
        font_manager.FontProperties(family='Bradley Hand', weight='bold'),
        fallback_to_default=False))
    font = font_manager.FontProperties(fname=path)
    if font.get_name() != 'Bradley Hand':
        raise ValueError('BRADLEY_HAND_FONT must identify a Bradley Hand font file')
    return font


def coordination_example():
    data = json.loads(REPORT.read_text())['example']
    font = bradley_hand_font()
    figure = plt.figure(figsize=(6, 1.15))
    colors = {-1: '#BCD6E7', 0: '#F6F6F6', 1: '#E0E0E0', 2: '#FCB89B'}
    for col, (key, title) in enumerate(zip(('x', 'y', 'error', 'prefix'),
                                          ('Source', 'Quantized values', 'Pixel errors', 'Prefix errors'))):
        values = np.array(data[key], dtype=np.int64)
        ax = figure.add_axes([.045 + .24 * col, .05, .19, .80])
        for i, j in np.ndindex(values.shape):
            value = int(values[i, j])
            face = '#FCB89B' if key == 'error' and value == 1 else colors[value]
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=face,
                                   edgecolor='#777777', linewidth=.45))
            label = f'{value:+d}' if key == 'error' else str(value)
            ax.text(j + .5, i + .5, label, ha='center', va='center', fontsize=10,
                    fontproperties=font)
        ax.set_xlim(0, values.shape[1]); ax.set_ylim(values.shape[0], 0)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_linewidth(.55)
        ax.set_title(f'({chr(97 + col)}) {title}', fontsize=8.5, pad=4,
                     fontproperties=font)
    return figure


if __name__ == '__main__':
    apply_publication_style()
    save_figure(coordination_example(), OUT)
    paths = (REPORT, Path(__file__).resolve(),
             ROOT/'paper/plotting/paper_plot_style.py',
             ROOT/'experiments/verify_coordination_example.py')
    receipt = {
        'status': 'PASS_SAVED_ANALYTICAL_DATA_FOUR_COLUMN_FIGURE',
        'analytical_example': True, 'empirical_rate_comparison': False,
        'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'outputs': {str(OUT.with_suffix(s).relative_to(ROOT)):
                    hashlib.sha256(OUT.with_suffix(s).read_bytes()).hexdigest() for s in ('.pdf', '.png')},
        'layout': {'inches': [6, 1.15], 'panels': [1, 4], 'numbered_cells': True},
        'font': {'family': 'Bradley Hand',
                 'file': str(bradley_hand_font().get_file()),
                 'sha256': hashlib.sha256(Path(bradley_hand_font().get_file()).read_bytes()).hexdigest()},
        'reference_repo': 'https://github.com/ChenLiu-1996/figures4papers',
        'reference_commit': 'f0bb7559abe90f5e1828797126d4d133c1bd47d7'}
    OUT.with_name('provenance_coordination_example.json').write_text(json.dumps(receipt, indent=2) + '\n')
