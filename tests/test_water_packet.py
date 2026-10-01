import unittest
import numpy as np
from controls.water_packet import encode,decode,water_grid


class WaterPacket(unittest.TestCase):
    def test_native_lossless_percentage_files(self):
        x=np.random.default_rng(2).integers(0,101,(9,11)); mask=np.zeros_like(x,bool); mask[2,3]=True; x[mask]=0
        grid=[c for c in water_grid() if c['backend'] in ('u8-lzma','u8-png','integer-lzma','jpeg2000')]
        for cfg in grid:
            blob,fees=encode(x,mask,cfg,{},[])
            y,m,p,meta=decode(blob,[])
            np.testing.assert_array_equal(y,x); np.testing.assert_array_equal(m,mask)
            self.assertEqual(sum(fees.values()),len(blob)); self.assertEqual(meta['cap'],100)
            with self.assertRaises(ValueError): decode(blob[:-1],[])

    def test_grid_is_metadata_scaled(self):
        configs=water_grid()
        self.assertEqual(len(configs),41)
        self.assertTrue(all(c['base_bound']==100 for c in configs if c['backend']=='qpet'))
