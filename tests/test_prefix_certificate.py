import unittest

import numpy as np

from range_rect_quant.corridor import rectangle_max


class PrefixCertificate(unittest.TestCase):
    def test_factor_four_is_tight_even_for_binary_pixels(self):
        for band in (1, 2, 3, 5, 17):
            row_sign = np.r_[np.ones(band, np.int64), -np.ones(2*band, np.int64)]
            difference = row_sign[:, None]*np.array([[1, -1, -1]], np.int64)
            x = np.maximum(-difference, 0)
            y = np.maximum(difference, 0)
            self.assertTrue(((0 <= x) & (x <= 1)).all())
            self.assertTrue(((0 <= y) & (y <= 1)).all())
            prefix = (y-x).cumsum(0).cumsum(1)
            self.assertEqual(int(np.abs(prefix).max()), band)
            self.assertEqual(int((y-x)[band:, 1:].sum()), 4*band)
            self.assertEqual(int(rectangle_max(y-x)), 4*band)


if __name__ == '__main__':
    unittest.main()
