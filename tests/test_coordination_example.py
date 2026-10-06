"""The opening example separates certificates, not encoded file sizes."""
import unittest

import numpy as np

from controls.viable_greedy import reconstruct
from experiments.verify_coordination_example import checkerboard_case, rectangle_count, rectangular_errors


class CoordinationExample(unittest.TestCase):
    def test_all_rectangles_and_linear_constructor_match(self):
        for height in range(1, 13):
            for width in range(1, 13):
                x, y, error, prefix = checkerboard_case(height, width)
                self.assertTrue(np.all(y != x))
                self.assertTrue(np.all((y == 0) | (y == 2)))
                self.assertEqual(int(np.abs(prefix).max()), 1)
                errors = rectangular_errors(error)
                self.assertEqual(len(errors), rectangle_count(height, width))
                self.assertEqual(max(map(abs, errors)), 1)
                actual, detail = reconstruct(x, 1, 2, 2, np.zeros(x.shape, bool))
                np.testing.assert_array_equal(actual, y)
                self.assertEqual(detail['off_lattice'], 0)

    def test_independent_witness_is_on_the_same_source(self):
        x, y, _, _ = checkerboard_case(3, 4)
        independent = np.full(x.shape, 2)
        self.assertTrue(np.all(np.abs(independent - x) <= 1))
        self.assertGreater(int((independent - x).sum()), 4)
        self.assertTrue(np.all(np.abs(y - x) == 1))

    def test_query_count_uses_exact_integer_arithmetic(self):
        self.assertEqual(rectangle_count(3, 4), 60)
        self.assertEqual(rectangle_count(1024, 1024), 275415040000)
        self.assertEqual(rectangle_count(10**10, 10**10), (10**10 * (10**10 + 1) // 2)**2)
        for shape in ((0, 4), (3, 0), (-1, 4)):
            with self.assertRaises(ValueError):
                rectangle_count(*shape)
        with self.assertRaises(TypeError):
            rectangle_count(2.5, 4)


if __name__ == '__main__':
    unittest.main()
