"""Replay exact failed configurations; retain stderr without replacing failures."""
import json
from pathlib import Path
import traceback

import numpy as np
from research_common import ROOT,save,sha,environment
from built_area_discrete_packet import body_codec
from run_expanded_research import center


def run():
    import os
    os.environ.update(environment())
    out=ROOT/'results/native_failure_replays_20261002'
    if out.exists(): raise ValueError('Fresh failure evidence required')
    out.mkdir(); rows=[]
    for ledger in sorted((ROOT/'results/expanded_frontier_20261002').glob('*/ledger.json')):
        case=json.loads(ledger.read_text())
        failures=[r for r in case['rows'] if r['status']=='EXCEPTION' and r['configuration']['family']=='baseline']
        if not failures: continue
        with np.load(ROOT/case['source'],allow_pickle=False) as z:
            x=center(z['raw'],case['size']).astype(np.float64); mask=center(z['mask'],case['size']); x[mask]=0
        for r in failures:
            folder=out/r['id']; folder.mkdir(); commands=[]; cfg=r['configuration']['config']
            result=dict(id=r['id'],configuration=cfg,source_sha256=case['source_sha256'],
                        original_failure_preserved=True,previous_error=r['error'])
            try:
                body=body_codec(cfg,'encode',x,x.shape,commands,folder)
                (folder/'native.body').write_bytes(body)
                result.update(status='REPLAY_SUCCEEDED',body_sha256=sha(folder/'native.body'))
            except Exception as e:
                result.update(status='REPRODUCED_EXCEPTION',error=str(e),traceback=traceback.format_exc())
            finally:
                result['commands']=commands; save(folder/'replay.json',result)
            rows.append(result); print(r['id'],result['status'],flush=True)
    save(out/'report.json',dict(status='COMPLETED_FAILURE_REPLAYS',rows=rows,
        failures_replayed=len(rows),reproduced=sum(r['status']=='REPRODUCED_EXCEPTION' for r in rows)))


if __name__=='__main__': run()
