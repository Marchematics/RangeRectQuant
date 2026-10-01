"""Research feasibility probe, not a publication-ready codec.

Encoder-only row DP over global prefix discrepancy. Every output value is
in [0, cap]. Coarse candidates are ALL multiples of step in the legal range;
fine transitions may use every legal integer; the original row is a witness
that every row has at least one feasible path.
The objective first minimizes off-lattice sites, then squared prefix state.
The state at a site is the GLOBAL 2D prefix error, not pixel error.
"""
from __future__ import annotations
import numpy as np
from numba import njit

@njit(cache=True)
def _row(x, up, band, step, cap, protected):
    """Quadratic-state reference over every physically legal integer value."""
    w=len(x);ns=2*band+1;inf=np.int64(2**60)
    oldn=np.full(ns,inf,np.int64);olde=np.full(ns,inf,np.int64)
    oldn[band]=0;olde[band]=0
    backs=np.full((w,ns),-1,np.int32)
    ups=0
    for j in range(w):
        d=up[j]-ups;ups=up[j]
        newn=np.full(ns,inf,np.int64);newe=np.full(ns,inf,np.int64)
        for ai in range(ns):
            if oldn[ai]==inf:continue
            for bi in range(ns):
                y=x[j]+bi-ai-d
                if y<0 or y>cap or (protected[j] and y!=x[j]):continue
                b=bi-band;cn=oldn[ai]+(1 if y%step else 0);ce=olde[ai]+b*b
                if cn<newn[bi] or (cn==newn[bi] and ce<newe[bi]):
                    newn[bi]=cn;newe[bi]=ce;backs[j,bi]=ai
        oldn=newn;olde=newe
    best=0
    for bi in range(ns):
        if oldn[bi]<oldn[best] or (oldn[bi]==oldn[best] and olde[bi]<olde[best]):best=bi
    if oldn[best]==inf:raise RuntimeError('No row path')
    out=np.empty(w,np.int64);errors=np.empty(w,np.int64);ix=best
    for j in range(w-1,-1,-1):
        prev=backs[j,ix];d=up[j]-(up[j-1] if j else 0)
        out[j]=x[j]+ix-prev-d;errors[j]=ix-band;ix=prev
    return out,errors,oldn[best],olde[best]

def reconstruct(x:np.ndarray, band:int, step:int, cap:int=10000, protected=None):
    x=np.asarray(x)
    if x.ndim!=2 or x.size==0 or not np.issubdtype(x.dtype,np.integer):
        raise ValueError('Expected nonempty 2D integer source')
    if any(not isinstance(v, (int, np.integer)) or isinstance(v, (bool, np.bool_)) for v in (band, step, cap)):
        raise TypeError('band, step and cap must be integers')
    band,step,cap=int(band),int(step),int(cap)
    if cap>2**30 or step>2**30 or x.size*cap>2**53-1:
        raise OverflowError('Probe integer arithmetic safety limit exceeded')
    if band<0 or step<=0 or cap<0 or x.min()<0 or x.max()>cap:
        raise ValueError('Illegal source, band, step or cap')
    if band>10000:raise ValueError('Probe state-space limit')
    x=x.astype(np.int64)
    if protected is None:protected=np.zeros_like(x,dtype=bool)
    protected=np.asarray(protected,dtype=bool)
    if protected.shape!=x.shape:raise ValueError('Mask shape mismatch')
    y=np.empty_like(x);up=np.zeros(x.shape[1],np.int64);counts=[]
    for i in range(x.shape[0]):
        y[i],up,n,_=_row(x[i],up,band,step,cap,protected[i]);counts.append(int(n))
    p=(y-x).cumsum(0).cumsum(1)
    assert np.abs(p).max()<=band
    assert y.min()>=0 and y.max()<=cap
    assert np.array_equal(y[protected],x[protected])
    return y,{'off_lattice':int(np.count_nonzero(y%step)), 'row_min_off_lattice':counts,
              'max_abs_prefix':int(np.abs(p).max()),'changed':int(np.count_nonzero(y!=x))}

@njit(cache=True)
def rectangle_max(error):
    h,w=error.shape; best=np.int64(0)
    for top in range(h):
        v=np.zeros(w,np.int64)
        for bottom in range(top,h):
            v+=error[bottom]; mx=np.int64(0);mn=np.int64(0)
            for j in range(w):
                mx=max(0,mx+v[j]);mn=min(0,mn+v[j])
                best=max(best,mx,-mn)
    return best

@njit(cache=True)
def _row_fast(x, up, band, step, cap, protected):
    """Same exact row objective, via residue-class sliding window minima.

    A coarse edge obeys a_idx == x - d + b_idx (mod step), and
    x-d+b_idx-cap <= a_idx <= x-d+b_idx. For each residue class,
    both interval endpoints increase monotonically, so a monotone deque
    finds all predecessor minima in O(2*band+1) work per source value.
    """
    w=len(x); ns=2*band+1; inf=np.int64(2**60)
    oldn=np.full(ns,inf,np.int64); olde=np.full(ns,inf,np.int64)
    oldn[band]=0;olde[band]=0
    backs=np.full((w,ns),-1,np.int32)
    dq=np.empty(ns,np.int32)
    ups=0
    for j in range(w):
        d=up[j]-ups;ups=up[j];t=x[j]-d
        newn=np.full(ns,inf,np.int64);newe=np.full(ns,inf,np.int64)
        if not protected[j]:
            for rb in range(min(step,ns)):
                ra=(t+rb)%step
                ap=ra;head=0;tail=0
                for bi in range(rb,ns,step):
                    hi=min(ns-1,t+bi);lo=max(0,t+bi-cap)
                    while ap<ns and ap<=hi:
                        if oldn[ap]!=inf:
                            while tail>head:
                                p=dq[tail-1]
                                if oldn[ap]<oldn[p] or (oldn[ap]==oldn[p] and olde[ap]<olde[p]):
                                    tail-=1
                                else:break
                            dq[tail]=ap;tail+=1
                        ap+=step
                    while tail>head and dq[head]<lo:head+=1
                    if tail>head:
                        ai=dq[head];b=bi-band
                        newn[bi]=oldn[ai];newe[bi]=olde[ai]+b*b;backs[j,bi]=ai
        if not protected[j]:
            # Fine channel: any legal integer, a contiguous predecessor window.
            ap=0;head=0;tail=0
            for bi in range(ns):
                hi=min(ns-1,t+bi);lo=max(0,t+bi-cap)
                while ap<ns and ap<=hi:
                    if oldn[ap]!=inf:
                        while tail>head:
                            p=dq[tail-1]
                            if oldn[ap]<oldn[p] or (oldn[ap]==oldn[p] and olde[ap]<olde[p]):tail-=1
                            else:break
                        dq[tail]=ap;tail+=1
                    ap+=1
                while tail>head and dq[head]<lo:head+=1
                if tail>head:
                    ai=dq[head];b=bi-band;cn=oldn[ai]+1;ce=olde[ai]+b*b
                    if cn<newn[bi] or (cn==newn[bi] and (ce<newe[bi] or (ce==newe[bi] and ai<backs[j,bi]))):
                        newn[bi]=cn;newe[bi]=ce;backs[j,bi]=ai
        for bi in range(ns):
            ai=bi-d
            if ai<0 or ai>=ns or oldn[ai]==inf:continue
            b=bi-band;cn=oldn[ai]+(1 if x[j]%step else 0);ce=olde[ai]+b*b
            if cn<newn[bi] or (cn==newn[bi] and (ce<newe[bi] or (ce==newe[bi] and ai<backs[j,bi]))):
                newn[bi]=cn;newe[bi]=ce;backs[j,bi]=ai
        oldn=newn;olde=newe
    best=0
    for bi in range(ns):
        if oldn[bi]<oldn[best] or (oldn[bi]==oldn[best] and olde[bi]<olde[best]):best=bi
    if oldn[best]==inf:raise RuntimeError('No row path')
    out=np.empty(w,np.int64);errors=np.empty(w,np.int64);ix=best
    for j in range(w-1,-1,-1):
        prev=backs[j,ix];b=ix-band;a=prev-band;d=up[j]-(up[j-1] if j else 0)
        out[j]=x[j]+b-a-d;errors[j]=b;ix=prev
    return out,errors,oldn[best],olde[best]

# The public routine can use either implementation for independent cross-checks.
row_reference = _row
_row = _row_fast
