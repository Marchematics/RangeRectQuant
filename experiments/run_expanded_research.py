"""Fixed expanded geography/frontier plus closest-mechanism and protected sweeps."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np

from controls.viable_greedy import reconstruct
from controls.closest_mechanisms import candidates
from controls import research_packet as transport
from research_common import ROOT,LEGACY,ColdDecoder,audit,legal,sha,save,environment,feasible_widths
from built_area_discrete_packet import grid,encode as native_encode

PREFLIGHT=ROOT/'integration/checks/expanded_encoding_preflight_20261002_v2.json'
MANIFEST=ROOT/'data/expanded_20261002/manifest_v2.json'
BUDGETS=(25,50,100,250,500,1000,2500,5000)


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()


def freeze():
    if PREFLIGHT.exists():
        raise ValueError('Refuse overwrite encoding freeze')
    manifest=json.loads(MANIFEST.read_text())
    if manifest['status']!='PASS_40_NATIVE_LOCATIONS':
        raise ValueError('Forty acquired locations required')
    native=json.loads((LEGACY/'integration/checks/built_area_discrete_preflight_20261001.json').read_text())
    files={}
    for name,digest in native['bindings_sha256'].items():
        path=LEGACY/name
        if sha(path)!=digest:
            raise ValueError('Native source binding '+name)
        files[str(path)]=digest
    runtimes=native['runtime_sha256']
    for name,digest in runtimes.items():
        if sha(name)!=digest:
            raise ValueError('Native runtime binding '+name)
    paths=[Path(__file__),PREFLIGHT.parent.parent/'expanded_assets_20261002.json',MANIFEST,
        ROOT/'docs/EXPANDED_RESEARCH_PROTOCOL_20261002.md',ROOT/'tests/test_research_controls.py',
        ROOT/'controls/viable_greedy.py',ROOT/'controls/closest_mechanisms.py',
        ROOT/'controls/research_packet.py',ROOT/'experiments/research_common.py',ROOT/'experiments/research_decoder.py',
        LEGACY/'experiments/built_area_fiber_packet.py',LEGACY/'experiments/built_area_integer_metrics.py']
    for source in manifest['rows']:
        for item in source['sources']:
            p=ROOT/item['source']
            if sha(p)!=item['source_sha256']:
                raise ValueError('New source binding')
            paths.append(p)
    old=json.loads((ROOT/'data/heldout_20261001/manifest.json').read_text())
    for row in old['rows']:
        paths.append(ROOT/row['source'])
    for p in paths:
        files[str(p)]=sha(p)
    save(PREFLIGHT,dict(status='FROZEN_BEFORE_EXPANDED_ENCODING',files=files,runtimes=runtimes,
        native_grid=grid(),budgets=list(BUDGETS),sizes=[256,512,1024],locations=40,
        expected_frontier_packets=6600,expected_stress_packets=56,expected_protected_packets=40,
        protected_seed=20261002,protected_fractions=[0,.001,.01,.05,.1],
        packet_storage='.aris/evidence/expanded_20261002',sourcefree_decoder='separate persistent subprocess',
        gpu_used=False))


def check_launch():
    if git('status','--porcelain') or git('ls-remote','origin','refs/heads/main').split()[0]!=git('rev-parse','HEAD'):
        raise ValueError('Clean pushed tree required before encoding')
    frozen=json.loads(PREFLIGHT.read_text())
    for group in ('files','runtimes'):
        for p,digest in frozen[group].items():
            if sha(p)!=digest:
                raise ValueError('Frozen '+group+' '+p)
    if frozen['native_grid']!=grid() or frozen['budgets']!=list(BUDGETS):
        raise ValueError('Matrix differs from freeze')
    return frozen


def center(a,size):
    h,w=a.shape; r=(h-size)//2; c=(w-size)//2
    return a[r:r+size,c:c+size].copy()


def crop_geo(geo,original,size):
    geo=dict(geo); affine=list(geo['affine']); shift=(original-size)//2
    affine[2]+=shift*affine[0]+shift*affine[1]
    affine[5]+=shift*affine[3]+shift*affine[4]
    geo['affine']=affine; geo['shape']=[size,size]
    return geo


def attempt(folder,storage,stem,x,mask,p,geo,cfg,decoder,audit_cache):
    row=dict(id=stem,configuration=cfg,status='EXCEPTION'); started=time.perf_counter()
    try:
        cfg=dict(cfg); family=cfg['family']; detail={}
        if family=='baseline':
            commands=[]; body_path=storage/(stem+'.body')
            blob,native_info=native_encode(x,mask,cfg['config'],geo,body_path,commands)
            fees={k:v for k,v in native_info.items() if k.endswith('_bytes')}
            row['native_encoder_info']=native_info
            body_path.unlink(); row['native_encode_commands']=commands
        elif family=='fixed-margin':
            blob,fees,detail=transport.encode_fiber(x,mask,cfg['margin'],cfg,geo)
        else:
            epsilon=cfg['epsilon']; q=max(1,epsilon//5); denominator=1
            if family=='RangeRectQuant':
                construction_start=time.perf_counter()
                y,detail=reconstruct(x,epsilon//4,q,10000,p)
                row['construction_and_audit_seconds']=time.perf_counter()-construction_start
                widths=feasible_widths(x,y,epsilon//4,10000,p)
                fine=(y%q!=0)&~p
                if (widths[fine]>=q).any():
                    raise ValueError('Fine bottleneck lemma violated')
                detail.update(unprotected_fine=int(fine.sum()),
                    unprotected_narrow=int(np.count_nonzero((widths<q)&~p)),
                    wide_interval_pixels=int(np.count_nonzero((widths>=q)&~p)),
                    protected_fine=int(np.count_nonzero((y%q!=0)&p)))
                if stem=='cairo-512-e1000-RangeRectQuant':
                    np.savez_compressed(folder/'mechanism_example.npz',x=x,y=y,widths=widths,protected=p)
            else:
                options={a[0]:a[1:] for a in candidates(x,10000,epsilon)}
                y,denominator,q,mechanism=options[family]; detail['mechanism']=mechanism
            blob,fees=transport.encode(y,mask,q,10000,cfg,geo,p,denominator)
        packet=storage/(stem+'.packet')
        if packet.exists():
            raise ValueError('Refuse overwrite packet')
        packet.write_bytes(blob)
        encoded=time.perf_counter()
        y,decoded_mask,decoded_p,decoded=decoder.decode(packet)
        denominator=decoded['meta'].get('denominator',1)
        identity=hashlib.sha256(y.astype('<i8').tobytes()+decoded_mask.tobytes()+decoded_p.tobytes()
                                  +str(denominator).encode()).hexdigest()
        if identity not in audit_cache:
            audit_cache[identity]=audit(x,y,mask,decoded_mask,p,decoded_p,denominator)
        checks=audit_cache[identity]
        row.update(status='DECODED_AND_AUDITED',packet=str(packet.relative_to(ROOT)),packet_bytes=len(blob),
            packet_sha256=hashlib.sha256(blob).hexdigest(),fees=fees,
            encode_seconds=encoded-started,decoder=decoded,audit=checks,mechanism=detail,
            legal_at={str(e):legal(checks,e) for e in BUDGETS},
            elapsed_seconds=time.perf_counter()-started)
        if len(blob)!=sum(fees.values()):
            raise ValueError('Paid byte decomposition')
    except Exception as e:
        row.update(error=type(e).__name__+': '+str(e),traceback=traceback.format_exc(),
                   elapsed_seconds=time.perf_counter()-started)
    save(folder/'attempts'/(stem+'.json'),row)
    return row


def case(task):
    os.environ.update(environment())
    source,size,out,packet_root=task
    source_path=ROOT/source['source']
    if sha(source_path)!=source['source_sha256']:
        raise ValueError('Worker source binding')
    with np.load(source_path,allow_pickle=False) as data:
        raw,mask=center(data['raw'],size),center(data['mask'],size)
    x=raw.astype(np.int64); x[mask]=0
    name=source['site']+f'-{size}'
    folder=out/name; folder.mkdir(); storage=packet_root/name; storage.mkdir(parents=True)
    geo=crop_geo(source['geo'],1024,size); decoder=ColdDecoder(folder/'decoder'); cache={}; rows=[]
    configs=([dict(family='RangeRectQuant',epsilon=e) for e in BUDGETS]+
             [dict(family='fixed-margin',margin=m) for m in (0,*(e//4 for e in BUDGETS))]+
             [dict(family='baseline',config=cfg) for cfg in grid()])
    try:
        for index,cfg in enumerate(configs):
            stem=f'{name}-{index:02d}-{cfg["family"]}'
            row=attempt(folder,storage,stem,x,mask,mask,geo,cfg,decoder,cache)
            rows.append(row)
            save(folder/'ledger.json',dict(site=source['site'],size=size,rows=rows,status='RUNNING',
                                          crop_uint16_sha256=hashlib.sha256(raw.astype('<u2').tobytes()).hexdigest()))
    finally:
        decoder.close()
    report=dict(site=source['site'],size=size,source=source['source'],source_sha256=sha(source_path),
        status='COMPLETE' if len(rows)==55 else 'PARTIAL',
        exceptions=sum(r['status']=='EXCEPTION' for r in rows),rows=rows,
        distinct_decoded_fields_audited=len(cache))
    save(folder/'ledger.json',report)
    return report


def summarize(out):
    cases=[json.loads(p.read_text()) for p in sorted(out.glob('*/ledger.json'))]
    frontier=[]
    for size in (256,512,1024):
        selected=[c for c in cases if c['size']==size]
        for e in BUDGETS:
            paired=[]; totals={k:0 for k in ('RangeRectQuant','fixed-margin','sz3','mgard','qpet','lossless','external-best')}
            counts={k:0 for k in totals}
            for c in selected:
                usable=[r for r in c['rows'] if r['status']=='DECODED_AND_AUDITED' and r['legal_at'][str(e)]]
                groups={k:[] for k in totals}
                for r in usable:
                    cfg=r['configuration']; family=cfg['family']
                    if family=='RangeRectQuant':
                        if cfg['epsilon']==e: groups[family].append(r)
                        continue
                    groups['external-best'].append(r)
                    if family=='fixed-margin': groups[family].append(r)
                    elif cfg['config']['backend'] in ('sz3','mgard','qpet'):
                        groups[cfg['config']['backend']].append(r)
                    if r['audit']['changed']==0:
                        groups['lossless'].append(r)
                best={k:min(g,key=lambda r:(r['packet_bytes'],r['id'])) for k,g in groups.items() if g}
                for k,r in best.items(): totals[k]+=r['packet_bytes']; counts[k]+=1
                main,base=best.get('RangeRectQuant'),best.get('external-best')
                paired.append(dict(site=c['site'],main_bytes=main['packet_bytes'] if main else None,
                    baseline_bytes=base['packet_bytes'] if base else None,
                    reduction=1-main['packet_bytes']/base['packet_bytes'] if main and base else None,
                    baseline_configuration=base['configuration'] if base else None))
            frontier.append(dict(size=size,epsilon=e,locations=len(selected),totals_bytes=totals,
                qualifying_locations=counts,bpp={k:8*v/(40*size*size) if counts[k]==40 else None for k,v in totals.items()},
                reduction_fraction=1-totals['RangeRectQuant']/totals['external-best']
                    if counts['RangeRectQuant']==40 and counts['external-best']==40 else None,
                strict_wins=sum(p['reduction'] is not None and p['reduction']>0 for p in paired),pairs=paired))
    complete=len(cases)==120 and all(c['status']=='COMPLETE' for c in cases)
    report=dict(status='COMPLETE_FIXED_40_LOCATION_MATRIX' if complete else 'PARTIAL',
        cases_completed=len(cases),locations_completed=len({c['site'] for c in cases}),
        attempted_packets=sum(len(c['rows']) for c in cases),
        sourcefree_decodes=sum(r['status']=='DECODED_AND_AUDITED' for c in cases for r in c['rows']),
        exceptions=sum(c['exceptions'] for c in cases),frontier=frontier,
        paired_unit='city; resolutions are nested',broad_codec_sota_established=False,gpu_used=False)
    save(out/'report.json',report)
    return report


def run_frontier(out,workers):
    frozen=check_launch()
    if out.exists() or workers not in (1,2):
        raise ValueError('Fresh result directory and <=2 CPU case workers')
    packet_root=ROOT/frozen['packet_storage']/'frontier'
    packet_root.mkdir(parents=True); out.mkdir(parents=True)
    save(out/'launch.json',dict(commit=git('rev-parse','HEAD'),preflight_sha256=sha(PREFLIGHT),
        started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),case_workers=workers,
        native_threads=1,packet_storage=str(packet_root),sourcefree_decoding=True))
    manifest=json.loads(MANIFEST.read_text()); tasks=[]
    for r in manifest['rows']:
        source=next(s for s in r['sources'] if s['shape']==[1024,1024])
        source=dict(source,site=r['site'])
        for size in (256,512,1024): tasks.append((source,size,out,packet_root))
    # The case worker owns construction/audit; its decoder never receives X.
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(case,t):t for t in tasks}
        for f in as_completed(futures):
            report=f.result(); print(report['site'],report['size'],report['exceptions'],flush=True)
    summarize(out)


def run_stress(out,protect=False):
    frozen=check_launch()
    if out.exists(): raise ValueError('Fresh result directory')
    out.mkdir(parents=True); storage=ROOT/frozen['packet_storage']/('protected' if protect else 'closest')
    storage.mkdir(parents=True)
    save(out/'launch.json',dict(commit=git('rev-parse','HEAD'),preflight_sha256=sha(PREFLIGHT),
                              sourcefree_decoding=True,protected_sweep=protect))
    rows=[]; decoder=ColdDecoder(out/'decoder'); sources=json.loads((ROOT/'data/heldout_20261001/manifest.json').read_text())['rows']
    try:
        for source in sources:
            with np.load(ROOT/source['source'],allow_pickle=False) as z:
                x=z['raw'].astype(np.int64); mask=z['mask']; x[mask]=0
            rng=np.random.default_rng(20261002); indices=rng.permutation(np.flatnonzero(~mask)); cache={}
            for e in (100,1000):
                if protect:
                    configurations=[dict(family='RangeRectQuant',epsilon=e,protected_fraction=f)
                                    for f in (0,.001,.01,.05,.1)]
                else:
                    configurations=[dict(family=name,epsilon=e) for name in
                        ('sigma-delta','sigma-delta-clip','sigma-delta-clip-integer','sigma-delta-project',
                         'prefix-round','prefix-round-clip','RangeRectQuant')]
                for cfg in configurations:
                    p=mask.copy()
                    if protect:
                        p.ravel()[indices[:round(len(indices)*cfg['protected_fraction'])]]=True
                    stem=f'{source["site"]}-512-e{e}-{cfg["family"]}'
                    if protect: stem+='-p'+str(cfg['protected_fraction'])
                    # The protected set affects audit identity even when decoded Y happens to match.
                    row=attempt(out,storage,stem,x,mask,p,source['geo'],cfg,decoder,cache)
                    row.update(site=source['site'],size=512,source_sha256=source['source_sha256'])
                    rows.append(row); save(out/'ledger.json',dict(status='RUNNING',rows=rows))
                    print(stem,row['status'],row.get('audit',{}).get('max_rectangle_error'),flush=True)
    finally: decoder.close()
    expected=40 if protect else 56
    report=dict(status='COMPLETE' if len(rows)==expected else 'PARTIAL',attempted_packets=len(rows),
        sourcefree_decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
        exceptions=sum(r['status']=='EXCEPTION' for r in rows),
        joint_valid=sum(r['status']=='DECODED_AND_AUDITED' and r['legal_at'][str(r['configuration']['epsilon'])] for r in rows),
        gpu_used=False)
    save(out/'ledger.json',dict(status=report['status'],rows=rows)); save(out/'report.json',report)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','frontier','closest','protected','summarize'])
    p.add_argument('--out',type=Path); p.add_argument('--workers',type=int,default=2); a=p.parse_args()
    if a.action=='freeze': freeze()
    elif a.action=='frontier': run_frontier(a.out.resolve(),a.workers)
    elif a.action=='summarize': summarize(a.out.resolve())
    else: run_stress(a.out.resolve(),a.action=='protected')
