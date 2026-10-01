"""Independent integer geometry, direct slices, and fresh source-free replay."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from numba import njit
from range_rect_quant.packet import HEADER, BODY_HEADER, digest, decode
from built_area_metrics import service_contract
from run_pilot import ROOT, PREFLIGHT, ENVIRONMENT, sha, write_json, sources, verify_preserved


@njit(cache=True)
def independent_rectangle_max(d):
    # Different orientation/recurrence from row-band Kadane used by the runner.
    h,w=d.shape
    row_prefix=np.zeros((h,w+1),np.int64)
    for r in range(h):
        for c in range(w):row_prefix[r,c+1]=row_prefix[r,c]+d[r,c]
    result=np.int64(0)
    for left in range(w):
        for right in range(left+1,w+1):
            current=np.int64(0);minimum=np.int64(0);maximum=np.int64(0)
            for r in range(h):
                current+=row_prefix[r,right]-row_prefix[r,left]
                minimum=min(minimum,current);maximum=max(maximum,current)
            result=max(result,maximum-minimum)
    return result


def replay(source_dir,out):
    if out.exists():raise SystemExit('Refusing to overwrite replay')
    out.mkdir(parents=True)
    start=time.perf_counter();preserved=verify_preserved()
    preflight=json.loads(PREFLIGHT.read_text());binding_count=0
    for group in ('files','runtimes'):
        for name,expected in preflight[group].items():
            if sha(ROOT/name if group=='files' else Path(name))!=expected:raise ValueError('Frozen binding')
            binding_count+=1
    records={s['site']:s for s in sources()};q=np.load(ROOT/'data/queries.npy',allow_pickle=False)
    rows=json.loads((source_dir/'ledger.json').read_text());report=json.loads((source_dir/'report.json').read_text())
    from run_pilot import summarize
    regenerated=summarize(rows,report['elapsed_seconds'])
    if regenerated!={k:v for k,v in report.items() if k!='preserved'}:raise ValueError('Summary regeneration')
    artifacts=0;queries_checked=0;float_counts=Counter();checked=[]
    for row in rows:
        if row['status']!='DECODED_AND_AUDITED':raise ValueError('Incomplete pilot case')
        for key in ('packet','body','output','worker_report'):
            if sha(ROOT/row[key])!=row[key+'_sha256']:raise ValueError('Saved artifact SHA')
            artifacts+=1
        raw=(ROOT/row['packet']).read_bytes();magic,h,w,ml,cl,bl,expected=HEADER.unpack_from(raw)
        if row['packet_bytes']!=len(raw) or sum(row['fees'].values())!=len(raw):raise ValueError('Complete fees')
        body=raw[HEADER.size+ml+cl:-32]
        if body!=(ROOT/row['body']).read_bytes():raise ValueError('Paid body')
        parts=BODY_HEADER.unpack_from(body);detail=row['body_detail']
        if parts!=(detail['quotient_bytes'],detail['remainder_bytes'],detail['source_zero_bitmap_bytes']) or BODY_HEADER.size+sum(parts)!=bl:raise ValueError('Body fee segments')
        output=out/(row['id']+'.npz');worker_report=out/(row['id']+'.json')
        argv=[sys.executable,str(ROOT/'experiments/worker.py'),str(ROOT/row['packet']),str(output),str(worker_report),'--queries',str(ROOT/'data/queries.npy')]
        process=subprocess.run(argv,capture_output=True,text=True,env=dict(os.environ,**ENVIRONMENT),timeout=120)
        (out/(row['id']+'.stdout.log')).write_text(process.stdout);(out/(row['id']+'.stderr.log')).write_text(process.stderr)
        if process.returncode:raise ValueError('Fresh source-free decode')
        with np.load(output,allow_pickle=False) as bundle:y,mask,zero=bundle['y'],bundle['mask'],bundle['zero_protect']
        with np.load(ROOT/row['output'],allow_pickle=False) as bundle:
            if not all(np.array_equal(a,bundle[k]) for a,k in ((y,'y'),(mask,'mask'),(zero,'zero_protect'))):raise ValueError('Fresh vs saved field')
        source=records[row['site']];x=source['x'];d=y.astype(np.int64)-x
        maximum=int(independent_rectangle_max(d))
        if y.dtype!=np.float64 or np.any(y!=np.rint(y)) or np.any((y<0)|(y>10000)) or not np.array_equal(mask,source['mask']) or y[mask].any():raise ValueError('Integer/range/mask')
        if expected!=digest(y,mask):raise ValueError('Paid full digest')
        meta=decode(raw)[2]
        if meta['geo']!=source['geo']:raise ValueError('Geospatial metadata')
        if row['mode']=='identity' and np.any(d):raise ValueError('Identity')
        if row['mode']=='zero-preserve' and (np.any(y[x==0]) or not np.array_equal(zero,(x==0)&~mask)):raise ValueError('Zero protection')
        if np.abs(d.cumsum(0).cumsum(1)).max()>meta['band']:raise ValueError('Full prefix invariant')
        fine=int(np.count_nonzero(y.astype(np.int64)%row['step']));changed=int(np.count_nonzero(d))
        if fine!=row['quantizer']['off_lattice'] or changed!=row['quantizer']['changed']:raise ValueError('Mechanism counts')
        workers=[json.loads(worker_report.read_text()),json.loads((ROOT/row['worker_report']).read_text())]
        for rectangle_index,rectangle in enumerate(q):
            a,b,c,e=map(int,rectangle);n=int((~mask[a:b,c:e]).sum())
            value=float(y[a:b,c:e].sum()) if n else None
            for worker in workers:
                if len(worker['answers'])!=1024 or worker['answers'][rectangle_index]!=dict(sum=value,count=n):raise ValueError('Independent direct slice answer')
            queries_checked+=1
        interval=service_contract(x,y,mask,mask,100)
        floats={}
        for epsilon in (100,1000):
            verdict='LEGAL' if maximum<=epsilon else 'ILLEGAL'
            if row['contracts'][str(epsilon)]['status']!=verdict or row['contracts'][str(epsilon)]['all_rectangle_query_error_exact']!=maximum:raise ValueError('Independent maximum/verdict')
            fs='LEGAL' if interval['all_rectangle_query_error_upper']<=epsilon else 'ILLEGAL' if interval['all_rectangle_query_error_lower']>epsilon else 'UNCERTIFIED'
            float_counts[fs]+=1;floats[str(epsilon)]=fs
        checked.append(dict(id=row['id'],independent_integer_maximum=maximum,fine=fine,changed=changed,float_verdicts=floats))
        print(row['id'],'REPLAY_PASS',maximum,flush=True)
    write_json(out/'report.json',dict(status='PASS_FRESH_SOURCE_FREE_REPLAY_AND_INDEPENDENT_GEOMETRY',
        original_report_sha256=sha(source_dir/'report.json'),artifact_sha_checks=artifacts,
        frozen_file_runtime_bindings=binding_count,fresh_source_free_decodes=len(checked),direct_slice_queries_checked=queries_checked,
        float_interval_verdicts=dict(float_counts),cases=checked,preserved=verify_preserved(),elapsed_seconds=time.perf_counter()-start,
        human_review=False,sota_established=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    replay(a.source.resolve(),a.out.resolve())


if __name__=='__main__':main()
