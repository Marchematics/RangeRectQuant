from pathlib import Path
import itertools,json,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'src'))
from corridor import _row_fast

def greedy(x,u,B,q,U):
    a=0;prevu=0;ys=[];es=[]
    for xj,uj in zip(x,u):
        d=uj-prevu;prevu=uj;options=[]
        for y in sorted(set(range(0,U+1,q))|{xj}):
            b=a+d+y-xj
            if -B<=b<=B:options.append((int(y%q!=0),b*b,b,y))
        if not options:return None
        _,_,b,y=min(options);ys.append(y);es.append(b);a=b
    return ys,es
out=None
for w in [2,3,4]:
    for xx in itertools.product(range(5),repeat=w):
        x=np.array(xx,np.int64)
        for uu in itertools.product(range(-1,2),repeat=w):
            u=np.array(uu,np.int64); y,e,n,_=_row_fast(x,u,1,2,4,np.zeros(w,bool))
            g=greedy(xx,uu,1,2,4)
            if g is None and n==0:
                du=np.diff(np.r_[0,u]);xp=np.maximum(-du,0);yp=np.maximum(du,0)
                out={'source_row':list(xx),'incoming_prefix_error':list(uu),'band':1,'step':2,'cap':4,
                     'greedy':'no feasible next value','dp_output':y.tolist(),'dp_prefix':e.tolist(),
                     'prior_row_source':xp.tolist(),'prior_row_output':yp.tolist()}
                break
        if out:break
    if out:break
print(out)
(Path(__file__).parent/'results/greedy_counterexample.json').write_text(json.dumps(out,indent=2))
