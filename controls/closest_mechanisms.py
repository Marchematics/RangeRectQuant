"""Exact-numerator implementations of the published 2D quantizer and controls."""
import numpy as np
from numba import njit


def bitdepth(cap,epsilon):
    if cap<=0 or epsilon<=0:
        raise ValueError('Positive cap and budget')
    d=2
    while 2*cap>epsilon*(2**d-3):
        d+=1
    return d


@njit(cache=True)
def sigma_delta(x, cap, d, projected=False):
    # All states are numerators with denominator m. E=sum(output-input).
    m=2**d-3
    h,w=x.shape; out=np.empty((h,w),np.int64); up=np.zeros(w,np.int64)
    lower=0 if projected else -1; upper=m if projected else m+1
    for i in range(h):
        left=np.int64(0); diagonal=np.int64(0)
        for j in range(w):
            old=up[j]
            z=x[i,j]*m-left-old+diagonal
            k=z//cap
            # Exactly nearest level, ties to the smaller level, also for z<0.
            if 2*(z-k*cap)>cap:
                k+=1
            k=min(upper,max(lower,k))
            out[i,j]=k*cap
            b=k*cap-z
            diagonal=old; up[j]=b; left=b
    return out


def nearest_integer(numerators,denominator):
    # Nearest integer, ties to the smaller integer. No floating-point error.
    a,r=np.divmod(numerators,denominator)
    return a+(2*r>denominator)


def prefix_round(x,step):
    s=np.asarray(x,np.int64).cumsum(0).cumsum(1)
    k,r=np.divmod(s,step); rounded=(k+(2*r>step))*step
    padded=np.pad(rounded,((1,0),(1,0)))
    return padded[1:,1:]-padded[:-1,1:]-padded[1:,:-1]+padded[:-1,:-1]


def candidates(x,cap,epsilon):
    d=bitdepth(cap,epsilon); m=2**d-3; q=max(1,epsilon//5)
    raw=sigma_delta(x,cap,d)
    clipped=np.clip(raw,0,cap*m)
    projected=sigma_delta(x,cap,d,True)
    prefix=prefix_round(x,q)
    return [
        ('sigma-delta',raw,m,cap,dict(d=d,denominator=m,projection=False)),
        ('sigma-delta-clip',clipped,m,cap,dict(d=d,denominator=m,postprocess='clip')),
        ('sigma-delta-clip-integer',nearest_integer(clipped,m),1,q,
         dict(d=d,postprocess='clip;nearest-integer-ties-lower')),
        ('sigma-delta-project',projected,m,cap,dict(d=d,denominator=m,projection=True)),
        ('prefix-round',prefix,1,q,dict(step=q,postprocess='inverse-difference')),
        ('prefix-round-clip',np.clip(prefix,0,cap),1,q,
         dict(step=q,postprocess='inverse-difference;clip')),
    ]
