"""Capacity-constrained sum pyramid and reversible sum-deviation coding.

This structural control uses no prefix-error states or RRQ viability intervals.
Every split conserves its parent total. Rectangle eligibility is audited later.
"""
import numpy as np
from numba import njit


def pyramid(a):
    a=np.asarray(a,np.int64)
    if a.ndim!=2 or a.shape[0]!=a.shape[1] or not a.size or a.shape[0]&(a.shape[0]-1):
        raise ValueError('Square power-of-two field required')
    levels=[a]
    while levels[-1].shape[0]>1:
        b=levels[-1]
        levels.append(b[::2,::2]+b[::2,1::2]+b[1::2,::2]+b[1::2,1::2])
    return levels


@njit(cache=True)
def _split(source,counts,parent,step,scaled,cap):
    h=parent.shape[0];out=np.zeros((2*h,2*h),np.int64)
    for i in range(h):
        for j in range(h):
            ss=np.int64(0);nn=np.int64(0)
            for k in range(4):
                ss+=source[2*i+k//2,2*j+k%2];nn+=counts[2*i+k//2,2*j+k%2]
            remaining=parent[i,j];rest=nn
            for k in range(4):
                r,c=2*i+k//2,2*j+k%2;n=counts[r,c];rest-=n
                lo=max(0,remaining-cap*rest);hi=min(cap*n,remaining)
                if lo>hi:raise ValueError('Infeasible parent mass')
                if k==3:
                    value=remaining
                elif nn==0:
                    value=0
                else:
                    target=source[r,c]*nn+(parent[i,j]-ss)*n
                    spacing=step*max(1,n) if scaled else step
                    lower=-((-lo)//spacing);upper=hi//spacing
                    if lower<=upper:
                        den=nn*spacing;index=target//den
                        if 2*(target-index*den)>den:index+=1
                        value=min(upper,max(lower,index))*spacing
                    else:
                        value=target//nn
                        if 2*(target-value*nn)>nn:value+=1
                        value=min(hi,max(lo,value))
                if value<lo or value>hi:raise ValueError('Child capacity')
                out[r,c]=value;remaining-=value
            if remaining:raise ValueError('Parent conservation')
    return out


def reconstruct(x,mask,step,scaled=False,cap=10000):
    x=np.asarray(x,np.int64);mask=np.asarray(mask,bool)
    if (mask.shape!=x.shape or type(step) is not int or not 1<=step<=65535 or
            not 0<=cap<=65535 or x.min()<0 or x.max()>cap or x[mask].any()):
        raise ValueError('Bounded pyramid input')
    source=pyramid(x);counts=pyramid(~mask)
    current=source[-1].copy()
    for level in range(len(source)-2,-1,-1):
        current=_split(source[level],counts[level],current,step,scaled,cap)
    if current[mask].any() or current.min()<0 or current.max()>cap or current.sum()!=x.sum():
        raise ValueError('Pyramid invariant')
    return current


def transform(y,mask):
    """Root total plus three sum deviations per quadtree node (exact N values)."""
    levels=pyramid(y);counts=pyramid(~np.asarray(mask,bool));stream=[levels[-1].ravel()]
    for level in range(len(levels)-2,-1,-1):
        parent=levels[level+1];n=counts[level+1];safe=np.maximum(1,n)
        ds=[]
        for k in range(3):
            child=levels[level][k//2::2,k%2::2]
            count=counts[level][k//2::2,k%2::2]
            ds.append(child-parent*count//safe)
        stream.append(np.stack(ds,axis=-1).ravel())
    out=np.concatenate(stream).astype('<i8')
    assert out.size==np.asarray(y).size
    return out


def inverse(stream,mask):
    mask=np.asarray(mask,bool);counts=pyramid(~mask);stream=np.asarray(stream,np.int64)
    if stream.ndim!=1 or stream.size!=mask.size:raise ValueError('Pyramid stream length')
    current=stream[:1].reshape(1,1);position=1
    for level in range(len(counts)-2,-1,-1):
        h=current.shape[0];length=3*h*h
        ds=stream[position:position+length].reshape(h,h,3);position+=length
        out=np.zeros((2*h,2*h),np.int64);n=counts[level+1];safe=np.maximum(1,n)
        total=np.zeros_like(current)
        for k in range(3):
            child=current*counts[level][k//2::2,k%2::2]//safe+ds[:,:,k]
            out[k//2::2,k%2::2]=child;total+=child
        out[1::2,1::2]=current-total;current=out
    if position!=stream.size:raise ValueError('Pyramid stream consumption')
    return current
