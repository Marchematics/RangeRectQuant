"""Re-run the unchanged density plan after extending its carrier allowlist."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from controls.dense_native import encode,added_grid
from run_review_revision import descriptors,load,deliver,Decoder,ANCHORS
from research_common import ROOT,LEGACY,environment,save,sha

OUT=ROOT/'results/review_dense_20261002'
PREFLIGHT=ROOT/'integration/checks/review_dense_preflight_20261002.json'


class DenseDecoder(Decoder):
    def __init__(self,folder):
        self.folder=folder;folder.mkdir();self.index=0;self.log=(folder/'stderr.log').open('x')
        self.p=subprocess.Popen([sys.executable,str(ROOT/'experiments/review_dense_decoder.py')],cwd=ROOT,
                                env=environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)


def freeze():
    if PREFLIGHT.exists():raise ValueError('Preflight exists')
    names=['controls/dense_native.py','experiments/review_dense_decoder.py','experiments/run_review_dense.py',
           'experiments/run_review_revision.py','experiments/review_decoder.py']
    files={str(ROOT/n):sha(ROOT/n) for n in names}
    original=json.loads((ROOT/'integration/checks/review_revision_preflight_20261002.json').read_text())
    files.update(original['files'])
    for p,h in {**files,**original['runtimes']}.items():
        if sha(p)!=h:raise ValueError('Frozen binding '+p)
    save(PREFLIGHT,dict(status='FROZEN_BEFORE_NATIVE_ALLOWLIST_REPAIR_RUN',files=files,runtimes=original['runtimes'],
                        added_grid=added_grid(),attempts=424,gpu_used=False,
                        previous_block='results/review_revision_20261002/dense',
                        repair='Extend setting allowlist in isolated module; preserve original codec/carrier/postprocessor and all previous failed adapter attempts'))


def case(record):
    folder=OUT/record['site'];folder.mkdir();decoder=DenseDecoder(folder/'decoder');cache={};rows=[]
    x,mask=load(record);start=time.perf_counter()
    try:
        for index,cfg in enumerate(added_grid()):
            name=f'{index:03}-{cfg["backend"]}';commands=[];body=folder/(name+'.body')
            try:
                blob,info=encode(x,mask,cfg,record['geo'],body,commands)
                if body.exists():body.unlink()
                row=deliver(folder,name,blob,{k:v for k,v in info.items() if k.endswith('_bytes')},
                            x,mask,decoder,cache,ANCHORS,cfg)
                row['native_encode_commands']=commands
            except Exception as error:
                row=dict(id=name,status='EXCEPTION',configuration=cfg,error=type(error).__name__+': '+str(error),
                         traceback=traceback.format_exc(),native_encode_commands=commands)
            save(folder/(name+'.json'),row);rows.append(row)
    finally:decoder.close()
    result=dict(site=record['site'],split=record['split'],source_sha256=record['source_sha256'],rows=rows,
                elapsed_seconds=time.perf_counter()-start)
    save(folder/'case.json',result);return result


def run():
    if OUT.exists():raise ValueError('Output exists')
    f=json.loads(PREFLIGHT.read_text())
    for group in ('files','runtimes'):
        for p,h in f[group].items():
            if sha(p)!=h:raise ValueError('Frozen binding '+p)
    revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    if subprocess.check_output(['git','-C',str(ROOT),'ls-remote','origin','refs/heads/main'],text=True).split()[0]!=revision:
        raise ValueError('Pushed tree required')
    OUT.mkdir();save(OUT/'launch.json',dict(commit=revision,preflight_sha256=sha(PREFLIGHT),workers=2,gpu_used=False))
    records=[r for r in descriptors() if r['split']=='original-heldout'];cases=[]
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(case,r) for r in records]
        for future in as_completed(futures):
            c=future.result();cases.append(c);print(json.dumps(dict(completed=len(cases),site=c['site'])),flush=True)
    comparisons=[];prior=json.loads((ROOT/'results/heldout_20261001/report.json').read_text())
    for e in ANCHORS:
        pairs=[]
        for c in cases:
            old=next(p for p in prior['comparisons'] if p['epsilon']==e and p['site']==c['site'])
            eligible=[r for r in c['rows'] if r['status']=='DECODED_AND_AUDITED' and r['audit']['legal_at'][str(e)]]
            best=min(eligible,key=lambda r:r['packet_bytes']) if eligible else None
            new=min(old['baseline_bytes'],best['packet_bytes'] if best else old['baseline_bytes'])
            pairs.append(dict(site=c['site'],main_bytes=old['main_bytes'],old_reference_bytes=old['baseline_bytes'],
                              new_reference_bytes=new,best_added_bytes=best['packet_bytes'] if best else None,
                              best_added_configuration=best['configuration'] if best else None))
        comparisons.append(dict(epsilon=e,pairs=pairs,strict_main_wins=sum(p['main_bytes']<p['new_reference_bytes'] for p in pairs),
                                main_bytes=sum(p['main_bytes'] for p in pairs),reference_bytes=sum(p['new_reference_bytes'] for p in pairs),
                                reduction_fraction=1-sum(p['main_bytes'] for p in pairs)/sum(p['new_reference_bytes'] for p in pairs)))
    rows=[r for c in cases for r in c['rows']]
    report=dict(status='COMPLETE_REPAIRED_DENSITY_PLAN',attempts=len(rows),sourcefree_decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
                exceptions=sum(r['status']=='EXCEPTION' for r in rows),comparisons=comparisons,gpu_used=False)
    assert len(rows)==424;save(OUT/'report.json',report);print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if args.freeze:freeze()
    elif args.run:run()
    else:parser.error('Choose freeze or run')
