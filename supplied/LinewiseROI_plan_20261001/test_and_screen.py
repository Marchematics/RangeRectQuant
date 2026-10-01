from __future__ import annotations
import sys, json, time, hashlib, lzma, struct, itertools
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'src'))
from corridor import row_reference, _row_fast, reconstruct, rectangle_max
ROOT=Path(__file__).parent
rng=np.random.default_rng(20261001)
checks=[]
start=time.perf_counter()
for k in range(1500):
    w=int(rng.integers(1,11)); B=int(rng.integers(0,11)); q=int(rng.integers(1,24));U=int(rng.integers(0,31))
    x=rng.integers(0,U+1,size=w,dtype=np.int64);up=rng.integers(-B,B+1,size=w,dtype=np.int64)
    protected=rng.random(w)<.1
    a=row_reference(x,up,B,q,U,protected);b=_row_fast(x,up,B,q,U,protected)
    assert all(np.array_equal(p,r) for p,r in zip(a,b)),(k,x,up,B,q,U,a,b)
checks.append({'test':'slow_fast_row_equality','cases':1500,'passed':True})
# Independently enumerate every legal candidate sequence on small rows.
for k in range(500):
    w=int(rng.integers(1,5));B=int(rng.integers(0,4));q=int(rng.integers(1,5));U=int(rng.integers(0,6))
    x=rng.integers(0,U+1,size=w,dtype=np.int64);up=rng.integers(-B,B+1,size=w,dtype=np.int64)
    protect=rng.random(w)<.2
    alphabets=[([int(x[j])] if protect[j] else list(range(0,U+1))) for j in range(w)]
    opt=None
    for seq in itertools.product(*alphabets):
        e=up+np.cumsum(np.array(seq)-x)
        if np.max(np.abs(e))>B:continue
        key=(sum(v%q!=0 for v in seq),int(e@e))
        if opt is None or key<opt:opt=key
    y,e,n,en=_row_fast(x,up,B,q,U,protect)
    assert (n,en)==opt,(k,x,up,B,q,U,(n,en),opt)
checks.append({'test':'independent_exhaustive_row_objective','cases':500,'passed':True})
for k in range(300):
    h=int(rng.integers(1,9));w=int(rng.integers(1,9));U=int(rng.integers(1,31));B=int(rng.integers(0,9));q=int(rng.integers(1,25))
    x=rng.integers(0,U+1,size=(h,w),dtype=np.int64);protected=rng.random(x.shape)<.2
    y,info=reconstruct(x,B,q,U,protected)
    em=rectangle_max(y-x)
    assert em<=4*B and y.min()>=0 and y.max()<=U and np.array_equal(x[protected],y[protected])
checks.append({'test':'full_field_range_rectangle_protected','cases':300,'passed':True})
(ROOT/'results/tests.json').write_text(json.dumps({'checks':checks,'seconds_including_compile':time.perf_counter()-start},indent=2))
print('TESTS',checks,flush=True)

# All data below are synthetic. No claim about the four target geographic windows.
h=w=128; ii,jj=np.indices((h,w));rows=[]
fields={
 'uniform_integer':rng.integers(0,10001,size=(h,w),dtype=np.int64),
 'sparse_integer':np.where(rng.random((h,w))<.6,0,rng.integers(1,10001,size=(h,w))).astype(np.int64),
 'smooth_saturated':np.clip(np.rint(10000*(.5+.6*np.sin(ii/11)*np.cos(jj/17))),0,10000).astype(np.int64),
 'checkerboard_extremes':np.where((ii+jj)%2,10000,0).astype(np.int64),
}

def shuffled(a):
    a=np.asarray(a,dtype='<u2')
    return a.view(np.uint8).reshape(-1,2).T.copy().tobytes()
for name,x in fields.items():
    baseline=lzma.compress(shuffled(x),preset=6)
    for eps,q in [(100,20),(1000,200)]:
        start=time.perf_counter();y,info=reconstruct(x,eps//4,q,10000)
        sec=time.perf_counter()-start
        coarse=(y//q).astype('<u2');rho=(y%q).astype('<u2')
        # Probe payload only: two independently compressed arrays; NOT BA02.
        z1=lzma.compress(shuffled(coarse),preset=6);z2=lzma.compress(shuffled(rho),preset=6)
        em=int(rectangle_max(y-x))
        row={'synthetic_source':name,'shape':[h,w],'epsilon':eps,'step':q,**{k:v for k,v in info.items() if k!='row_min_off_lattice'},
             'exact_max_rectangle':em,'encoder_seconds':sec,'raw_lossless_payload_bytes':len(baseline),
             'coarse_payload_bytes':len(z1),'fine_payload_bytes':len(z2),
             'payload_saved_pct':100*(1-(len(z1)+len(z2))/len(baseline)),
             'source_sha256':hashlib.sha256(x.astype('<i8').tobytes()).hexdigest()}
        rows.append(row);print(row,flush=True)
        np.savez_compressed(ROOT/'results'/f'{name}_{eps}.npz',x=x,y=y)
(ROOT/'results/synthetic_screen.json').write_text(json.dumps({'warning':'Synthetic feasibility and payload diagnostic only. No complete BA02 stream and no geographic evaluation.','rows':rows},indent=2))
