from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT.parent/'LinewiseROI/experiments'))
from controls import research_packet as packet
from controls.closest_mechanisms import sigma_delta,bitdepth,prefix_round,nearest_integer
from controls.viable_greedy import reconstruct
from experiments.research_common import feasible_widths,_maximum_rectangle


def rectangles(d):
    h,w=d.shape
    return max(abs(int(d[a:b,c:e].sum())) for a in range(h) for b in range(a+1,h+1)
               for c in range(w) for e in range(c+1,w+1))


class ResearchControls(unittest.TestCase):
    def test_signed_rational_transport(self):
        y=np.array([[-10000,0,10000],[20000,2530000,2540000]],np.int64)
        mask=np.zeros(y.shape,bool); p=mask.copy(); p[0,1]=True
        blob,fees=packet.encode(y,mask,10000,10000,{'method':'sigma-delta'},{},p,253)
        actual,m,protected,meta=packet.decode(blob)
        np.testing.assert_array_equal(actual,y)
        np.testing.assert_array_equal(protected,p)
        self.assertEqual(meta['denominator'],253)
        self.assertEqual(sum(fees.values()),len(blob))
        for corrupted in (blob[:-1],blob+b'x',blob[:100]+bytes([blob[100]^1])+blob[101:]):
            with self.assertRaises(ValueError):
                packet.decode(corrupted)

    def test_mask_and_protected_are_distinct(self):
        y=np.array([[0,13,6],[7,2,0]])
        mask=np.zeros_like(y,bool); mask[0,0]=True
        p=np.zeros_like(y,bool); p[0,1]=True
        blob,_=packet.encode(y,mask,5,100,{}, {},p)
        out,m,protected,_=packet.decode(blob)
        np.testing.assert_array_equal(out,y)
        np.testing.assert_array_equal(m,mask)
        np.testing.assert_array_equal(protected,p|mask)

    def test_fiber_expanded_parameter(self):
        x=np.random.default_rng(1).integers(0,10001,(9,7))
        mask=np.zeros_like(x,bool); mask[2,1]=True; x[mask]=0
        blob,fees,_=packet.encode_fiber(x,mask,62,{}, {})
        y,m,p,meta=packet.decode(blob)
        self.assertLessEqual(rectangles(y-x),248)
        self.assertTrue(np.array_equal(mask,m) and np.array_equal(p,m))
        self.assertEqual(sum(fees.values()),len(blob))
        self.assertEqual(meta['margin'],62)

    def test_published_sigma_delta_against_fraction_reference(self):
        x=np.array([[0,1,3],[11,0,10],[5,11,0]],np.int64); cap=11; d=3; m=5
        out=sigma_delta(x,cap,d)
        states={}; expected=np.empty_like(x)
        alphabet=[Fraction(k*cap,m) for k in range(-1,m+2)]
        for i in range(3):
            for j in range(3):
                z=Fraction(int(x[i,j]))+states.get((i,j-1),0)+states.get((i-1,j),0)-states.get((i-1,j-1),0)
                v=min(alphabet,key=lambda a:(abs(a-z),a))
                states[i,j]=z-v; expected[i,j]=int(v*m)
        np.testing.assert_array_equal(out,expected)
        prefix=(out-x*m).cumsum(0).cumsum(1)
        self.assertLessEqual(2*int(np.abs(prefix).max()),cap)

    def test_budget_bitdepth_and_ties(self):
        self.assertEqual(bitdepth(10000,100),8)
        self.assertEqual(bitdepth(10000,1000),5)
        np.testing.assert_array_equal(nearest_integer(np.array([-3,-1,1,3]),2),[-2,-1,0,1])
        np.testing.assert_array_equal(prefix_round(np.array([[5,5]]),10),[[0,10]])

    def test_fine_bottleneck_with_protection(self):
        rng=np.random.default_rng(42)
        for q in (1,2,5,20):
            for b in (0,1,4,10):
                x=rng.integers(0,31,(8,11)); p=rng.random(x.shape)<.15
                y,_=reconstruct(x,b,q,30,p)
                widths=feasible_widths(x,y,b,30,p)
                fine=(y%q!=0)&~p
                self.assertTrue((widths[fine]<q).all())
                self.assertTrue((widths[~p]>0).all())

    def test_exact_maximum_for_signed_numerators(self):
        rng=np.random.default_rng(0)
        for shape in ((1,4),(4,1),(3,4)):
            d=rng.integers(-20000,20001,shape)
            self.assertEqual(_maximum_rectangle(d),rectangles(d))

    def test_integer_pointwise_barrier_exhaustive(self):
        cap=2
        pairs=list(itertools.product(range(cap+1),repeat=2))
        for delta in (0,.9,1,1.9,2,3):
            worst=max(abs(sum(y)-sum(x)) for x in pairs for y in pairs
                      if all(abs(a-b)<=delta for a,b in zip(x,y)))
            self.assertEqual(worst,2*min(int(delta),cap))
