import itertools
import tempfile
import subprocess
import os
import sys
import unittest
from pathlib import Path
import numpy as np
from controls.viable_greedy import row_greedy, reconstruct
from controls.field_packet import encode, decode
from range_rect_quant.corridor import _row_fast


class ViableGreedyTests(unittest.TestCase):
    def test_1000_suffix_safe_rows_and_dp_lower_bound(self):
        rng = np.random.default_rng(20261011)
        for _ in range(1000):
            w = int(rng.integers(1, 15)); b = int(rng.integers(0, 8))
            q = int(rng.integers(1, 20)); cap = int(rng.integers(0, 25))
            x = rng.integers(0, cap+1, w, dtype=np.int64)
            up = rng.integers(-b, b+1, w, dtype=np.int64)
            protected = rng.random(w) < .3
            y, states, fine, energy = row_greedy(x, up, b, q, cap, protected)
            np.testing.assert_array_equal(states, up+(y-x).cumsum())
            np.testing.assert_array_equal(y[protected], x[protected])
            self.assertTrue(np.all((y >= 0) & (y <= cap)))
            self.assertLessEqual(np.abs(states).max(), b)
            _, _, optimum, _ = _row_fast(x, up, b, q, cap, protected)
            self.assertGreaterEqual(fine, optimum)
            self.assertEqual(fine, np.count_nonzero(y % q))
            self.assertEqual(energy, (states*states).sum())

    def test_1000_independent_brute_greedy_choices(self):
        rng = np.random.default_rng(20261012)
        for _ in range(1000):
            w = int(rng.integers(1, 5)); b = int(rng.integers(0, 4))
            q = int(rng.integers(1, 7)); cap = int(rng.integers(0, 6))
            x = rng.integers(0, cap+1, w, dtype=np.int64)
            up = rng.integers(-b, b+1, w, dtype=np.int64)
            protected = rng.random(w) < .3
            possible = []
            for values in itertools.product(*[([int(x[j])] if protected[j] else range(cap+1)) for j in range(w)]):
                states = up+(np.array(values)-x).cumsum()
                if np.abs(states).max() <= b:
                    possible.append((values, states))
            y, _, _, _ = row_greedy(x, up, b, q, cap, protected)
            for j in range(w):
                available = [v for v in possible if v[0][:j] == tuple(y[:j])]
                best = min(available, key=lambda v: (v[0][j] % q != 0, int(v[1][j])**2, int(v[1][j])))
                self.assertEqual(y[j], best[0][j])

    def test_250_fields_and_domains(self):
        rng = np.random.default_rng(20261013)
        for _ in range(250):
            shape = tuple(map(int, rng.integers(1, 10, 2)))
            cap = int(rng.integers(0, 30)); b = int(rng.integers(0, 8)); q = int(rng.integers(1, 24))
            x = rng.integers(0, cap+1, shape, dtype=np.int64)
            protected = rng.random(shape) < .2
            y, info = reconstruct(x, b, q, cap, protected)
            self.assertLessEqual(np.abs((y-x).cumsum(0).cumsum(1)).max(), b)
            self.assertEqual(info['off_lattice'], np.count_nonzero(y % q))
            np.testing.assert_array_equal(y[protected], x[protected])
        for source in (np.array([[.9]]), np.array([1])):
            with self.assertRaises(ValueError):
                reconstruct(source, 1, 2)
        with self.assertRaises(TypeError):
            reconstruct(np.array([[1]]), 1.0, 2)

    def test_packet_same_body_and_paid_algorithm(self):
        x = np.array([[0, 20, 40], [60, 80, 100]], np.int64)
        mask = np.zeros(x.shape, bool); mask[0, 0] = True
        for step in (20, 200):
            for mode in ('lossy', 'zero-preserve'):
                a, abody, afees = encode(x, x, mask, step, mode, 0, {})
                b, bbody, bfees = encode(x, x, mask, step, mode, 1, {})
                self.assertEqual(abody, bbody)
                for packet, code, fees in ((a, 0, afees), (b, 1, bfees)):
                    self.assertEqual(sum(fees['fees'].values()), len(packet))
                    y, m, metadata, protected = decode(packet)
                    np.testing.assert_array_equal(y, x)
                    np.testing.assert_array_equal(m, mask)
                    self.assertEqual(metadata['algorithm_id'], code)
                    damaged = bytearray(packet); damaged[-1] ^= 1
                    with self.assertRaises(ValueError):
                        decode(damaged)

    def test_cold_sourcefree_worker(self):
        root = Path(__file__).resolve().parents[1]
        x = np.array([[0, 20, 40], [60, 80, 100]], np.int64)
        mask = np.zeros(x.shape, bool); mask[0, 0] = True
        packet, _, _ = encode(x, x, mask, 20, 'zero-preserve', 1, {})
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder/'field.qf01').write_bytes(packet)
            np.save(folder/'queries.npy', np.array([[0, 2, 0, 3], [0, 1, 0, 1]], np.int64))
            result = subprocess.run([sys.executable, str(root/'controls/worker.py'),
                str(folder/'field.qf01'), str(folder/'output.npz'), str(folder/'worker.json'),
                '--queries', str(folder/'queries.npy')], cwd=folder, timeout=30,
                capture_output=True, text=True,
                env=dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, (root, root/'src', root/'experiments')))))
            self.assertEqual(result.returncode, 0, result.stderr)
            with np.load(folder/'output.npz', allow_pickle=False) as output:
                np.testing.assert_array_equal(output['y'], x)


if __name__ == '__main__':
    unittest.main()
