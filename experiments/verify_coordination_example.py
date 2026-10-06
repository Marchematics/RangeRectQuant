"""Check an analytical coordination example, not an empirical rate comparison."""
import json
from operator import index
from pathlib import Path

import numpy as np

from controls.viable_greedy import reconstruct


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'results/coordination_example_20261007/report.json'


def rectangle_count(height, width):
    height, width = index(height), index(width)
    if height < 1 or width < 1:
        raise ValueError('A field must have positive dimensions')
    return height * (height + 1) * width * (width + 1) // 4


def checkerboard_case(height, width):
    rectangle_count(height, width)
    x = np.ones((height, width), dtype=np.int64)
    error = 2 * (np.indices(x.shape).sum(axis=0) % 2) - 1
    y = x + error
    prefix = error.cumsum(axis=0).cumsum(axis=1)
    return x, y, error, prefix


def rectangular_errors(error):
    """Independent four-loop enumeration for the small analytical fields."""
    height, width = error.shape
    prefix = np.pad(error.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    return [int(prefix[b, d] - prefix[a, d] - prefix[b, c] + prefix[a, c])
            for a in range(height) for b in range(a + 1, height + 1)
            for c in range(width) for d in range(c + 1, width + 1)]


def verify():
    fields = rectangles = strict_separations = 0
    for height in range(1, 13):
        for width in range(1, 13):
            x, y, error, prefix = checkerboard_case(height, width)
            measured = rectangular_errors(error)
            actual, detail = reconstruct(x, 1, 2, 2, np.zeros(x.shape, bool))
            np.testing.assert_array_equal(actual, y)
            assert detail['off_lattice'] == 0
            assert detail['changed'] == x.size
            assert int(np.abs(prefix).max()) == 1
            assert max(abs(v) for v in measured) == 1
            assert len(measured) == rectangle_count(height, width)
            if x.size > 4:
                # At tolerance >= 1, independent limits permit this source-
                # specific witness, whose whole-field error exceeds budget 4.
                independent_output = np.full(x.shape, 2, dtype=np.int64)
                assert int((independent_output - x).sum()) > 4
                strict_separations += 1
            fields += 1
            rectangles += len(measured)

    x, y, error, prefix = checkerboard_case(3, 4)
    errors = rectangular_errors(error)
    return {
        'status': 'PASS_ANALYTICAL_SEPARATION_AND_MAIN_CONSTRUCTION',
        'analytical_example': True, 'empirical_rate_comparison': False,
        'checked_fields': fields, 'checked_rectangles': rectangles,
        'source_specific_independent_witnesses': strict_separations,
        'constructor': {'band': 1, 'step': 2, 'cap': 2, 'budget': 4,
                        'protected_samples': 0, 'matches_checkerboard': True},
        'example': {'x': x.tolist(), 'y': y.tolist(), 'error': error.tolist(),
                    'prefix': prefix.tolist(), 'changed_pixels': int(x.size),
                    'max_abs_rectangle_error': max(abs(v) for v in errors),
                    'rectangle_count': len(errors)},
        'query_counts': {str(n): rectangle_count(n, n) for n in (256, 512, 1024)},
        'scope': 'Independent certification versus coordinated quantization; no file-rate separation claimed.'}


if __name__ == '__main__':
    report = verify()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'checked_fields',
                     'checked_rectangles', 'source_specific_independent_witnesses')}))
