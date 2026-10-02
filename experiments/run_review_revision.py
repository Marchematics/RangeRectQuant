"""Fixed source-free representation, step, hierarchy and density experiments."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import traceback
import numpy as np
from controls import research_packet,review_packet
from controls.viable_greedy import reconstruct
from controls.hierarchical_sum import reconstruct as hierarchy
from controls.review_geometry import certificate
from research_common import ROOT,LEGACY,environment,save,sha,_maximum_rectangle
from built_area_discrete_packet import grid,encode as native_encode

OUT=ROOT/'results/review_revision_20261002'
PREFLIGHT=ROOT/'integration/checks/review_revision_preflight_20261002.json'
BUDGETS=(25,50,100,250,500,1000,2500,5000)
ANCHORS=(100,1000)
DIVISORS=(16,12,8,6,5,4,3,2)
STEPS=(1,2,4,8,16,32,64,128,256,512)
ADDED_BOUNDS=(.25,.375,.625,.75,.875,1.5,2.,3.,6.,8.,12.,24.,32.)


def descriptors():
    output=[]
    for r in json.loads((ROOT/'integration/REFERENCE_MANIFEST.json').read_text())['sources']:
        output.append(dict(site=r['site'],split='development',source=r['local_source'],
                           source_sha256=r['source_sha256'],geo=r['geo']))
    for r in json.loads((ROOT/'data/heldout_20261001/manifest.json').read_text())['rows']:
        output.append(dict(site=r['site'],split='original-heldout',source=r['source'],
                           source_sha256=r['source_sha256'],geo=r['geo']))
    for r in json.loads((ROOT/'data/expanded_20261002/manifest_v2.json').read_text())['rows']:
        source=next(s for s in r['sources'] if s['shape']==[1024,1024]);geo=dict(source['geo'])
        affine=list(geo['affine']);affine[2]+=256*affine[0]+256*affine[1];affine[5]+=256*affine[3]+256*affine[4]
        geo.update(affine=affine,shape=[512,512])
        output.append(dict(site=r['site'],split='expanded',source=source['source'],
                           source_sha256=source['source_sha256'],geo=geo))
    assert len(output)==48
    return output


def load(record):
    path=ROOT/record['source']
    if sha(path)!=record['source_sha256']:raise ValueError('Source changed')
    with np.load(path,allow_pickle=False) as z:raw=z['raw'];mask=z['mask']
    if record['split']=='expanded':raw=raw[256:768,256:768];mask=mask[256:768,256:768]
    x=raw.astype(np.int64);x[mask]=0
    assert x.shape==(512,512) and x.min()>=0 and x.max()<=10000
    return x,mask.copy()


def dense_grid():
    output=[]
    templates=[]
    for cfg in grid():
        if cfg.get('dtype')=='float64' and cfg['bound']==.49:templates.append(cfg)
    assert len(templates)==7
    for cfg in templates:
        for bound in ADDED_BOUNDS:output.append(dict(cfg,bound=bound))
    for algorithm in ('INTERP_LORENZO','INTERP','LORENZO_REG'):
        for bound in (1.,2.,4.,8.,16.):
            output.append(dict(backend='sz3',dtype='int64',algorithm=algorithm,bound=bound,transform='direct'))
    assert len(output)==106
    return output


def freeze():
    if PREFLIGHT.exists():raise ValueError('Preflight exists')
    names=['controls/review_geometry.py','controls/review_packet.py','controls/hierarchical_sum.py',
           'experiments/review_decoder.py','experiments/run_review_revision.py','tests/test_review_revision.py',
           'docs/REVIEW_REVISION_PROTOCOL_20261002.md','docs/GEOMETRY_RATE_DERIVATION_20261002.md',
           'controls/viable_greedy.py','controls/research_packet.py','experiments/research_common.py']
    files={str(ROOT/n):sha(ROOT/n) for n in names}
    for r in descriptors():files[str(ROOT/r['source'])]=r['source_sha256']
    previous=json.loads((ROOT/'integration/checks/expanded_encoding_preflight_20261002_v2.json').read_text())
    for p,h in previous['runtimes'].items():
        if sha(p)!=h:raise ValueError('Original runtime changed')
    for name in ('built_area_discrete_packet.py','built_area_packet.py','built_area_integer_metrics.py','native_sz3_worker.py'):
        files[str(LEGACY/'experiments'/name)]=sha(LEGACY/'experiments'/name)
    save(PREFLIGHT,dict(status='FROZEN_BEFORE_REVIEW_EXPERIMENTS',files=files,runtimes=previous['runtimes'],
                        original_sources=descriptors(),representation_attempts=1280,step_attempts=128,
                        hierarchy_attempts=2400,dense_attempts=424,dense_grid=dense_grid(),
                        anchors=list(ANCHORS),divisors=list(DIVISORS),hierarchy_steps=list(STEPS),gpu_used=False))


class Decoder:
    def __init__(self,folder):
        self.folder=folder;folder.mkdir();self.index=0
        self.log=(folder/'stderr.log').open('x')
        self.p=subprocess.Popen([sys.executable,str(ROOT/'experiments/review_decoder.py')],cwd=ROOT,
                                env=environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
    def decode(self,path):
        self.index+=1;target=self.folder/f'{self.index:04}.npz'
        self.p.stdin.write(json.dumps(dict(packet=str(path.resolve()),output=str(target.resolve())))+'\n');self.p.stdin.flush()
        if not select.select([self.p.stdout],[],[],240)[0]:raise TimeoutError('Decoder')
        line=self.p.stdout.readline()
        if not line:raise RuntimeError('Decoder exited')
        info=json.loads(line)
        if info['status']!='DECODED':raise ValueError(info)
        with np.load(target,allow_pickle=False) as z:y,m,p=(z[k] for k in ('y','mask','protected'))
        target.unlink();return y,m,p,info
    def close(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            try:self.p.wait(timeout=10)
            except subprocess.TimeoutExpired:self.p.terminate();self.p.wait(timeout=10)
        self.p.stdout.close();self.log.close()


def eligibility(x,y,mask,m,p,budgets,cache):
    h=hashlib.sha256(y.astype('<i8').tobytes()).hexdigest()
    if h in cache:return cache[h]
    if not np.array_equal(mask,m) or not np.array_equal(mask,p) or y[mask].any() or y.min()<0 or y.max()>10000:
        raise ValueError('Decoded range/mask/protection')
    difference=y-x;prefix=difference.cumsum(0).cumsum(1);e=int(np.abs(prefix).max())
    error=None
    if any(e<=b<4*e for b in budgets):error=int(_maximum_rectangle(difference))
    verdicts={str(b):bool(error<=b if error is not None else 4*e<=b) for b in budgets}
    info=dict(max_abs_prefix_error=e,rectangle_error_exact=error,rectangle_error_lower=e,
              rectangle_error_upper=4*e,legal_at=verdicts,
              certificate='exact-enumeration' if error is not None else 'four-corner-bound-and-prefix-witness',
              changed=int(np.count_nonzero(difference)),global_sum_error=int(difference.sum()),
              numerator_sha256=h,mask_ok=True,protected_ok=True,range_ok=True)
    cache[h]=info;return info


def deliver(folder,name,blob,fees,x,mask,decoder,cache,budgets,config,expected=None):
    path=folder/(name+'.packet');path.write_bytes(blob)
    if sum(fees.values())!=len(blob):raise ValueError('Fee total')
    y,m,p,decoded=decoder.decode(path)
    if expected is not None and not np.array_equal(y,expected):raise ValueError('Changed lossless representation')
    row=dict(id=name,status='DECODED_AND_AUDITED',configuration=config,packet=str(path.relative_to(ROOT)),
             packet_bytes=len(blob),packet_sha256=sha(path),fees=fees,decoder=decoded,
             audit=eligibility(x,y,mask,m,p,budgets,cache))
    save(folder/(name+'.json'),row)
    return row


def case(block,record):
    folder=OUT/block/record['site'];folder.mkdir(parents=True);decoder=Decoder(folder/'decoder')
    rows=[];cache={};x,mask=load(record);site=record['site'];geo=record['geo'];start=time.perf_counter()
    try:
        if block=='representation':
            for index,e in enumerate(BUDGETS):
                original=ROOT/f'.aris/evidence/expanded_20261002/frontier/{site}-512/{site}-512-{index:02}-RangeRectQuant.packet'
                y,m,p,decoded=decoder.decode(original);q=max(1,e//5)
                if not np.array_equal(mask,m) or not np.array_equal(p,mask):raise ValueError('Original masks')
                original_row=json.loads((ROOT/f'results/expanded_frontier_20261002/{site}-512/attempts/{site}-512-{index:02}-RangeRectQuant.json').read_text())
                if decoded['numerator_sha256']!=original_row['decoder']['numerator_sha256']:raise ValueError('Original field hash')
                for layout in ('direct','shuffled','split','quotient-only'):
                    cfg=dict(family='representation',epsilon=e,layout=layout,quantization_step=q)
                    blob,fees=review_packet.encode(y,mask,q,layout,dict(family='RangeRectQuant',epsilon=e),geo)
                    row=deliver(folder,f'e{e}-{layout}',blob,fees,x,mask,decoder,cache,BUDGETS,cfg,
                                expected=y if layout!='quotient-only' else None)
                    row['original_packet_bytes']=original_row['packet_bytes'];row['original_y_sha256']=decoded['numerator_sha256']
                    save(folder/(row['id']+'.json'),row);rows.append(row)
        elif block=='step':
            for e in ANCHORS:
                for divisor in DIVISORS:
                    q=max(1,e//divisor);y,detail=reconstruct(x,e//4,q,10000,mask)
                    cfg=dict(family='RangeRectQuant',epsilon=e,divisor=divisor,quantization_step=q)
                    blob,fees=research_packet.encode(y,mask,q,10000,cfg,geo)
                    row=deliver(folder,f'e{e}-d{divisor}',blob,fees,x,mask,decoder,cache,ANCHORS,cfg,expected=y)
                    row['geometry']=certificate(x,y,mask,e//4,q);row['split']=record['split']
                    save(folder/(row['id']+'.json'),row);rows.append(row)
        elif block=='hierarchy':
            for scaled in (False,True):
                for q in STEPS:
                    y=hierarchy(x,mask,q,scaled)
                    for layout in ('shuffled','split','hierarchical'):
                        cfg=dict(family='sum-pyramid',step=q,scaled=scaled,layout=layout)
                        blob,fees=review_packet.encode(y,mask,q,layout,cfg,geo)
                        row=deliver(folder,f's{int(scaled)}-q{q}-{layout}',blob,fees,x,mask,decoder,cache,ANCHORS,cfg,expected=y)
                        rows.append(row)
        else:
            for index,cfg in enumerate(dense_grid()):
                name=f'{index:03}-{cfg["backend"]}';commands=[];body=folder/(name+'.body')
                try:
                    blob,info=native_encode(x,mask,cfg,geo,body,commands)
                    if body.exists():body.unlink()
                    fees={k:v for k,v in info.items() if k.endswith('_bytes')}
                    row=deliver(folder,name,blob,fees,x,mask,decoder,cache,ANCHORS,cfg)
                    row['native_encode_commands']=commands
                except Exception as error:
                    row=dict(id=name,status='EXCEPTION',configuration=cfg,error=type(error).__name__+': '+str(error),
                             traceback=traceback.format_exc(),native_encode_commands=commands)
                save(folder/(name+'.json'),row);rows.append(row)
    finally:decoder.close()
    result=dict(site=site,split=record['split'],block=block,source_sha256=record['source_sha256'],rows=rows,
                elapsed_seconds=time.perf_counter()-start)
    save(folder/'case.json',result);return result


def summarize(cases):
    reports={}
    for block in ('representation','step','hierarchy','dense'):
        group=[c for c in cases if c['block']==block];rows=[r for c in group for r in c['rows']]
        reports[block]=dict(cases=len(group),attempts=len(rows),decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
                            exceptions=sum(r['status']=='EXCEPTION' for r in rows))
    reports['representation']['budgets']=[]
    reps=[c for c in cases if c['block']=='representation']
    for e in BUDGETS:
        totals={};legal_counts={}
        for layout in ('direct','shuffled','split','quotient-only'):
            selected=[r for c in reps for r in c['rows'] if r['configuration']['epsilon']==e and r['configuration']['layout']==layout]
            totals[layout]=sum(r['packet_bytes'] for r in selected)
            legal_counts[layout]=sum(r['audit']['legal_at'][str(e)] for r in selected)
        reports['representation']['budgets'].append(dict(epsilon=e,bytes=totals,bpp={k:v*8/(40*512**2) for k,v in totals.items()},legal=legal_counts,
            split_reduction_vs_shuffled=1-totals['split']/totals['shuffled']))
    reports['step']['groups']=[]
    for split in ('development','original-heldout'):
        for e in ANCHORS:
            for divisor in DIVISORS:
                selected=[r for c in cases if c['block']=='step' and c['split']==split for r in c['rows']
                          if r['configuration']['epsilon']==e and r['configuration']['divisor']==divisor]
                n=sum(r['geometry']['pixels'] for r in selected)
                reports['step']['groups'].append(dict(split=split,epsilon=e,divisor=divisor,q=max(1,e//divisor),cases=len(selected),
                    bytes=sum(r['packet_bytes'] for r in selected),bpp=sum(r['packet_bytes'] for r in selected)*8/n,
                    quotient_bpp=sum(r['fees']['quotient_or_body_bytes'] for r in selected)*8/n,
                    remainder_bpp=sum(r['fees']['remainder_bytes'] for r in selected)*8/n,
                    fine_fraction=sum(r['geometry']['fine'] for r in selected)/n,
                    width_bound_fraction=sum(r['geometry']['width_bound_fine'] for r in selected)/n,
                    all_legal=all(r['audit']['legal_at'][str(e)] for r in selected)))
    for block in ('hierarchy','dense'):
        reports[block]['comparisons']=[]
        for e in ANCHORS:
            pairs=[]
            for c in cases:
                if c['block']!=block:continue
                pool=[r for r in c['rows'] if r['status']=='DECODED_AND_AUDITED' and r['audit']['legal_at'][str(e)]]
                if block=='hierarchy':
                    report=json.loads((ROOT/'results/expanded_frontier_20261002/report.json').read_text())
                    item=next(f for f in report['frontier'] if f['size']==512 and f['epsilon']==e)
                    old=next(p for p in item['pairs'] if p['site']==c['site'])
                    index=BUDGETS.index(e)
                    main=json.loads((ROOT/f'results/expanded_frontier_20261002/{c["site"]}-512/attempts/{c["site"]}-512-{index:02}-RangeRectQuant.json').read_text())
                    main_bytes=main['packet_bytes'];old_bytes=old['baseline_bytes']
                else:
                    prior=json.loads((ROOT/f'results/heldout_20261001/report.json').read_text())
                    old=next(p for p in prior['comparisons'] if p['epsilon']==e and p['site']==c['site'])
                    main_bytes=old['main_bytes'];old_bytes=old['baseline_bytes']
                best=min(pool,key=lambda r:r['packet_bytes']) if pool else None
                new_bytes=min(old_bytes,best['packet_bytes'] if best else old_bytes)
                pairs.append(dict(site=c['site'],main_bytes=main_bytes,old_reference_bytes=old_bytes,new_reference_bytes=new_bytes,
                                  best_new_control_bytes=best['packet_bytes'] if best else None,
                                  best_configuration=best['configuration'] if best else None))
            reports[block]['comparisons'].append(dict(epsilon=e,pairs=pairs,strict_main_wins=sum(p['main_bytes']<p['new_reference_bytes'] for p in pairs),
                main_bytes=sum(p['main_bytes'] for p in pairs),reference_bytes=sum(p['new_reference_bytes'] for p in pairs),
                reduction_fraction=1-sum(p['main_bytes'] for p in pairs)/sum(p['new_reference_bytes'] for p in pairs)))
    return dict(status='COMPLETE_FIXED_REVIEW_EXPERIMENTS',blocks=reports,attempts=sum(r['attempts'] for r in reports.values()),
                sourcefree_decodes=sum(r['decodes'] for r in reports.values()),exceptions=sum(r['exceptions'] for r in reports.values()),gpu_used=False)


def run(workers):
    if OUT.exists():raise ValueError('Output exists')
    if subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain']):raise ValueError('Clean committed tree required')
    revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if subprocess.check_output(['git','-C',str(ROOT),'ls-remote','origin','refs/heads/main'],text=True).split()[0]!=revision:raise ValueError('Pushed tree required')
    f=json.loads(PREFLIGHT.read_text())
    for group in ('files','runtimes'):
        for p,h in f[group].items():
            if sha(p)!=h:raise ValueError('Frozen binding '+p)
    OUT.mkdir();save(OUT/'launch.json',dict(commit=revision,preflight_sha256=sha(PREFLIGHT),workers=workers,gpu_used=False))
    tasks=[]
    for r in descriptors():
        if r['split']=='expanded':tasks.extend((b,r) for b in ('representation','hierarchy'))
        else:
            tasks.append(('step',r))
            if r['split']=='original-heldout':tasks.append(('dense',r))
    cases=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(case,b,r):(b,r['site']) for b,r in tasks}
        for future in as_completed(futures):
            c=future.result();cases.append(c);print(json.dumps(dict(completed=len(cases),total=len(tasks),block=c['block'],site=c['site'])),flush=True)
    report=summarize(cases);assert report['attempts']==4232
    save(OUT/'report.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--run',action='store_true');parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.run:run(args.workers)
    else:parser.error('Choose freeze or run')
