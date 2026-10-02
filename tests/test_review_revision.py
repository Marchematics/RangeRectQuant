import itertools
import unittest
import numpy as np
from controls import review_packet
from controls.hierarchical_sum import reconstruct as tree,transform,inverse
from controls.review_geometry import certificate,finite_code_bits
from controls.viable_greedy import reconstruct


class ReviewRevision(unittest.TestCase):
    def test_residue_width_and_protected_counts(self):
        rng=np.random.default_rng(302)
        for q,b in itertools.product((1,2,5,10),(0,1,4,10)):
            for _ in range(12):
                x=rng.integers(0,31,(7,9));p=rng.random(x.shape)<.2
                y,_=reconstruct(x,b,q,30,p);c=certificate(x,y,p,b,q,30)
                self.assertEqual(c['fine'],np.count_nonzero(y%q))
                self.assertLessEqual(c['fine'],c['width_bound_fine'])
        with self.assertRaises(ValueError):
            certificate(np.zeros((1,1),np.int64),np.array([[31]]),np.zeros((1,1),bool),40,5,30)

    def test_interval_multiple_count_exhaustive(self):
        for q in range(1,12):
            for lo in range(-10,12):
                for hi in range(lo,14):
                    actual=sum(v%q==0 for v in range(lo,hi+1))
                    self.assertEqual(hi//q-(lo-1)//q,actual)
                    if hi-lo+1>=q:self.assertGreater(actual,0)

    def test_finite_set_rank_lengths(self):
        self.assertEqual(finite_code_bits(3,0,1,0),0)
        self.assertEqual(finite_code_bits(3,1,1,0),3)
        with self.assertRaises(ValueError):finite_code_bits(3,1,1,1)
        for n,q,u in itertools.product(range(1,5),range(2,5),range(0,6)):
            Q=u//q+1
            for m in range(n+1):
                bits=finite_code_bits(n,u,q,m)
                import math
                count=Q**n*(n+1)*math.comb(n,m)*(q-1)**m
                self.assertGreaterEqual(2**bits,count)

    def test_capacity_pyramid_and_all_transports(self):
        rng=np.random.default_rng(33)
        for size in (1,2,4,8,16):
            x=rng.integers(0,101,(size,size));mask=rng.random(x.shape)<.3;x[mask]=0
            np.testing.assert_array_equal(inverse(transform(x,mask),mask),x)
            for step,scaled in itertools.product((1,2,7,32),(False,True)):
                y=tree(x,mask,step,scaled,100)
                self.assertEqual(y.sum(),x.sum());self.assertFalse(y[mask].any())
                self.assertTrue(((0<=y)&(y<=100)).all())
                if step==1 and not scaled:np.testing.assert_array_equal(y,x)
                for layout in review_packet.LAYOUTS:
                    blob,fees=review_packet.encode(y,mask,step,layout,{}, {},cap=100)
                    actual,m,p,meta=review_packet.decode(blob)
                    expected=step*(y//step) if layout=='quotient-only' else y
                    np.testing.assert_array_equal(actual,expected)
                    np.testing.assert_array_equal(m,mask);np.testing.assert_array_equal(p,mask)
                    self.assertEqual(sum(fees.values()),len(blob))
                    with self.assertRaises(ValueError):review_packet.decode(blob[:-1]+bytes([blob[-1]^1]))
