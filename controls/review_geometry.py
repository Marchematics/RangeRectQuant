"""Exact residue certificate along an unchanged, observed RRQ construction."""
import math
import numpy as np
from numba import njit


@njit(cache=True)
def _counts(x, y, protected, band, step, cap):
    h,w=x.shape; up=np.zeros(w,np.int64)
    fine=narrow=missing=protected_fine=range_deficit=suffix_deficit=0
    for i in range(h):
        low=np.empty(w+1,np.int64); high=np.empty(w+1,np.int64)
        low[w]=-band; high[w]=band
        for j in range(w-1,-1,-1):
            delta=up[j]-(up[j-1] if j else 0)
            if protected[i,j]:
                low[j]=max(-band,low[j+1]-delta);high[j]=min(band,high[j+1]-delta)
            else:
                t=x[i,j]-delta
                low[j]=max(-band,low[j+1]+t-cap);high[j]=min(band,high[j+1]+t)
        a=np.int64(0); diagonal=np.int64(0)
        for j in range(w):
            old=up[j];delta=old-diagonal;t=x[i,j]-delta
            if not 0<=y[i,j]<=cap:raise ValueError('Output range')
            observed=int(y[i,j]%step!=0);fine+=observed
            if protected[i,j]:
                if y[i,j]!=x[i,j]:raise ValueError('Protected value')
                protected_fine+=observed
            else:
                lo=max(low[j+1],a-t);hi=min(high[j+1],a-t+cap)
                s=t+lo-a;v=t+hi-a
                width=hi-lo+1; kappa=v//step-(s-1)//step
                left=max(0,low[j+1]+band,a-t+band)
                right=max(0,band-high[j+1],band-a-cap+t)
                if width!=2*band+1-left-right or width<1:
                    raise ValueError('Interval deficit identity')
                if observed!=int(kappa==0):raise ValueError('Residue certificate')
                missing+=int(kappa==0);narrow+=int(width<step)
                range_deficit+=int(max(0,a-t+band)+max(0,band-a-cap+t)>0)
                suffix_deficit+=int(low[j+1]>-band or high[j+1]<band)
            b=y[i,j]-t+a
            if not low[j+1]<=b<=high[j+1]:raise ValueError('Remaining-row state')
            diagonal=old;up[j]=b;a=b
    return fine,narrow,missing,protected_fine,range_deficit,suffix_deficit


def certificate(x,y,protected,band,step,cap=10000):
    x,y=np.asarray(x,np.int64),np.asarray(y,np.int64);p=np.asarray(protected,bool)
    if x.shape!=y.shape or x.shape!=p.shape or x.ndim!=2 or not x.size or step<1:
        raise ValueError('Certificate shapes/step')
    values=_counts(x,y,p,band,step,cap)
    out=dict(zip(('fine','narrow_unprotected','missing_coarse_residue','protected_fine',
                  'current_range_restrictions','remaining_row_restrictions'),map(int,values)))
    out['width_bound_fine']=out['narrow_unprotected']+out['protected_fine']
    out['pixels']=x.size;out['fine_fraction']=out['fine']/x.size
    out['width_bound_fraction']=out['width_bound_fine']/x.size
    assert out['fine']==out['missing_coarse_residue']+out['protected_fine']
    assert out['fine']<=out['width_bound_fine']
    return out


def finite_code_bits(n,cap,step,m):
    """Exact finite-set rank lengths; intended for small proof regressions."""
    if not (n>=1 and cap>=0 and step>=1 and 0<=m<=n) or (step==1 and m):
        raise ValueError('Finite code parameters')
    q=cap//step+1
    if step==1:return (q**n-1).bit_length()
    return ((q**n-1).bit_length() + n.bit_length() +
            (math.comb(n,m)-1).bit_length() +
            (((step-1)**m-1).bit_length() if step>1 else 0))
