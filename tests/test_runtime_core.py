import unittest
import numpy as np
from experiments.runtime_scaling import construct_core
from controls.viable_greedy import reconstruct
from range_rect_quant.corridor import reconstruct as reference,_row_fast


class RuntimeCore(unittest.TestCase):
    def test_same_choices_without_audit_array(self):
        rng=np.random.default_rng(4)
        for band,q in ((0,1),(2,5),(25,20)):
            x=rng.integers(0,10001,(7,11)); p=rng.random(x.shape)<.1
            y,_=reconstruct(x,band,q,10000,p)
            np.testing.assert_array_equal(construct_core(x,p,band,q),y)
            z,_=reference(x,band,q,10000,p)
            np.testing.assert_array_equal(construct_core(x,p,band,q,_row_fast),z)
