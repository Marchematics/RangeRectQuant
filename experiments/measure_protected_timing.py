"""Uniformly warmed timings for exactly the already delivered protected fields."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from controls.viable_greedy import reconstruct
from research_common import ROOT,save,sha


def run():
    target=ROOT/'results/protected_timing_20261002/report.json'
    if target.exists(): raise ValueError('Refuse overwrite warmed timing evidence')
    ledger=ROOT/'results/protected_sweep_20261002/ledger.json'
    frozen=json.loads(ledger.read_text())['rows']
    sources={r['site']:r for r in json.loads((ROOT/'data/heldout_20261001/manifest.json').read_text())['rows']}
    tiny=np.zeros((2,2),np.int64); reconstruct(tiny,25,20,10000,np.zeros(tiny.shape,bool))
    rows=[]
    for site,source in sources.items():
        with np.load(ROOT/source['source'],allow_pickle=False) as z:
            x=z['raw'].astype(np.int64); mask=z['mask']; x[mask]=0
        indices=np.random.default_rng(20261002).permutation(np.flatnonzero(~mask))
        for r in [v for v in frozen if v['site']==site]:
            cfg=r['configuration']; p=mask.copy()
            p.ravel()[indices[:round(len(indices)*cfg['protected_fraction'])]]=True
            elapsed=[]
            for _ in range(3):
                started=time.perf_counter(); y,_=reconstruct(x,cfg['epsilon']//4,cfg['epsilon']//5,10000,p)
                elapsed.append(time.perf_counter()-started)
                if hashlib.sha256(y.astype('<i8').tobytes()).hexdigest()!=r['decoder']['numerator_sha256']:
                    raise ValueError('Warmed construction differs from saved packet')
            rows.append(dict(id=r['id'],site=site,configuration=cfg,seconds=elapsed,
                             median_seconds=float(np.median(elapsed)),same_decoded_field=True))
    save(target,dict(status='COMPLETE_UNIFORMLY_WARMED_TIMINGS',rows=rows,repetitions=3,
        input_ledger_sha256=sha(ledger),scope='same core plus full prefix audit; compilation excluded',
        simultaneous_frontier_jobs=False,gpu_used=False))


if __name__=='__main__': run()
