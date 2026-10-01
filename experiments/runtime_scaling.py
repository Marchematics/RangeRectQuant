"""Fresh-worker native-image scaling, with construction and coding separated."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

import numpy as np
from controls.viable_greedy import row_greedy
from range_rect_quant.corridor import _row_fast
from controls import research_packet as packet
from research_common import ROOT,save,sha,environment


def construct_core(x,p,band,step,kernel=row_greedy):
    """Same frozen row choices, without materializing a full prefix audit."""
    y=np.empty_like(x); up=np.zeros(x.shape[1],np.int64)
    for i in range(x.shape[0]):
        y[i],up,_,_=kernel(x[i],up,band,step,10000,p[i])
    return y


def worker(size,epsilon,method,out):
    kernel=_row_fast if method=='Exact row search' else row_greedy
    tiny=np.zeros((2,2),np.int64); mask=np.zeros(tiny.shape,bool)
    # Compilation precedes input loading and every timed measurement.
    construct_core(tiny,mask,epsilon//4,max(1,epsilon//5),kernel)
    source=ROOT/'data/expanded_20261002/london-4096.npz'
    with np.load(source,allow_pickle=False) as z:
        off=(4096-size)//2
        raw=z['raw'][off:off+size,off:off+size].copy()
        p=z['mask'][off:off+size,off:off+size].copy()
    x=raw.astype(np.int64); x[p]=0; del raw
    times=[]; cores=[]; decodes=[]; files=[]; initial_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    config=dict(method=method,epsilon=epsilon); geo=dict(anchor='London nominal tile; metadata-only clamped 4096 crop',shape=list(x.shape),units='m2')
    for repetition in range(3):
        started=time.perf_counter()
        if method=='Fixed margin':
            blob,fees,_=packet.encode_fiber(x,p,epsilon//4,config,geo)
            core=None
        else:
            y=construct_core(x,p,epsilon//4,max(1,epsilon//5),kernel)
            core=time.perf_counter()-started
            blob,fees=packet.encode(y,p,max(1,epsilon//5),10000,config,geo)
            del y
        times.append(time.perf_counter()-started); cores.append(core); files.append(len(blob))
        before=time.perf_counter(); decoded,m,protected,meta=packet.decode(blob)
        decodes.append(time.perf_counter()-before)
        if repetition==0:
            # Audit outside encode/decode timings. Record whole-reference peak
            # including this audit, not an alleged O(W) process-memory bound.
            difference=decoded-x; prefix=difference.cumsum(0).cumsum(1)
            prefix_max=int(np.abs(prefix).max())
            if prefix_max>epsilon//4 or decoded.min()<0 or decoded.max()>10000 or not np.array_equal(decoded[p],x[p]):
                raise ValueError('Range/protection/prefix certificate')
            del difference,prefix
        del decoded,blob
    if len(set(files))!=1:
        raise ValueError('Deterministic complete files')
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report=dict(status='MEASURED',method=method,size=size,epsilon=epsilon,pixels=x.size,
        core_seconds=cores,encode_seconds=times,decode_seconds=decodes,packet_bytes=files[0],fees=fees,
        median_encode_mpixel_s=x.size/float(np.median(times))/1e6,
        median_decode_mpixel_s=x.size/float(np.median(decodes))/1e6,
        median_core_mpixel_s=x.size/float(np.median(cores))/1e6 if cores[0] is not None else None,
        process_peak_rss_bytes=int(peak),initial_peak_rss_bytes=int(initial_peak),
        rss_scope='macOS fresh worker peak including JIT, native input/output, coding and full-prefix audit',
        warm_compilation=True,max_abs_prefix=prefix_max,all_rectangle_bound=4*prefix_max,
        regional_budget_certified=True,source_sha256=sha(source),gpu_used=False,
        timing_scope='encode: construction plus paid file; decode: paid file to field; verification outside both',
        decode_source_used=False)
    save(out,report)


def run(out):
    if out.exists(): raise ValueError('Fresh scaling output')
    out.mkdir(parents=True)
    launch_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    save(out/'launch.json',dict(commit=launch_commit,source_sha256=sha(ROOT/'data/expanded_20261002/london-4096.npz'),
        script_sha256=sha(__file__),repetitions=3,worker_timeout_seconds=180,
        source='single native 4096 crop, nested resolutions',gpu_used=False))
    rows=[]
    for epsilon in (100,1000):
        for size in (256,512,1024,2048,4096):
            for method in ('RangeRectQuant','Exact row search','Fixed margin'):
                stem=f'{size}-e{epsilon}-'+method.lower().replace(' ','_')
                target=out/(stem+'.json')
                command=[sys.executable,str(Path(__file__).resolve()),'worker','--size',str(size),
                         '--epsilon',str(epsilon),'--method',method,'--out',str(target)]
                started=time.perf_counter()
                try:
                    completed=subprocess.run(command,env=environment(),capture_output=True,text=True,timeout=180)
                    (out/(stem+'.stdout.log')).write_text(completed.stdout)
                    (out/(stem+'.stderr.log')).write_text(completed.stderr)
                    if completed.returncode or not target.exists():
                        raise RuntimeError('Worker return '+str(completed.returncode))
                    row=json.loads(target.read_text())
                except subprocess.TimeoutExpired:
                    row=dict(status='TIMEOUT',method=method,size=size,epsilon=epsilon,timeout_seconds=180)
                    save(target,row)
                except Exception as e:
                    row=dict(status='EXCEPTION',method=method,size=size,epsilon=epsilon,error=str(e))
                    save(target,row)
                row['worker_wall_seconds']=time.perf_counter()-started
                rows.append(row); save(out/'report.json',dict(status='RUNNING',rows=rows))
                print(size,epsilon,method,row['status'],row.get('encode_seconds'),flush=True)
    save(out/'report.json',dict(status='COMPLETE_ATTEMPTED_SCALING',rows=rows,
        measured=sum(r['status']=='MEASURED' for r in rows),timeouts=sum(r['status']=='TIMEOUT' for r in rows),
        exceptions=sum(r['status']=='EXCEPTION' for r in rows),gpu_used=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['run','worker']); p.add_argument('--out',type=Path,required=True)
    p.add_argument('--size',type=int); p.add_argument('--epsilon',type=int); p.add_argument('--method')
    a=p.parse_args()
    run(a.out.resolve()) if a.action=='run' else worker(a.size,a.epsilon,a.method,a.out.resolve())
