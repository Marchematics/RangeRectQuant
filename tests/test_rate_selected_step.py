import unittest

import numpy as np

from controls import research_packet
from controls.rate_selected_step import encode_selected
from controls.review_geometry import finite_code_bits
from controls.viable_greedy import reconstruct
from range_rect_quant.corridor import rectangle_max


class RateSelectedStep(unittest.TestCase):
    def test_exhaustive_selection_matches_independent_complete_encodings(self):
        x = np.array([[0, 3, 5], [5, 1, 0]], np.int64)
        mask = np.zeros(x.shape, bool); mask[1, 2] = True
        protected = np.zeros(x.shape, bool); protected[0, 1] = True
        packet, y, detail = encode_selected(x, 12, 5, mask, protected, candidates=range(1, 7))
        expected = []
        for q in range(1, 7):
            field, _ = reconstruct(x, 3, q, 5, protected | mask)
            blob, _ = research_packet.encode(field, mask, q, 5,
                dict(family='RangeRectQuant', epsilon=12, quantization_step=q), {}, protected | mask)
            expected.append((len(blob), q, blob, field))
        winner = min(expected, key=lambda row: row[:2])
        self.assertEqual(packet, winner[2])
        np.testing.assert_array_equal(y, winner[3])
        self.assertEqual(detail['selected_step'], winner[1])
        self.assertTrue(detail['complete_canonical_domain'])
        self.assertEqual(len(detail['rows']), 6)
        for _, _, _, field in expected:
            self.assertLessEqual(int(rectangle_max(field-x)), 12)
            np.testing.assert_array_equal(field[protected | mask], x[protected | mask])

    def test_nested_candidates_never_increase_paid_rate(self):
        rng = np.random.default_rng(20261004)
        for epsilon in (0, 4, 19):
            x = rng.integers(0, 8, (4, 5), dtype=np.int64)
            first, _, small = encode_selected(x, epsilon, 7, candidates=[1, 3])
            second, y, large = encode_selected(x, epsilon, 7, candidates=[8, 3, 1, 2, 3])
            self.assertLessEqual(len(second), len(first))
            self.assertFalse(large['complete_canonical_domain'])
            self.assertEqual(large['candidate_steps'], [1, 2, 3, 8])
            self.assertLessEqual(int(rectangle_max(y-x)), epsilon)
            self.assertEqual(small['selected_bytes'], len(first))

    def test_zero_range_zero_budget_and_protected_field(self):
        packet, y, detail = encode_selected(np.zeros((2, 3), np.int64), 0, 0)
        self.assertEqual(detail['candidate_count'], 65536)
        self.assertEqual(detail['full_construction_trials'], 1)
        self.assertTrue(detail['complete_transport_domain'])
        self.assertFalse(y.any())
        x = np.array([[0, 7], [6, 1]], np.int64)
        protected = np.ones(x.shape, bool)
        packet, y, detail = encode_selected(x, 7, 7, protected=protected)
        np.testing.assert_array_equal(y, x)
        decoded, _, p, meta = research_packet.decode(packet)
        np.testing.assert_array_equal(decoded, x)
        np.testing.assert_array_equal(p, protected)
        self.assertEqual(meta['step'], detail['selected_step'])

    def test_arguments_and_caller_metadata(self):
        x = np.array([[1]], np.int64)
        for epsilon, cap, candidates, error in [
            (-1, 3, None, ValueError), (True, 3, None, TypeError),
            (4.0, 3, None, TypeError), (4, 32768, None, ValueError),
            (4, 3, [], ValueError), (4, 3, [0], ValueError),
            (4, 3, [65537], ValueError), (4, 3, [False], TypeError),
            (4, 3, [1.2], TypeError)]:
            with self.subTest(epsilon=epsilon, cap=cap, candidates=candidates):
                with self.assertRaises(error):
                    encode_selected(x, epsilon, cap, candidates=candidates)
        with self.assertRaises(ValueError):
            encode_selected(x, 4, 3, mask=np.ones(x.shape, bool))
        with self.assertRaises(ValueError):
            encode_selected(x, 4, 3, protected=np.ones((2, 2), bool))
        with self.assertRaises(ValueError):
            encode_selected(np.array([[.5]]), 4, 3)
        config = {'note': 'kept'}; geo = {'units': 'test'}
        packet, _, _ = encode_selected(x, 4, 3, config=config, geo=geo)
        meta = research_packet.decode(packet)[3]
        self.assertEqual(config, {'note': 'kept'})
        self.assertEqual(geo, {'units': 'test'})
        self.assertEqual(meta['method']['note'], 'kept')

    def test_large_steps_equal_independent_packets_and_constructions(self):
        x = np.array([[0, 3, 5], [4, 2, 1]], np.int64)
        p = np.array([[False, True, False], [True, False, False]])
        candidates = [6, 7, 12, 101, 1000, 65536]
        blob, y, detail = encode_selected(x, 12, 5, protected=p, candidates=candidates,
                                          config={'note': 'fixed'}, geo={'units': 'test'})
        expected = []
        for q in candidates:
            field, _ = reconstruct(x, 3, q, 5, p)
            method = dict(note='fixed', family='RangeRectQuant', epsilon=12, quantization_step=q)
            packet, _ = research_packet.encode(field, np.zeros(x.shape, bool), q, 5, method,
                                               {'units': 'test'}, p)
            expected.append((len(packet), q, packet))
            np.testing.assert_array_equal(field, y)
        self.assertEqual(blob, min(expected, key=lambda row: row[:2])[2])
        self.assertEqual(detail['full_construction_trials'], 1)
        self.assertEqual(detail['large_step_equivalence']['candidate_count'], len(candidates))

    def test_same_budget_has_disjoint_enumerative_step_optima(self):
        # Even exact protected fields at the same budget have different optima.
        winners = []
        for value in (0, 3):
            x = np.full((2, 4), value, np.int64)
            costs = []
            for q in range(1, 5):
                y, _ = reconstruct(x, 25, q, 3, np.ones(x.shape, bool))
                m = int(np.count_nonzero(y % q))
                costs.append(finite_code_bits(x.size, 3, q, m))
            winners.append({q+1 for q, cost in enumerate(costs) if cost == min(costs)})
        self.assertEqual(winners, [{4}, {2, 3}])
        self.assertFalse(winners[0] & winners[1])


if __name__ == '__main__':
    unittest.main()
