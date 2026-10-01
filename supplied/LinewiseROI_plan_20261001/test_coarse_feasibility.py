from pathlib import Path
import sys, json
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from corridor import _row_fast
from coarse_feasibility import coarse_row_feasible
rng=np.random.default_rng(20261003)
for trial in range(1000):
    w=int(rng.integers(1,25));B=int(rng.integers(0,14));q=int(rng.integers(1,30));U=int(rng.integers(0,51))
    x=rng.integers(0,U+1,w,dtype=np.int64)
    up=rng.integers(-B,B+1,w,dtype=np.int64)
    p=rng.random(w)<.15
    z=coarse_row_feasible(x,up,B,q,U,p)
    y,e,n,energy=_row_fast(x,up,B,q,U,p)
    assert z['feasible']==(n==0),(trial,x,up,B,q,U,p,z,n)
report={'test':'linear_zero_fine_feasibility_vs_exact_dp','cases':1000,'passed':True,
        'note':'Conditional on a fixed incoming prefix-error row. Not a global two-dimensional optimality result.'}
(ROOT/'results/coarse_feasibility_tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
