import unittest
import numpy as np
from experiments.run_recompression_diagnostic import encode_step, summarize
from controls.field_packet import decode as greedy_decode
from controls.viable_greedy import reconstruct as greedy_reconstruct
from range_rect_quant.corridor import reconstruct as dp_reconstruct
from range_rect_quant.packet import decode as dp_decode, SETTINGS


class RecompressionTests(unittest.TestCase):
    def test_100_fully_coarse_fixed_points(self):
        rng = np.random.default_rng(20261021)
        for _ in range(100):
            q = int(rng.choice([20, 200])); b = SETTINGS[q][1]
            shape = tuple(map(int, rng.integers(1, 8, 2)))
            x = q * rng.integers(0, 10000 // q + 1, shape, dtype=np.int64)
            protected = rng.random(shape) < .3
            for reconstruct in (dp_reconstruct, greedy_reconstruct):
                y, info = reconstruct(x, b, q, 10000, protected)
                np.testing.assert_array_equal(y, x)
                self.assertEqual(info['off_lattice'], 0)

    def test_small_paid_iteration_and_identity(self):
        x = np.array([[0, 23, 10000], [81, 60, 1]], np.int64)
        mask = np.zeros_like(x, bool); mask[0, 0] = True
        for algorithm in ('dp', 'greedy', 'identity'):
            current = x
            for _ in range(3):
                packet, body, info = encode_step(current, mask, 20, algorithm, {'test': True})
                y, recovered_mask, meta, _ = (greedy_decode if algorithm == 'greedy' else dp_decode)(packet)
                self.assertEqual(sum(info['fees'].values()), len(packet))
                self.assertEqual(info['fees']['body_bytes'], len(body))
                self.assertEqual(meta['geo'], {'test': True})
                np.testing.assert_array_equal(recovered_mask, mask)
                self.assertLessEqual(np.abs((y.astype(np.int64) - current).cumsum(0).cumsum(1)).max(), 25)
                if algorithm == 'identity':
                    np.testing.assert_array_equal(y, x)
                current = y.astype(np.int64)
        with self.assertRaises(ValueError):
            encode_step(x, mask, 20, 'new-unknown-algorithm', {})

    def test_frozen_drift_gate_not_local_failure_or_one_bad_site(self):
        rows = []
        for algorithm in ('dp', 'greedy'):
            for q, epsilon in ((20, 100), (200, 1000)):
                for site in range(4):
                    for generation in range(2, 9):
                        rows.append(dict(algorithm=algorithm, step=q, site=site, **{'pass': generation},
                            status='DECODED_AND_AUDITED', packet_bytes=1, fine=1,
                            changed_from_previous=1, local_maximum=epsilon,
                            cumulative_maximum=epsilon + (1 if site < 3 else 0)))
        positive = summarize(rows, 0)
        self.assertTrue(all(positive['serious_drift_algorithm_pass'].values()))
        for row in rows:
            row['cumulative_maximum'] = SETTINGS[row['step']][0]
        self.assertFalse(any(summarize(rows, 0)['serious_drift_algorithm_pass'].values()))
        for row in rows:
            row['cumulative_maximum'] += 1
        rows[0]['local_maximum'] += 1
        self.assertFalse(summarize(rows, 0)['serious_drift_algorithm_pass']['dp'])


if __name__ == '__main__':
    unittest.main()
