"""Shared exact audits and source-free process endpoint for expanded evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

import numpy as np
from numba import njit

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT.parent/'LinewiseROI'
sys.path.append(str(LEGACY/'experiments'))
from built_area_integer_metrics import _maximum_rectangle


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for b in iter(lambda:stream.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def save(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def environment():
    env=dict(os.environ)
    env.update(json.loads((ROOT/'integration/checks/heldout_experiment_preflight_20261001.json').read_text())['environment'])
    env['PYTHONPATH']=os.pathsep.join(map(str,(ROOT,ROOT/'src',ROOT/'experiments',LEGACY/'experiments')))
    return env


class ColdDecoder:
    def __init__(self,folder):
        self.folder=Path(folder); self.folder.mkdir(parents=True,exist_ok=True)
        self.log=(self.folder/'decoder-stderr.log').open('x')
        self.process=subprocess.Popen([sys.executable,str(ROOT/'experiments/research_decoder.py')],
            cwd=ROOT,env=environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=self.log,text=True,bufsize=1)
        self.count=0

    def decode(self,packet):
        self.count+=1; out=self.folder/f'decode-{self.count:04d}.npz'
        self.process.stdin.write(json.dumps(dict(packet=str(Path(packet).resolve()),output=str(out.resolve())))+'\n')
        self.process.stdin.flush()
        ready,_,_=select.select([self.process.stdout],[],[],240)
        if not ready:
            raise TimeoutError('Source-free decode limit; worker stderr retained')
        line=self.process.stdout.readline()
        if not line:
            raise RuntimeError('Source-free decoder exited '+str(self.process.poll()))
        info=json.loads(line)
        if info['status']!='DECODED':
            raise RuntimeError(info)
        with np.load(out,allow_pickle=False) as data:
            y,mask,p=(data[k] for k in ('y','mask','protected'))
        # Only transient decoded arrays are deleted; packets and hashes persist.
        out.unlink()
        return y,mask,p,info

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.terminate(); self.process.wait(timeout=10)
        self.process.stdout.close()
        self.log.close()


def audit(x,y,mask,decoded_mask,protected,decoded_protected,denominator=1,cap=10000):
    if (x.shape!=y.shape or mask.shape!=x.shape or decoded_mask.shape!=x.shape
        or protected.shape!=x.shape or decoded_protected.shape!=x.shape):
        raise ValueError('Audit shapes')
    x=np.asarray(x,np.int64); y=np.asarray(y,np.int64)
    if denominator<1 or cap<0 or 4*x.size*max(int(np.abs(y).max()),cap*denominator)>2**62:
        raise ValueError('Exact sum safety')
    d=y-x*denominator
    error=0 if not d.any() else int(_maximum_rectangle(d))
    prefix=d.cumsum(0).cumsum(1)
    outside=int(np.count_nonzero((y<0)|(y>cap*denominator)))
    fractional=int(np.count_nonzero(y%denominator))
    return dict(max_rectangle_numerator=error,denominator=denominator,
        max_rectangle_error=error/denominator,max_abs_prefix_numerator=int(np.abs(prefix).max()),
        range_violations=outside,range_violation_fraction=outside/x.size,
        integer_violations=fractional,changed=int(np.count_nonzero(d)),
        mask_ok=bool(np.array_equal(mask,decoded_mask) and not y[mask].any()),
        protected_ok=bool(np.array_equal(protected,decoded_protected) and not d[protected].any()),
        valid_samples=int((~mask).sum()))


def legal(a,epsilon):
    return (a['range_violations']==0 and a['integer_violations']==0 and a['mask_ok']
        and a['protected_ok'] and a['max_rectangle_numerator']<=epsilon*a['denominator'])


@njit(cache=True)
def feasible_widths(x,y,band,cap,p):
    h,w=x.shape; up=np.zeros(w,np.int64); widths=np.zeros((h,w),np.int32)
    for i in range(h):
        low=np.empty(w+1,np.int64); high=np.empty(w+1,np.int64)
        low[w]=-band; high[w]=band
        for j in range(w-1,-1,-1):
            delta=up[j]-(up[j-1] if j else 0)
            if p[i,j]:
                low[j]=max(-band,low[j+1]-delta)
                high[j]=min(band,high[j+1]-delta)
            else:
                t=x[i,j]-delta
                low[j]=max(-band,low[j+1]+t-cap)
                high[j]=min(band,high[j+1]+t)
        a=np.int64(0); diagonal=np.int64(0)
        for j in range(w):
            old=up[j]; delta=old-diagonal; t=x[i,j]-delta
            if not p[i,j]:
                lo=max(low[j+1],a-t); hi=min(high[j+1],a-t+cap)
                widths[i,j]=hi-lo+1
            b=y[i,j]-t+a
            if not low[j+1]<=b<=high[j+1]:
                raise ValueError('Observed state outside viable suffix')
            diagonal=old; up[j]=b; a=b
    return widths
