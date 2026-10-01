"""Percentage-field comparison, with the same construction and native controls."""
import argparse
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
from controls.research_packet import encode as encode_main
from controls.water_packet import encode as encode_native,water_grid
from research_common import ROOT,ColdDecoder,audit,legal,sha,save,environment

MANIFEST=ROOT/'data/water_20261002/manifest_v2.json'
PREFLIGHT=ROOT/'integration/checks/water_encoding_preflight_20261002.json'
BUDGETS=(5,10,25,50,100,250,500,1000)


class WaterDecoder(ColdDecoder):
    def __init__(self,folder):
        self.folder=Path(folder); self.folder.mkdir(parents=True,exist_ok=True)
        self.log=(self.folder/'decoder-stderr.log').open('x')
        self.process=subprocess.Popen([sys.executable,str(ROOT/'experiments/water_decoder.py')],
            cwd=ROOT,env=environment(),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
        self.count=0


def freeze():
    if PREFLIGHT.exists(): raise ValueError('No preflight overwrite')
    manifest=json.loads(MANIFEST.read_text())
    if manifest['status']!='PASS_EIGHT_OCCURRENCE_WINDOWS': raise ValueError('Eight actual percentage windows')
    files={}
    paths=[Path(__file__),ROOT/'experiments/water_decoder.py',ROOT/'controls/water_packet.py',
        ROOT/'controls/research_packet.py',ROOT/'controls/viable_greedy.py',ROOT/'experiments/research_common.py',
        ROOT/'tests/test_water_packet.py',ROOT/'docs/WATER_PROTOCOL_20261002.md',MANIFEST,
        ROOT/'integration/water_assets_20261002.json']
    paths.extend(ROOT/r['source'] for r in manifest['rows'])
    for p in paths: files[str(p)]=sha(p)
    old=json.loads((ROOT/'integration/checks/expanded_encoding_preflight_20261002_v2.json').read_text())
    for p,digest in old['files'].items():
        if '/LinewiseROI/' in p:
            if sha(p)!=digest: raise ValueError('Native source binding')
            files[p]=digest
    save(PREFLIGHT,dict(status='FROZEN_BEFORE_PERCENTAGE_ENCODING',files=files,runtimes=old['runtimes'],
        native_configs=water_grid(),budgets=list(BUDGETS),locations=8,planned_packets=392,gpu_used=False))


def run(out):
    if out.exists(): raise ValueError('Fresh percentage result')
    frozen=json.loads(PREFLIGHT.read_text())
    for group in ('files','runtimes'):
        for p,digest in frozen[group].items():
            if sha(p)!=digest: raise ValueError('Water binding '+p)
    git=lambda *a:subprocess.check_output(['git','-C',str(ROOT),*a],text=True).strip()
    if git('status','--porcelain') or git('rev-parse','HEAD')!=git('ls-remote','origin','refs/heads/main').split()[0]:
        raise ValueError('Clean pushed percentage matrix')
    os.environ.update(environment()); out.mkdir(parents=True)
    storage=ROOT/'.aris/evidence/expanded_20261002/water'; storage.mkdir(parents=True)
    save(out/'launch.json',dict(commit=git('rev-parse','HEAD'),preflight_sha256=sha(PREFLIGHT),sourcefree_decoding=True))
    decoder=WaterDecoder(out/'decoder'); rows=[]
    try:
        for source in json.loads(MANIFEST.read_text())['rows']:
            with np.load(ROOT/source['source'],allow_pickle=False) as z:
                x=z['raw'].astype(np.int64); mask=z['mask']; x[mask]=0
            cache={}; configs=([dict(family='RangeRectQuant',epsilon=e) for e in BUDGETS]+
                              [dict(family='baseline',config=c) for c in water_grid()])
            for index,cfg in enumerate(configs):
                stem=f'{source["site"]}-{index:02d}-{cfg["family"]}'; commands=[]
                row=dict(id=stem,site=source['site'],configuration=cfg,status='EXCEPTION',source_sha256=source['source_sha256'])
                started=time.perf_counter()
                try:
                    if cfg['family']=='RangeRectQuant':
                        e=cfg['epsilon']; q=min(100,max(1,e//5))
                        y,mechanism=reconstruct(x,e//4,q,100,mask)
                        blob,fees=encode_main(y,mask,q,100,cfg,source['geo'])
                        row['mechanism']=mechanism
                    else: blob,fees=encode_native(x,mask,cfg['config'],source['geo'],commands)
                    encoded=time.perf_counter(); path=storage/(stem+'.packet'); path.write_bytes(blob)
                    y,m,p,decoded=decoder.decode(path)
                    identity=hashlib.sha256(y.astype('<i8').tobytes()+m.tobytes()+p.tobytes()).hexdigest()
                    if identity not in cache: cache[identity]=audit(x,y,mask,m,mask,p,cap=100)
                    checks=cache[identity]
                    if sum(fees.values())!=len(blob): raise ValueError('Paid percentage bytes')
                    row.update(status='DECODED_AND_AUDITED',packet=str(path.relative_to(ROOT)),packet_bytes=len(blob),fees=fees,
                        packet_sha256=sha(path),decoder=decoded,audit=checks,encode_seconds=encoded-started,
                        legal_at={str(e):legal(checks,e) for e in BUDGETS})
                except Exception as e:
                    row.update(error=str(e),traceback=traceback.format_exc())
                finally: row['native_encode_commands']=commands
                rows.append(row); save(out/'attempts'/(stem+'.json'),row)
                save(out/'ledger.json',dict(status='RUNNING',rows=rows))
            print(source['site'],'completed',flush=True)
    finally: decoder.close()
    comparisons=[]
    for e in BUDGETS:
        pairs=[]
        for source in json.loads(MANIFEST.read_text())['rows']:
            valid=[r for r in rows if r['site']==source['site'] and r['status']=='DECODED_AND_AUDITED' and r['legal_at'][str(e)]]
            mains=[r for r in valid if r['configuration']==dict(family='RangeRectQuant',epsilon=e)]
            baselines=[r for r in valid if r['configuration']['family']=='baseline']
            main=mains[0] if mains else None; base=min(baselines,key=lambda r:r['packet_bytes']) if baselines else None
            pairs.append(dict(site=source['site'],main_bytes=main['packet_bytes'] if main else None,
                baseline_bytes=base['packet_bytes'] if base else None,main_changed=main['audit']['changed'] if main else None,
                baseline_configuration=base['configuration'] if base else None,
                reduction=1-main['packet_bytes']/base['packet_bytes'] if main and base else None))
        complete=all(p['main_bytes'] and p['baseline_bytes'] for p in pairs)
        comparisons.append(dict(epsilon=e,pairs=pairs,main_bytes=sum(p['main_bytes'] or 0 for p in pairs),
            baseline_bytes=sum(p['baseline_bytes'] or 0 for p in pairs),
            reduction_fraction=1-sum(p['main_bytes'] for p in pairs)/sum(p['baseline_bytes'] for p in pairs) if complete else None,
            strict_wins=sum(p['reduction'] is not None and p['reduction']>0 for p in pairs)))
    report=dict(status='COMPLETE_FIXED_PERCENTAGE_MATRIX' if len(rows)==392 else 'PARTIAL',attempted_packets=len(rows),
        sourcefree_decodes=sum(r['status']=='DECODED_AND_AUDITED' for r in rows),
        exceptions=sum(r['status']=='EXCEPTION' for r in rows),comparisons=comparisons,gpu_used=False)
    save(out/'ledger.json',dict(status=report['status'],rows=rows)); save(out/'report.json',report)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','run']); p.add_argument('--out',type=Path)
    a=p.parse_args(); freeze() if a.action=='freeze' else run(a.out.resolve())
