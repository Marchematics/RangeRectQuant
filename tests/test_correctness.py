import itertools
import unittest
import numpy as np
from range_rect_quant.corridor import _row_fast, row_reference, reconstruct, rectangle_max
from range_rect_quant.coarse_feasibility import coarse_row_feasible


class CorrectnessTests(unittest.TestCase):
    def test_1500_fast_reference(self):
        rng = np.random.default_rng(20261001)
        for k in range(1500):
            w=int(rng.integers(1,11)); b=int(rng.integers(0,11)); q=int(rng.integers(1,24)); cap=int(rng.integers(0,31))
            x=rng.integers(0,cap+1,w,dtype=np.int64); up=rng.integers(-b,b+1,w,dtype=np.int64)
            protect=rng.random(w)<.1
            fast=_row_fast(x,up,b,q,cap,protect); slow=row_reference(x,up,b,q,cap,protect)
            for a,z in zip(fast,slow):np.testing.assert_array_equal(a,z,err_msg=str(k))

    def test_500_independent_brute_rows(self):
        rng=np.random.default_rng(20261004)
        for k in range(500):
            w=int(rng.integers(1,5)); b=int(rng.integers(0,4)); q=int(rng.integers(1,5)); cap=int(rng.integers(0,6))
            x=rng.integers(0,cap+1,w,dtype=np.int64); up=rng.integers(-b,b+1,w,dtype=np.int64); protect=rng.random(w)<.2
            optimum=None
            for values in itertools.product(*[([int(x[j])] if protect[j] else range(cap+1)) for j in range(w)]):
                error=[]; cumulative=0
                for j,value in enumerate(values):
                    cumulative+=value-int(x[j]);error.append(int(up[j])+cumulative)
                if any(abs(v)>b for v in error):continue
                cost=(sum(v%q!=0 for v in values),sum(v*v for v in error))
                if optimum is None or cost<optimum:optimum=cost
            y,e,n,energy=_row_fast(x,up,b,q,cap,protect)
            self.assertEqual((int(n),int(energy)),optimum,str(k))

    def test_300_fields(self):
        rng=np.random.default_rng(20261005)
        for k in range(300):
            shape=tuple(map(int,rng.integers(1,9,2)));cap=int(rng.integers(1,31));b=int(rng.integers(0,9));q=int(rng.integers(1,25))
            x=rng.integers(0,cap+1,shape,dtype=np.int64);protect=rng.random(shape)<.2
            y,info=reconstruct(x,b,q,cap,protect)
            self.assertLessEqual(rectangle_max(y-x),4*b);self.assertTrue(np.all((y>=0)&(y<=cap)))
            np.testing.assert_array_equal(x[protect],y[protect])
            self.assertEqual(info['off_lattice'],int(np.count_nonzero(y%q)))

    def test_1000_coarse_feasibility(self):
        rng=np.random.default_rng(20261003)
        for k in range(1000):
            w=int(rng.integers(1,25));b=int(rng.integers(0,14));q=int(rng.integers(1,30));cap=int(rng.integers(0,51))
            x=rng.integers(0,cap+1,w,dtype=np.int64);up=rng.integers(-b,b+1,w,dtype=np.int64);protect=rng.random(w)<.15
            result=coarse_row_feasible(x,up,b,q,cap,protect)
            y,e,n,energy=_row_fast(x,up,b,q,cap,protect)
            self.assertEqual(result['feasible'],n==0,str(k))

    def test_greedy_counterexample_and_domains(self):
        y,e,n,energy=_row_fast(np.array([1,4]),np.array([0,-1]),1,2,4,np.zeros(2,bool))
        np.testing.assert_array_equal(y,[2,4]); self.assertEqual(n,0)
        for args in [(np.zeros((1,1)),1,2,4),(np.array([[5]]),1,2,4),(np.array([[1]]),-1,2,4)]:
            with self.assertRaises((ValueError,TypeError)):reconstruct(*args)

    def test_independent_geometry_100_brute_fields(self):
        from verify_saved import independent_rectangle_max
        rng=np.random.default_rng(20261006)
        for _ in range(100):
            h,w=map(int,rng.integers(1,6,2));d=rng.integers(-9,10,(h,w),dtype=np.int64)
            brute=max(abs(int(d[a:b,c:e].sum())) for a in range(h) for b in range(a+1,h+1) for c in range(w) for e in range(c+1,w+1))
            self.assertEqual(independent_rectangle_max(d),brute)


if __name__ == '__main__':unittest.main()
