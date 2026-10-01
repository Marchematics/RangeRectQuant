"""One frozen, paid 24-packet real development pilot; no held-out claims."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
from range_rect_quant.packet import MODES, SETTINGS, encode, digest
from built_area_integer_metrics import integer_error, contract
from built_area_metrics import queries

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / 'integration/checks/preflight_20261001.json'
ENVIRONMENT = dict(CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   PYTHONPATH=str(ROOT/'src')+os.pathsep+str(ROOT/'experiments'))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args]).decode().strip()


def verify_preserved():
    supplied=json.loads((ROOT/'integration/IMPORT_MANIFEST.json').read_text())
    archive=ROOT/'imports/LinewiseROI_Research_Plan_and_Probe_20261001.zip'
    if sha(archive)!=supplied['archive_sha256'] or archive.stat().st_size!=supplied['archive_bytes']:raise ValueError('Supplied ZIP changed')
    for row in supplied['files']:
        p=ROOT/row['path']
        if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('Supplied file changed: '+row['path'])
    refs=json.loads((ROOT/'integration/REFERENCE_MANIFEST.json').read_text())
    for path,row in refs['previous_files'].items():
        if (ROOT/path).stat().st_size!=row['bytes'] or sha(ROOT/path)!=row['sha256']:raise ValueError('Prior evidence changed')
    # This audit is local lineage evidence, not a portability dependency of RQ01.
    previous=ROOT.parent/'LinewiseROI'
    imported=json.loads((previous/'integration/IMPORT_MANIFEST.json').read_text())
    if sha(previous/'integration/IMPORT_MANIFEST.json')!=refs['previous_import_manifest_sha256']:raise ValueError('Original manifest changed')
    for row in imported['files']:
        p=previous/row['path']
        if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('745 historical original changed')
    return dict(supplied_files=len(supplied['files']),historical_files=len(imported['files']),previous_artifacts=len(refs['previous_files']))


def sources():
    refs=json.loads((ROOT/'integration/REFERENCE_MANIFEST.json').read_text())
    output=[]
    for row in refs['sources']:
        p=ROOT/row['local_source']
        if sha(p)!=row['source_sha256']:raise ValueError('Copied source hash')
        with np.load(p,allow_pickle=False) as bundle:raw,mask=bundle['raw'],bundle['mask']
        if raw.shape!=(512,512) or raw.dtype!=np.uint16 or mask.dtype!=bool or not np.array_equal(mask,raw==65535):raise ValueError('Source dtype/mask')
        x=raw.astype(np.int64);x[mask]=0
        if np.any(x>10000):raise ValueError('Source cap')
        output.append(dict(row,x=x,mask=mask))
    return output


def freeze():
    import numba, llvmlite.binding
    if PREFLIGHT.exists():raise SystemExit('Refusing to overwrite frozen preflight')
    paths=set()
    for directory in ('src','tests','experiments','data','evidence/previous'):
        paths.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and
                     '__pycache__' not in p.parts and p.suffix not in ('.nbc','.nbi','.pyc'))
    paths.update(ROOT/p for p in ('docs/PROTOCOL_20261001.md','docs/METHOD_20261001.md',
        'requirements.txt','integration/IMPORT_MANIFEST.json','integration/REFERENCE_MANIFEST.json',
        'integration/checks/tests_attempt1_20261001.log','integration/checks/tests_attempt2_20261001.log',
        'integration/checks/supplied_replay_20261001.json'))
    preserved=verify_preserved()
    sources()
    q=np.load(ROOT/'data/queries.npy',allow_pickle=False)
    if not np.array_equal(q,queries((512,512))):raise ValueError('Unchanged common query array')
    runtime=[Path(sys.executable).resolve(),Path(np._core._multiarray_umath.__file__).resolve(),
             Path(llvmlite.binding.ffi.lib._name).resolve()]
    write_json(PREFLIGHT,dict(status='PASS_FROZEN_PAID_PILOT_PREFLIGHT',
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},
        runtimes={str(p):sha(p) for p in runtime},versions={p:importlib.metadata.version(p) for p in ('numpy','numba','llvmlite')},
        python=sys.version,environment=ENVIRONMENT,preserved=preserved,
        planned_packets=24,planned_budget_verdicts=48,no_real_source_encoding_during_freeze=True))


def summarize(rows,seconds):
    refs=json.loads((ROOT/'integration/REFERENCE_MANIFEST.json').read_text())
    comparisons=[];gates={}
    for epsilon,step in ((100,20),(1000,200)):
        selected=[r for r in rows if r['step']==step and r['mode']=='lossy']
        previous=[r for r in refs['comparisons'] if r['epsilon']==epsilon]
        for scope,key in (('plan_lossless','lossless_bytes'),('strong_prior_including_conditional_haar','strong_prior_bytes')):
            old=sum(r[key] for r in previous);new=sum(r.get('packet_bytes',0) for r in selected)
            valid=len(selected)==4 and all(r['status']=='DECODED_AND_AUDITED' and r.get('contracts',{}).get(str(epsilon),{}).get('status')=='LEGAL' and r['contracts'][str(epsilon)]['changed_values']>0 for r in selected)
            wins=0;maximum_expansion=0.
            for prior in previous:
                candidate=next((r for r in selected if r['site']==prior['site']),None)
                good=candidate is not None and candidate['status']=='DECODED_AND_AUDITED' and candidate.get('contracts',{}).get(str(epsilon),{}).get('status')=='LEGAL'
                n=candidate.get('packet_bytes') if candidate else None
                wins+=int(good and n<prior[key]);maximum_expansion=max(maximum_expansion,n/prior[key]-1 if n is not None else 1.)
                comparisons.append(dict(epsilon=epsilon,scope=scope,site=prior['site'],baseline_bytes=prior[key],candidate_bytes=n,legal=good))
            gain=1-new/old if valid else None
            gates[f'{epsilon}:{scope}']=dict(all_legal_nontrivial=valid,strict_wins=wins,baseline_bytes=old,
                candidate_bytes=new if valid else None,reduction_fraction=gain,maximum_source_expansion_fraction=maximum_expansion,
                passed=bool(valid and wins>=3 and gain>=.10 and maximum_expansion<=.05))
    counts=Counter(c['status'] for r in rows for c in r.get('contracts',{}).values())
    return dict(status='COMPLETE_FROZEN_REAL_PILOT' if len(rows)==24 and all(r['status']=='DECODED_AND_AUDITED' for r in rows) else 'PARTIAL',
        planned_packets=24,attempted_packets=len(rows),full_source_free_decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
        service_verdicts=sum(counts.values()),statuses=dict(counts),exception_packets=sum(r['status']=='EXCEPTION' for r in rows),
        gates=gates,comparisons=comparisons,elapsed_seconds=seconds,previously_observed_development_sources=True,
        novelty_established=False,sota_established=False,full_goal_completed=False,gpu_used=False)


def run(out):
    if out.exists() or not out.is_relative_to(ROOT/'results'):raise SystemExit('Need fresh results directory')
    if git('status','--porcelain'):raise SystemExit('Need clean tree')
    revision=git('rev-parse','HEAD')
    if git('ls-remote','origin','refs/heads/main').split()[0]!=revision:raise SystemExit('Need pushed snapshot')
    preflight=json.loads(PREFLIGHT.read_text())
    for group in ('files','runtimes'):
        for path,d in preflight[group].items():
            if sha(ROOT/path if group=='files' else Path(path))!=d:raise ValueError('Frozen file/runtime changed: '+path)
    verify_preserved();records=sources();q=np.load(ROOT/'data/queries.npy',allow_pickle=False)
    out.mkdir(parents=True)
    for folder in ('packets','bodies','decodes','workers','attempts'):(out/folder).mkdir()
    write_json(out/'launch.json',dict(commit=revision,clean_pushed_tree=True,preflight_sha256=sha(PREFLIGHT),
        argv=sys.argv,environment=ENVIRONMENT,gpu_used=False,started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    started=time.perf_counter();rows=[]
    for source in records:
        for step in (20,200):
            for mode in MODES:
                name=f"{source['site']}-q{step}-{mode}"
                row=dict(id=name,site=source['site'],step=step,mode=mode,status='EXCEPTION',source=source['local_source'],source_sha256=source['source_sha256'])
                if time.perf_counter()-started>1800:break
                t=time.perf_counter()
                try:
                    packet,body,info=encode(source['x'],source['mask'],step,mode,source['geo'])
                    row.update(encode_seconds=time.perf_counter()-t,packet_bytes=len(packet),**info)
                    if sum(info['fees'].values())!=len(packet):raise ValueError('Paid total')
                    for key,raw,suffix in (('packet',packet,'.rq01'),('body',body,'.body')):
                        p=out/('packets' if key=='packet' else 'bodies')/(name+suffix);p.write_bytes(raw)
                        row[key]=str(p.relative_to(ROOT));row[key+'_sha256']=sha(p)
                    output=out/'decodes'/(name+'.npz');report=out/'workers'/(name+'.json')
                    argv=[sys.executable,str(ROOT/'experiments/worker.py'),str(ROOT/row['packet']),str(output),str(report),'--queries',str(ROOT/'data/queries.npy')]
                    cold=time.perf_counter()
                    worker=subprocess.run(argv,env=dict(os.environ,**ENVIRONMENT),capture_output=True,text=True,timeout=120)
                    for stream in ('stdout','stderr'):(out/'workers'/(name+'.'+stream+'.log')).write_text(getattr(worker,stream))
                    row.update(worker_argv=argv,worker_returncode=worker.returncode,cold_process_seconds=time.perf_counter()-cold)
                    if worker.returncode!=0:raise RuntimeError('Source-free worker failure')
                    saved=json.loads(report.read_text())
                    with np.load(output,allow_pickle=False) as bundle:y,mask,zero=bundle['y'],bundle['mask'],bundle['zero_protect']
                    if y.dtype!=np.float64 or mask.dtype!=bool or zero.dtype!=bool:raise ValueError('Independent decode dtype')
                    error=integer_error(source['x'],y,source['mask'],mask)
                    row['contracts']={str(e):contract(error,e) for e in (100,1000)}
                    prefix=(y.astype(np.int64)-source['x']).cumsum(0).cumsum(1)
                    if np.abs(prefix).max()>SETTINGS[step][1]:raise ValueError('Prefix invariant contradicted')
                    if mode=='identity' and error['changed_values']:raise ValueError('Identity changed source')
                    if mode=='zero-preserve' and (np.any(y[source['x']==0]) or not np.array_equal(zero,(source['x']==0)&~source['mask'])):raise ValueError('Source-zero preservation')
                    max_query=0
                    for rectangle,answer in zip(q,saved['answers']):
                        a,b,c,d=map(int,rectangle);count=int((~mask[a:b,c:d]).sum())
                        value=float(y[a:b,c:d].sum()) if count else None
                        if answer!=dict(sum=value,count=count):raise ValueError('Source-free query answer')
                        if count:max_query=max(max_query,abs(int(y[a:b,c:d].sum())-int(source['x'][a:b,c:d].sum())))
                    if len(saved['answers'])!=1024 or max_query>error['all_rectangle_query_error_exact']:raise ValueError('Query count/rectangle consistency')
                    row.update(fixed_1024_query_max_error=max_query,cold_decode_cache_first_query_seconds=saved['first_query_completed_perf_counter']-cold,
                        warm_1024_query_seconds=saved['warm_1024_query_seconds'],decoder_self_peak_rss_bytes=saved['process_peak_rss_bytes'])
                    for key,p in (('output',output),('worker_report',report)):
                        row[key]=str(p.relative_to(ROOT));row[key+'_sha256']=sha(p)
                    if digest(y,mask)!=packet[24:56]:raise ValueError('Paid decoded digest')
                    row['status']='DECODED_AND_AUDITED'
                except Exception as error:
                    row.update(error=type(error).__name__+': '+str(error),traceback=traceback.format_exc())
                row['attempt_wall_seconds']=time.perf_counter()-t
                rows.append(row);write_json(out/'attempts'/(name+'.json'),row);write_json(out/'ledger.json',rows)
                print(json.dumps(dict(id=name,status=row['status'],bytes=row.get('packet_bytes'),fine=row.get('quantizer',{}).get('off_lattice'),error=row.get('contracts',{}).get('1000',{}).get('all_rectangle_query_error_exact'))),flush=True)
                if time.perf_counter()-started>1800:break
            if time.perf_counter()-started>1800:break
        if time.perf_counter()-started>1800:break
    report=summarize(rows,time.perf_counter()-started);report['preserved']=verify_preserved()
    write_json(out/'report.json',report)
    print(json.dumps(report,indent=2),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--freeze',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.freeze:freeze()
    elif a.out:run(a.out.resolve())
    else:p.error('Need --freeze or --out')


if __name__=='__main__':main()
